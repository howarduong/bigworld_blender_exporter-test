# 文件位置: bigworld_blender_exporter/formats/animation_format.py
# Animation file format for BigWorld export (aligned to official runtime expectations)

import struct
from ..utils.binary_writer import create_directory, write_u32, write_f32
from ..utils.logger import get_logger
from ..utils.validation import ValidationError

logger = get_logger("animation_format")


def export_animation_file(filepath, animation_data):
    """
    Export animation data to BigWorld .animation binary file.

    animation_data dict expected keys:
      - name: str
      - bones: list of { name: str, parent: str|None }
      - keyframes: list of { frame: int, time: float,
                     bone_transforms: { bone_name: { position: [x,y,z], rotation: [x,y,z,w], scale: [x,y,z] } } }
      - frame_rate: float
      - duration: float
      - loop: bool
      - cognate: bool
      - alpha: bool
      - markers: optional list of { time: float, name: str }  # 可选事件标记
    """
    logger.info(f"Exporting animation file: {filepath}")

    # Basic validation
    if "bones" not in animation_data or not animation_data["bones"]:
        raise ValidationError("Animation export failed: no bones in animation_data")
    if "keyframes" not in animation_data or not animation_data["keyframes"]:
        raise ValidationError("Animation export failed: no keyframes in animation_data")
    if "name" not in animation_data or not animation_data["name"]:
        raise ValidationError("Animation export failed: missing animation name")

    create_directory(filepath)
    with open(filepath, "wb") as f:
        _write_header(f, animation_data)
        _write_bones(f, animation_data["bones"])
        _write_keyframes(f, animation_data["keyframes"], animation_data["bones"])
        _write_markers(f, animation_data.get("markers", []))


def _write_header(f, anim):
    """
    Binary header layout (little-endian):
      - magic: u32 (0x42570101)
      - version: u32 (1)
      - boneCount: u32
      - frameCount: u32
      - frameRate: f32
      - duration: f32
      - name: char[64] (null-terminated/truncated ASCII)
      - flags: 4 bytes
          [0] loop: u8 (0/1)
          [1] cognate: u8 (0/1)
          [2] alpha: u8 (0/1)
          [3] reserved/padding: u8 (0)
    """
    # Magic number and version (keep aligned with current exporter expectations)
    f.write(struct.pack("<I", 0x42570101))
    f.write(struct.pack("<I", 1))

    # Counts and timings
    write_u32(f, len(anim["bones"]))
    write_u32(f, len(anim["keyframes"]))
    write_f32(f, float(anim.get("frame_rate", 30.0)))
    write_f32(f, float(anim.get("duration", 0.0)))

    # Name (64 bytes, null-terminated)
    name_bytes = anim["name"][:63].encode("ascii", errors="ignore")
    f.write(name_bytes)
    f.write(b"\0" * (64 - len(name_bytes)))

    # Flags: loop, cognate, alpha, padding
    loop_flag = 1 if anim.get("loop", False) else 0
    cognate_flag = 1 if anim.get("cognate", False) else 0
    alpha_flag = 1 if anim.get("alpha", False) else 0
    f.write(struct.pack("<BBBB", loop_flag, cognate_flag, alpha_flag, 0))


def _write_bones(f, bones):
    """
    Write bone table:
      - name: char[32] (null-terminated/truncated ASCII)
      - parentIndex: i32 (-1 if no parent)
    """
    # Precompute a name->index map for parent lookups
    name_to_index = {b["name"]: i for i, b in enumerate(bones)}

    for bone in bones:
        # Name
        bname = bone["name"][:31].encode("ascii", errors="ignore")
        f.write(bname)
        f.write(b"\0" * (32 - len(bname)))
        # Parent index
        parent_index = -1
        parent_name = bone.get("parent")
        if parent_name:
            parent_index = name_to_index.get(parent_name, -1)
        f.write(struct.pack("<i", parent_index))


def _write_keyframes(f, keyframes, bones):
    """
    For each keyframe:
      - frame: u32
      - time: f32
      - For each bone in bones order:
          position: f32 * 3
          rotation: f32 * 4 (x, y, z, w)
          scale:    f32 * 3
    """
    for kf in keyframes:
        # Per-frame header
        write_u32(f, int(kf["frame"]))
        write_f32(f, float(kf["time"]))

        # Per-bone TRS in skeleton order
        bt = kf.get("bone_transforms", {})
        for bone in bones:
            bname = bone["name"]
            if bname not in bt:
                raise ValidationError(f"Missing transform for bone '{bname}' in frame {kf.get('frame')}")

            tr = bt[bname]
            pos = tr.get("position")
            rot = tr.get("rotation")
            scl = tr.get("scale")

            if pos is None or len(pos) != 3:
                raise ValidationError(f"Invalid position for bone '{bname}' at frame {kf.get('frame')}")
            if rot is None or len(rot) != 4:
                raise ValidationError(f"Invalid rotation for bone '{bname}' at frame {kf.get('frame')}")
            if scl is None or len(scl) != 3:
                raise ValidationError(f"Invalid scale for bone '{bname}' at frame {kf.get('frame')}")

            # Position
            write_f32(f, float(pos[0])); write_f32(f, float(pos[1])); write_f32(f, float(pos[2]))
            # Rotation (x, y, z, w)
            write_f32(f, float(rot[0])); write_f32(f, float(rot[1])); write_f32(f, float(rot[2])); write_f32(f, float(rot[3]))
            # Scale
            write_f32(f, float(scl[0])); write_f32(f, float(scl[1])); write_f32(f, float(scl[2]))


def _write_markers(f, markers):
    """
    Optional marker table:
      - markerCount: u32
      - For each marker: time f32, name[32] ASCII
    """
    write_u32(f, len(markers))
    for m in markers:
        write_f32(f, float(m.get("time", 0.0)))
        name_bytes = str(m.get("name", ""))[:31].encode("ascii", errors="ignore")
        f.write(name_bytes)
        f.write(b"\0" * (32 - len(name_bytes)))
