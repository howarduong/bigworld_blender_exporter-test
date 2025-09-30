# 文件位置: bigworld_blender_exporter/formats/material_format.py
# Material file format for BigWorld export (.mfm aligned to EffectMaterial grammar)

import os
import xml.etree.ElementTree as ET
from ..utils.logger import get_logger
from ..utils.xml_writer import write_xml_file
from ..utils.validation import ValidationError

logger = get_logger("material_format")


def export_material_file(filepath, material_data):
    """
    Export material data to BigWorld .mfm file

    material_data dict expected keys:
      - identifier: str (material name, usually same as .mfm filename without extension)
      - fx: str (shader path, e.g. "shaders/std_effects/lightonly_skinned.fx")
      - materialKind: str or int
      - collisionFlags: str (optional)
      - properties: list of { name: str, type: str, value: any }
        type ∈ {"Texture","Vector4","Float","Bool","Int"}
    """
    logger.info(f"Exporting material file: {filepath}")

    # Create directory if it doesn't exist
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    root = ET.Element("material")

    eff = ET.SubElement(root, "EffectMaterial")
    ET.SubElement(eff, "identifier").text = material_data.get("identifier", "")
    ET.SubElement(eff, "fx").text = material_data.get("fx", "shaders/std_effects.fx")
    ET.SubElement(eff, "materialKind").text = str(material_data.get("materialKind", "0"))

    if "collisionFlags" in material_data:
        ET.SubElement(eff, "collisionFlags").text = str(material_data["collisionFlags"])

    # properties
    props = material_data.get("properties", [])
    for p in props:
        prop_elem = ET.SubElement(eff, "property")
        ET.SubElement(prop_elem, "name").text = p["name"]

        ptype = p["type"]
        val = p["value"]

        if ptype == "Texture":
            ET.SubElement(prop_elem, "Texture").text = str(val)
        elif ptype == "Vector4":
            if not (isinstance(val, (list, tuple)) and len(val) == 4):
                raise ValidationError(f"Vector4 property {p['name']} must be length 4")
            ET.SubElement(prop_elem, "Vector4").text = " ".join(f"{float(x):.6f}" for x in val)
        elif ptype == "Float":
            ET.SubElement(prop_elem, "Float").text = f"{float(val):.6f}"
        elif ptype == "Bool":
            ET.SubElement(prop_elem, "Bool").text = str(bool(val)).lower()
        elif ptype == "Int":
            ET.SubElement(prop_elem, "Int").text = str(int(val))
        else:
            raise ValidationError(f"Unsupported property type: {ptype}")

    # Write XML file
    write_xml_file(root, filepath)
    logger.info(f".mfm written: {filepath}")
