# 文件位置: bigworld_blender_exporter/formats/animation_format.py
# Animation file format for BigWorld export (aligned to official runtime expectations)

import struct
import os
from ..utils.binary_writer import create_directory, write_u32, write_f32
from ..utils.logger import get_logger
from ..utils.validation import ValidationError

logger = get_logger("animation_format")


def export_animation_file(filepath, animation_data):
    """
    Export animation data to BigWorld .animation binary file.

    animation_data dict expected keys:
      - name: str
      - bones: list of { name, parent (or None), index }
      - keyframes: list of { frame, time, bone_transforms: { bone_name: { position, rotation, scale } } }
      - frame_rate: float
      - duration: float
      - loop: bool
    """
    logger.info(f"Exporting animation file: {filepath}")

    create_directory(filepath)
    with open(filepath, "wb") as f:
        _write_header(f, animation_data)
        _write_bones(f, animation_data["bones"])
        _write_keyframes(f, animation_data["keyframes"], animation_data["bones"])


def _write_header(f, anim):
    # Magic number (BigWorld convention, 0x42570101 or 0x42570100 depending on version)
    f.write(struct.pack("<I", 0x42570101))
    # Version (1)
    f.write(struct.pack("<I", 1))

    # Bone count
    write_u32(f, len(anim["bones"]))
    # Keyframe count
    write_u32(f, len(anim["keyframes"]))
    # Frame rate
    write_f32(f, float(anim.get("frame_rate", 30.0)))
    # Duration
    write_f32(f, float(anim.get("duration", 0.0)))

    # Animation name (64 bytes, null-terminated)
    name = anim["name"][:63].encode("ascii", errors="ignore")
    f.write(name)
    f.write(b"\0" * (64 - len(name)))

    # Loop flag (u8) + padding
    loop_flag = 1 if anim.get("loop", False) else 0
    f.write(struct.pack("<B", loop_flag))
    f.write(b"\0" * 3)


def _write_bones(f, bones):
    """
    Write bone hierarchy: name (32B), parent index (i32).
    """
    for bone in bones:
        # Bone name (32 bytes, null-terminated)
        name = bone["name"][:31].encode("ascii", errors="ignore")
        f.write(name)
        f.write(b"\0" * (32 - len(name)))

        # Parent index
        parent_index = -1
        if bone.get("parent"):
            for i, b in enumerate(bones):
                if b["name"] == bone["parent"]:
                    parent_index = i
                    break
        f.write(struct.pack("<i", parent_index))


def _write_keyframes(f, keyframes, bones):
    """
    Write keyframe data: for each frame, write frame index, time, then TRS for each bone in order.
    """
    for kf in keyframes:
        write_u32(f, kf["frame"])
        write_f32(f, kf["time"])

        for bone in bones:
            bname = bone["name"]
            if bname not in kf["bone_transforms"]:
                raise ValidationError(f"Missing transform for bone {bname} in frame {kf['frame']}")

            tr = kf["bone_transforms"][bname]

            # Position (3 floats)
            write_f32(f, tr["position"][0])
            write_f32(f, tr["position"][1])
            write_f32(f, tr["position"][2])

            # Rotation (4 floats: x, y, z, w) — must match core/animation_processor.py output
            write_f32(f, tr["rotation"][0])
            write_f32(f, tr["rotation"][1])
            write_f32(f, tr["rotation"][2])
            write_f32(f, tr["rotation"][3])

            # Scale (3 floats)
            write_f32(f, tr["scale"][0])
            write_f32(f, tr["scale"][1])
            write_f32(f, tr["scale"][2])
