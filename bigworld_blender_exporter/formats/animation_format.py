# 文件位置: bigworld_blender_exporter/formats/animation_format.py
# Animation file format for BigWorld export

# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET
from ..utils.logger import get_logger

logger = get_logger("animation_format")


def _vec3_to_text(v):
    # v: (x, y, z)
    return f"{float(v[0]):.6f} {float(v[1]):.6f} {float(v[2]):.6f}"


def _quat_to_text(q):
    # q: (x, y, z, w) — 输出顺序为 w x y z，符合常见引擎约定
    return f"{float(q[3]):.6f} {float(q[0]):.6f} {float(q[1]):.6f} {float(q[2]):.6f}"


def create_animation_xml(animation_data):
    """
    创建符合 BigWorld 规范的 .animation XML 树。

    参数结构示例（请在导出器中组装该字典）：
    animation_data = {
        "name": "walk",
        "frame_rate": 30.0,
        "duration": 2.0,
        "loop": True,
        "channels": [
            {
                "bone": "Hip",
                "keyframes": [
                    {
                        "time": 0.0,
                        "position": (0.0, 0.0, 0.0),
                        "rotation": (0.0, 0.0, 0.0, 1.0),  # (x, y, z, w)
                        "scale": (1.0, 1.0, 1.0)
                    },
                    # ...
                ]
            },
            # 更多骨骼……
        ]
    }
    """
    root = ET.Element("animation")

    # 基本信息
    name_elem = ET.SubElement(root, "name")
    name_elem.text = animation_data.get("name", "unnamed")

    fr_elem = ET.SubElement(root, "frameRate")
    fr_elem.text = f"{float(animation_data.get('frame_rate', 30.0)):.6f}"

    dur_elem = ET.SubElement(root, "duration")
    dur_elem.text = f"{float(animation_data.get('duration', 0.0)):.6f}"

    loop_elem = ET.SubElement(root, "loop")
    loop_elem.text = "true" if bool(animation_data.get("loop", False)) else "false"

    # 通道（每个骨骼一个 channel）
    channels_elem = ET.SubElement(root, "channels")

    for ch in animation_data.get("channels", []):
        channel_elem = ET.SubElement(channels_elem, "channel")

        bone_elem = ET.SubElement(channel_elem, "bone")
        bone_elem.text = ch.get("bone", "")

        kfs_elem = ET.SubElement(channel_elem, "keyframes")

        for kf in ch.get("keyframes", []):
            kf_elem = ET.SubElement(kfs_elem, "keyframe")

            t_elem = ET.SubElement(kf_elem, "time")
            t_elem.text = f"{float(kf.get('time', 0.0)):.6f}"

            p_elem = ET.SubElement(kf_elem, "position")
            p_elem.text = _vec3_to_text(kf.get("position", (0.0, 0.0, 0.0)))

            r_elem = ET.SubElement(kf_elem, "rotation")
            r_elem.text = _quat_to_text(kf.get("rotation", (0.0, 0.0, 0.0, 1.0)))

            s_elem = ET.SubElement(kf_elem, "scale")
            s_elem.text = _vec3_to_text(kf.get("scale", (1.0, 1.0, 1.0)))

    return ET.ElementTree(root)


def export_animation_file(filepath, animation_data):
    """
    导出 .animation 文件（XML）
    - 路径由上层传入（建议位于 res/animations/...）
    - animation_data 结构参考 create_animation_xml 的说明
    """
    try:
        logger.info(f"Exporting animation file: {filepath}")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        tree = create_animation_xml(animation_data)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)

        logger.info(f"Animation file written: {filepath}")
    except Exception as e:
        logger.error(f"Failed to export animation file {filepath}: {str(e)}")
        raise
