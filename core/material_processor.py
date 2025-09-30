# 文件位置: bigworld_blender_exporter/core/material_processor.py
# Material data processing for BigWorld export (aligned to EffectMaterial grammar)

import bpy
import os
from ..utils import logger
from .. import config
from ..utils.validation import ValidationError
from ..formats.material_format import export_material_file


class MaterialProcessor:
    """
    Responsible for collecting and processing material data
    and converting it into BigWorld EffectMaterial (.mfm) format.
    """

    def __init__(self):
        self.texture_cache = {}
        self.material_cache = {}

    def process(self, obj, settings):
        """
        Process all materials of a Blender object into EffectMaterial dicts.
        """
        logger.info(f"Processing materials for object: {obj.name}")
        materials_data = []
        for i, mat_slot in enumerate(obj.material_slots):
            if mat_slot.material:
                mat = mat_slot.material
                material_data = self._process_material(mat, settings, i)
                if material_data:
                    materials_data.append(material_data)
        return materials_data

    def _process_material(self, material, settings, index):
        """
        Convert a single Blender material into EffectMaterial dict.
        """
        identifier = material.name

        mat_data = {
            "identifier": identifier,
            "fx": getattr(settings, "default_fx", config.DEFAULT_SHADER),
            "materialKind": getattr(settings, "default_materialKind", 1),
            "properties": []
        }

        # --- Base color / diffuse ---
        if hasattr(material, "diffuse_color"):
            rgba = list(material.diffuse_color)
            mat_data["properties"].append({
                "name": "diffuseColor",
                "type": "Vector4",
                "value": rgba if len(rgba) == 4 else rgba + [1.0]
            })

        # --- Specular power ---
        if hasattr(material, "specular_intensity"):
            mat_data["properties"].append({
                "name": "specPower",
                "type": "Float",
                "value": float(material.specular_intensity * 128.0)
            })

        # --- Roughness / Metallic ---
        if hasattr(material, "roughness"):
            mat_data["properties"].append({
                "name": "roughness",
                "type": "Float",
                "value": float(material.roughness)
            })
        if hasattr(material, "metallic"):
            mat_data["properties"].append({
                "name": "metallic",
                "type": "Float",
                "value": float(material.metallic)
            })

        # --- Alpha ---
        if hasattr(material, "blend_method") and material.blend_method != "OPAQUE":
            alpha_val = material.diffuse_color[3] if len(material.diffuse_color) > 3 else 1.0
            mat_data["properties"].append({
                "name": "alphaRef",
                "type": "Float",
                "value": float(alpha_val)
            })

        # --- Textures ---
        textures = {}
        if material.use_nodes:
            textures = self._extract_textures_from_nodes(material, settings)
        else:
            textures = self._extract_textures_from_properties(material, settings)

        for tex_type, tex_path in textures.items():
            prop_name = self._map_texture_type(tex_type)
            mat_data["properties"].append({
                "name": prop_name,
                "type": "Texture",
                "value": tex_path
            })

        logger.info(f"Processed material: {material.name} with {len(mat_data['properties'])} properties")
        return mat_data

    def _extract_textures_from_nodes(self, material, settings):
        textures = {}
        if not material.node_tree:
            return textures
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                texture_type = self._get_texture_type_from_node(node)
                texture_path = self._process_texture_path(node.image, settings)
                if texture_path:
                    textures[texture_type] = texture_path
        return textures

    def _extract_textures_from_properties(self, material, settings):
        # Legacy fallback: Blender Internal style materials
        return {}

    def _get_texture_type_from_node(self, node):
        for output in node.outputs:
            for link in output.links:
                input_socket = link.to_socket
                if input_socket.name in ('Base Color', 'Color'):
                    return 'diffuse'
                elif input_socket.name == 'Normal':
                    return 'normal'
                elif input_socket.name == 'Roughness':
                    return 'roughness'
                elif input_socket.name == 'Metallic':
                    return 'metallic'
                elif input_socket.name == 'Emission':
                    return 'emission'
                elif input_socket.name == 'Alpha':
                    return 'alpha'
        return 'diffuse'

    def _map_texture_type(self, tex_type):
        mapping = {
            "diffuse": "diffuseMap",
            "normal": "normalMap",
            "roughness": "roughnessMap",
            "metallic": "metallicMap",
            "emission": "glowMap",
            "alpha": "alphaMap",
        }
        return mapping.get(tex_type, tex_type + "Map")

    def _process_texture_path(self, image, settings):
        if not image.filepath:
            return None
        if image.filepath.startswith('//'):
            texture_path = image.filepath[2:]
        else:
            texture_path = os.path.basename(image.filepath)

        if settings.copy_textures:
            self._copy_texture_file(image, settings)
        if settings.convert_to_dds:
            texture_path = self._convert_to_dds(texture_path)
        return texture_path

    def _copy_texture_file(self, image, settings):
        if not image.filepath or not settings.export_path:
            return
        textures_dir = os.path.join(settings.export_path, settings.texture_path)
        os.makedirs(textures_dir, exist_ok=True)
        if image.filepath.startswith('//'):
            source_path = os.path.join(bpy.path.abspath('//'), image.filepath[2:])
        else:
            source_path = bpy.path.abspath(image.filepath)
        dest_filename = os.path.basename(source_path)
        dest_path = os.path.join(textures_dir, dest_filename)
        try:
            import shutil
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied texture: {dest_filename}")
        except Exception as e:
            logger.error(f"Failed to copy texture {dest_filename}: {str(e)}")

    def _convert_to_dds(self, texture_path):
        if texture_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tga', '.bmp')):
            return os.path.splitext(texture_path)[0] + '.dds'
        return texture_path

    def export_material_data(self, material_data, filepath):
        """
        Export one EffectMaterial dict to .mfm file
        """
        export_material_file(filepath, material_data)


def register():
    pass

def unregister():
    pass
