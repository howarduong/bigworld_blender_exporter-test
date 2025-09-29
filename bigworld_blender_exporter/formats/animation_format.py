# 文件位置: bigworld_blender_exporter/formats/animation_format.py
# Animation file format for BigWorld export

import struct
import os
from ..utils.binary_writer import create_directory, write_uint32, write_float32, write_float3, write_float4
from ..utils.logger import get_logger

logger = get_logger("animation_format")

def export_animation_file(filepath, animation_data):
    """Export animation data to BigWorld .animation file"""
    logger.info(f"Exporting animation file: {filepath}")
    
    # Create directory if it doesn't exist
    create_directory(filepath)
    
    with open(filepath, 'wb') as f:
        # Write header
        write_animation_header(f, animation_data)
        
        # Write bone data
        write_bone_data(f, animation_data['bones'])
        
        # Write keyframe data
        write_keyframe_data(f, animation_data['keyframes'])

def write_animation_header(f, animation_data):
    """Write animation file header"""
    # Magic number for BigWorld animation files
    f.write(struct.pack('<I', 0x42570101))  # BigWorld animation magic
    
    # Version
    f.write(struct.pack('<I', 0x01000000))  # Version 1.0.0.0
    
    # Animation info
    write_uint32(f, len(animation_data['bones']))  # Bone count
    write_uint32(f, len(animation_data['keyframes']))  # Keyframe count
    write_float32(f, animation_data['frame_rate'])  # Frame rate
    write_float32(f, animation_data['duration'])  # Duration
    
    # Animation name (null-terminated string, 64 chars max)
    name = animation_data['name'][:63].encode('ascii')
    f.write(name)
    f.write(b'\0' * (64 - len(name)))
    
    # Loop flag
    f.write(struct.pack('<B', 1 if animation_data.get('loop', False) else 0))
    
    # Padding
    f.write(b'\0' * 3)

def write_bone_data(f, bones_data):
    """Write bone hierarchy data"""
    for bone in bones_data:
        # Bone name (null-terminated string, 32 chars max)
        name = bone['name'][:31].encode('ascii')
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
        write_float32(f, bone['length'])
        
        # Head position
        write_float3(f, bone['head'][0], bone['head'][1], bone['head'][2])
        
        # Tail position
        write_float3(f, bone['tail'][0], bone['tail'][1], bone['tail'][2])

def write_keyframe_data(f, keyframes):
    """Write keyframe animation data"""
    for keyframe in keyframes:
        # Frame number
        write_uint32(f, keyframe['frame'])
        
        # Time
        write_float32(f, keyframe['time'])
        
        # Bone transforms
        for bone_name, transform in keyframe['bone_transforms'].items():
            # Position
            write_float3(f, transform['position'][0], transform['position'][1], transform['position'][2])
            
            # Rotation (quaternion: w, x, y, z)
            write_float4(f, transform['rotation'][3], transform['rotation'][0], 
                        transform['rotation'][1], transform['rotation'][2])
            
            # Scale
            write_float3(f, transform['scale'][0], transform['scale'][1], transform['scale'][2])

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
                    
                    # Position (3 floats)
                    f.write(struct.pack('<3f', t[0], t[1], t[2]))
                    
                    # Rotation (4 floats: w, x, y, z)
                    f.write(struct.pack('<4f', r[3], r[0], r[1], r[2]))
                    
                    # Scale (3 floats)
                    f.write(struct.pack('<3f', s[0], s[1], s[2]))
                else:
                    # Write identity transform if bone not found
                    f.write(struct.pack('<3f4f3f', 0, 0, 0, 1, 0, 0, 0, 1, 1, 1))
