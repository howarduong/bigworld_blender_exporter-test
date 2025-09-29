# 文件位置: bigworld_blender_exporter/formats/animation_format.py
# Animation file format for BigWorld export

import struct
import os
from datetime import datetime
from ..utils.binary_writer import (
    create_directory, write_uint32, write_float32, write_float3, write_float4
)
from ..utils.logger import get_logger

logger = get_logger("animation_format")


def export_animation_file(filepath, animation_data):
    """
    Export animation data to BigWorld .animation file
    """
    try:
        logger.info(f"Exporting animation file: {filepath}")
        create_directory(filepath)

        with open(filepath, 'wb') as f:
            # Header
            write_animation_header(f, animation_data)
            # Bone data
            write_bone_data(f, animation_data['bones'])
            # Keyframe data
            write_keyframe_data(f, animation_data['keyframes'])

        logger.info(f"Animation file written: {filepath}")
    except Exception as e:
        logger.error(f"Failed to export animation file {filepath}: {str(e)}")
        raise


def write_animation_header(f, animation_data):
    """Write animation file header"""
    # Magic number for BigWorld animation files
    f.write(struct.pack('<I', 0x42570101))  # BW magic
    # Version
    f.write(struct.pack('<I', 0x01000000))  # 1.0.0.0
    # Bone count
    write_uint32(f, len(animation_data['bones']))
    # Keyframe count
    write_uint32(f, len(animation_data['keyframes']))
    # Frame rate
    write_float32(f, animation_data['frame_rate'])
    # Duration
    write_float32(f, animation_data['duration'])
    # Animation name (UTF-8, null-terminated, 64 bytes max)
    name = animation_data['name'][:63].encode('utf-8', errors='ignore')
    f.write(name)
    f.write(b'\0' * (64 - len(name)))
    # Loop flag
    f.write(struct.pack('<B', 1 if animation_data.get('loop', False) else 0))
    # Padding
    f.write(b'\0' * 3)
    # Export timestamp
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode('ascii')
    ts = ts[:31]  # max 32 bytes
    f.write(ts)
    f.write(b'\0' * (32 - len(ts)))


def write_bone_data(f, bones_data):
    """Write bone hierarchy data"""
    for bone in bones_data:
        # Bone name (null-terminated string, 32 chars max)
        name = bone['name'][:31].encode('utf-8', errors='ignore')
        f.write(name)
        f.write(b'\0' * (32 - len(name)))
        # Parent bone index (-1 if no parent)
        parent_index = -1
        if bone['parent']:
            for i, b in enumerate(bones_data):
                if b['name'] == bone['parent']:
                    parent_index = i
                    break
        f.write(struct.pack('<i', parent_index))
        # Bone length
        write_float32(f, bone.get('length', 1.0))
        # Head position
        write_float3(f, *bone['head'])
        # Tail position
        write_float3(f, *bone['tail'])


def write_keyframe_data(f, keyframes, threshold=0.0001):
    """Write keyframe animation data with optional compression"""
    last_transforms = {}
    for keyframe in keyframes:
        # Frame number
        write_uint32(f, keyframe['frame'])
        # Time
        write_float32(f, keyframe['time'])
        # Bone transforms
        for bone_name, transform in keyframe['bone_transforms'].items():
            prev = last_transforms.get(bone_name)
            if prev and _is_similar(prev, transform, threshold):
                # 写入 identity 代替，节省空间
                write_float3(f, 0.0, 0.0, 0.0)
                write_float4(f, 1.0, 0.0, 0.0, 0.0)
                write_float3(f, 1.0, 1.0, 1.0)
            else:
                write_float3(f, *transform['position'])
                write_float4(f, transform['rotation'][3], transform['rotation'][0],
                             transform['rotation'][1], transform['rotation'][2])
                write_float3(f, *transform['scale'])
                last_transforms[bone_name] = transform


def _is_similar(t1, t2, threshold):
    """Check if two transforms are similar enough to skip"""
    def diff(a, b): return abs(a - b) < threshold
    return (
        all(diff(a, b) for a, b in zip(t1['position'], t2['position'])) and
        all(diff(a, b) for a, b in zip(t1['rotation'], t2['rotation'])) and
        all(diff(a, b) for a, b in zip(t1['scale'], t2['scale']))
    )


def export_animation_data_legacy(filepath, frames, bones):
    """Legacy animation export function for backward compatibility"""
    logger.warning("Using legacy animation export format")
    create_directory(filepath)
    with open(filepath, 'wb') as f:
        # Write frame and bone count
        f.write(struct.pack('<II', len(frames), len(bones)))
        for frame in frames:
            for bone in bones:
                if bone in frame:
                    t = frame[bone]['position']
                    r = frame[bone]['rotation']
                    s = frame[bone]['scale']
                    f.write(struct.pack('<3f4f3f', t[0], t[1], t[2],
                                        r[3], r[0], r[1], r[2],
                                        s[0], s[1], s[2]))
                else:
                    # Identity transform
                    f.write(struct.pack('<3f4f3f', 0, 0, 0, 1, 0, 0, 0, 1, 1, 1))
