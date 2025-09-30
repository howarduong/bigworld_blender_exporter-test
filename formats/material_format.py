# 文件位置: bigworld_blender_exporter/formats/material_format.py
# -*- coding: utf-8 -*-
"""
Material (.mfm) writer aligned with official grammar, including extended flags.

Supported keys:
  - identifier: str
  - fx: str
  - materialKind: str
  - properties: dict[str, any]  # Float/Int/Bool/Vector4/Texture
  - collisionFlags: optional int
  - alphaTestEnable: optional bool
  - doubleSided: optional bool
"""

import xml.etree.ElementTree as ET
from ..utils.logger import get_logger
from ..utils.xml_writer import write_xml_file

logger = get_logger("material_format")


def export_material_file(filepath, mat_data):
    """
    Export material data to .mfm XML file.

    mat_data keys:
      - identifier, fx, materialKind, properties
      - collisionFlags?: int
      - alphaTestEnable?: bool
      - doubleSided?: bool
    """
    logger.info(f"Exporting material file: {filepath}")
    root = ET.Element("mfm")

    ET.SubElement(root, "identifier").text = mat_data.get("identifier", "")
    ET.SubElement(root, "fx").text = mat_data.get("fx", "shaders/std_effects.fx")
    ET.SubElement(root, "materialKind").text = mat_data.get("materialKind", "solid")

    props = mat_data.get("properties", {})
    if props:
        props_elem = ET.SubElement(root, "properties")
        for k, v in props.items():
            p = ET.SubElement(props_elem, "property")
            ET.SubElement(p, "name").text = k
            if isinstance(v, bool):
                ET.SubElement(p, "type").text = "Bool"
                ET.SubElement(p, "value").text = str(v).lower()
            elif isinstance(v, int):
                ET.SubElement(p, "type").text = "Int"
                ET.SubElement(p, "value").text = str(v)
            elif isinstance(v, float):
                ET.SubElement(p, "type").text = "Float"
                ET.SubElement(p, "value").text = f"{v:.6f}"
            elif isinstance(v, (list, tuple)) and len(v) == 4:
                ET.SubElement(p, "type").text = "Vector4"
                ET.SubElement(p, "value").text = " ".join(f"{float(x):.6f}" for x in v)
            else:
                # treat as Texture path string
                ET.SubElement(p, "type").text = "Texture"
                ET.SubElement(p, "value").text = str(v)

    # Extended flags
    if "collisionFlags" in mat_data:
        ET.SubElement(root, "collisionFlags").text = str(int(mat_data["collisionFlags"]))
    if "alphaTestEnable" in mat_data:
        ET.SubElement(root, "alphaTestEnable").text = str(bool(mat_data["alphaTestEnable"])).lower()
    if "doubleSided" in mat_data:
        ET.SubElement(root, "doubleSided").text = str(bool(mat_data["doubleSided"])).lower()

    write_xml_file(root, filepath)
    logger.info(f".mfm written: {filepath}")
