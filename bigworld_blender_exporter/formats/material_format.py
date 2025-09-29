# 文件位置: bigworld_blender_exporter/formats/material_format.py
# Material file format for BigWorld export

import os
from ..utils.xml_writer import create_material_xml, write_xml_file
from ..utils.logger import get_logger

logger = get_logger("material_format")


def export_material_file(filepath, material_data):
    """
    Export material data to BigWorld .mfm file
    """
    try:
        logger.info(f"Exporting material file: {filepath}")

        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Create XML structure
        root = create_material_xml(material_data)

        # Write XML file
        write_xml_file(root, filepath)
        logger.info(f"Material file written: {filepath}")

    except Exception as e:
        logger.error(f"Failed to export material file {filepath}: {str(e)}")
        raise


def export_material_file_legacy(filepath, material_data):
    """
    Legacy material export function for backward compatibility
    """
    try:
        logger.warning("Using legacy material export format")

        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("material\n{\n")
            # Shader
            f.write(f" fx = {material_data.get('shader', 'shaders/std_effects.fx')}\n")
            f.write(f" technique = {material_data.get('technique', 'default')}\n")

            # Textures
            if material_data.get('textures'):
                f.write(" textures\n {\n")
                for tex_type, tex_path in material_data['textures'].items():
                    f.write(f"  {tex_type} = {tex_path}\n")
                f.write(" }\n")

            # Parameters
            if material_data.get('parameters'):
                f.write(" parameters\n {\n")
                for param_name, param_value in material_data['parameters'].items():
                    f.write(f"  {param_name} = {param_value}\n")
                f.write(" }\n")

            # PBR properties
            f.write(f" diffuse_color = {format_color(material_data.get('diffuse_color', [1, 1, 1, 1]))}\n")
            f.write(f" specular_color = {format_color(material_data.get('specular_color', [1, 1, 1, 1]))}\n")
            f.write(f" emissive_color = {format_color(material_data.get('emissive_color', [0, 0, 0, 1]))}\n")
            f.write(f" roughness = {material_data.get('roughness', 0.5)}\n")
            f.write(f" metallic = {material_data.get('metallic', 0.0)}\n")
            f.write(f" alpha = {material_data.get('alpha', 1.0)}\n")
            f.write("}\n")

        logger.info(f"Legacy material file written: {filepath}")

    except Exception as e:
        logger.error(f"Failed to export legacy material file {filepath}: {str(e)}")
        raise


def format_color(color):
    """Format color array as string"""
    if len(color) >= 4:
        return f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} {color[3]:.3f}"
    elif len(color) >= 3:
        return f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} 1.000"
    else:
        return "1.000 1.000 1.000 1.000"
