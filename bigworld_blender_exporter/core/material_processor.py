# 文件位置: bigworld_blender_exporter/core/material_processor.py
# Material data processing for BigWorld export

import bpy
import os
from ..utils import logger
from .. import config

class MaterialProcessor:
    """
    Responsible for collecting and processing material data.
    负责材质数据的收集与处理。
    """
    
    def __init__(self):
        self.texture_cache = {}
        self.material_cache = {}

    def process(self, obj, settings):
        """Process material data for export"""
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
        """Process individual material"""
        material_data = {
            'name': material.name,
            'index': index,
            'shader': config.DEFAULT_SHADER,
            'technique': 'default',
            'textures': {},
            'parameters': {},
            'type': 'STANDARD'
        }
        
        # Get material properties
        material_data['diffuse_color'] = list(material.diffuse_color)
        material_data['specular_color'] = list(material.specular_color)
        material_data['roughness'] = material.roughness
        material_data['metallic'] = material.metallic
        material_data['alpha'] = material.diffuse_color[3] if len(material.diffuse_color) > 3 else 1.0
        
        # Process textures
        if material.use_nodes:
            material_data['textures'] = self._extract_textures_from_nodes(material, settings)
        else:
            material_data['textures'] = self._extract_textures_from_properties(material, settings)
        
        # Set material type based on properties
        if material_data['textures'].get('normal'):
            material_data['type'] = 'DETAILED'
        elif material_data['metallic'] > 0.5:
            material_data['type'] = 'METALLIC'
        
        logger.info(f"Processed material: {material.name} with {len(material_data['textures'])} textures")
        return material_data

    def _extract_textures_from_nodes(self, material, settings):
        """Extract textures from material nodes"""
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
        """Extract textures from material properties (legacy)"""
        textures = {}
        
        # This is for materials without node trees
        # In Blender 4.5+, most materials use nodes, but we keep this for compatibility
        
        return textures

    def _get_texture_type_from_node(self, node):
        """Determine texture type from node connections"""
        # Check what the node is connected to
        for output in node.outputs:
            for link in output.links:
                input_socket = link.to_socket
                if input_socket.name == 'Base Color' or input_socket.name == 'Color':
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
        
        # Default to diffuse if we can't determine
        return 'diffuse'

    def _process_texture_path(self, image, settings):
        """Process texture file path"""
        if not image.filepath:
            return None
        
        # Get relative path
        if image.filepath.startswith('//'):
            # Relative path
            texture_path = image.filepath[2:]  # Remove '//'
        else:
            # Absolute path - make it relative to project
            texture_path = os.path.basename(image.filepath)
        
        # Copy texture if requested
        if settings.copy_textures:
            self._copy_texture_file(image, settings)
        
        # Convert to DDS if requested
        if settings.convert_to_dds:
            texture_path = self._convert_to_dds(texture_path)
        
        return texture_path

    def _copy_texture_file(self, image, settings):
        """Copy texture file to export directory"""
        if not image.filepath or not settings.export_path:
            return
        
        # Create textures directory
        textures_dir = os.path.join(settings.export_path, settings.texture_path)
        os.makedirs(textures_dir, exist_ok=True)
        
        # Get source and destination paths
        if image.filepath.startswith('//'):
            source_path = os.path.join(bpy.path.abspath('//'), image.filepath[2:])
        else:
            source_path = bpy.path.abspath(image.filepath)
        
        dest_filename = os.path.basename(source_path)
        dest_path = os.path.join(textures_dir, dest_filename)
        
        # Copy file
        try:
            import shutil
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied texture: {dest_filename}")
        except Exception as e:
            logger.error(f"Failed to copy texture {dest_filename}: {str(e)}")

    def _convert_to_dds(self, texture_path):
        """Convert texture to DDS format"""
        # This would require additional DDS conversion library
        # For now, just change extension
        if texture_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tga', '.bmp')):
            return os.path.splitext(texture_path)[0] + '.dds'
        return texture_path

    def export_material_data(self, material_data, filepath):
        """Export material data to .mfm file"""
        from ..formats.material_format import export_material_file
        export_material_file(filepath, material_data)

def register():
    pass

def unregister():
    pass
