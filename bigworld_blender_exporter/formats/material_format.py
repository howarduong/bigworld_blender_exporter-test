# 文件位置: bigworld_blender_exporter/formats/material_format.py
# Material file format for BigWorld export

# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET
from ..utils.logger import get_logger

logger = get_logger("material_format")


def create_material_xml(base_name: str,
                        shader_path: str,
                        textures: dict,
                        parameters: dict = None) -> ET.ElementTree:
    """
    创建符合 BigWorld 规范的 .mfm XML 树

    Parameters:
        base_name: 材质基名 (e.g., "Chair")
        shader_path: 引擎 shader 路径 (e.g., "shaders/std_effects/normalmap_specmap.fx")
        textures: { property_name: texture_rel_path }
                  e.g., { "diffuseMap": "maps/chair_diffuse.dds" }
        parameters: { property_name: value } (Float/Vector4/Bool)

    Returns:
        xml.etree.ElementTree.ElementTree
    """

    root = ET.Element(f"{base_name}.mfm")

    # Shader
    fx_elem = ET.SubElement(root, "fx")
    fx_elem.text = shader_path

    # Textures
    for prop_name, tex_path in textures.items():
        prop_elem = ET.SubElement(root, "property")
        prop_elem.set("name", prop_name)
        tex_elem = ET.SubElement(prop_elem, "Texture")
        tex_elem.text = tex_path

    # Parameters
    if parameters:
        for prop_name, value in parameters.items():
            prop_elem = ET.SubElement(root, "property")
            prop_elem.set("name", prop_name)

            if isinstance(value, float) or isinstance(value, int):
                val_elem = ET.SubElement(prop_elem, "Float")
                val_elem.text = f"{value:.6f}"
            elif isinstance(value, (list, tuple)) and len(value) == 4:
                val_elem = ET.SubElement(prop_elem, "Vector4")
                val_elem.text = " ".join(f"{v:.6f}" for v in value)
            elif isinstance(value, bool):
                val_elem = ET.SubElement(prop_elem, "Bool")
                val_elem.text = "true" if value else "false"
            else:
                logger.warning(f"Unsupported parameter type for {prop_name}: {value}")

    return ET.ElementTree(root)


def export_material_file(filepath: str,
                         base_name: str,
                         shader_path: str,
                         textures: dict,
                         parameters: dict = None):
    """
    导出 .mfm 文件（符合 BigWorld 规范）
    - 如果文件已存在，则复用，不重复生成
    """

    if os.path.exists(filepath):
        logger.info(f"Material already exists, reusing: {filepath}")
        return

    try:
        logger.info(f"Exporting material file: {filepath}")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        tree = create_material_xml(base_name, shader_path, textures, parameters)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)

        logger.info(f"Material file written: {filepath}")
    except Exception as e:
        logger.error(f"Failed to export material file {filepath}: {str(e)}")
        raise
