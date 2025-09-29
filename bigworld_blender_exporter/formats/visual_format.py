# 文件位置: bigworld_blender_exporter/formats/visual_format.py
# Visual file format for BigWorld export

from ..utils.xml_writer import create_visual_xml, write_xml_file
from ..utils.logger import get_logger

logger = get_logger("visual_format")

def export_visual_file(filepath, visual_data):
    """Export visual data to BigWorld .visual file"""
    logger.info(f"Exporting visual file: {filepath}")
    
    # Create XML structure（严格对齐BigWorld标准）
    import xml.etree.ElementTree as ET
    root = ET.Element('visual')
    # node树（静态模型用root节点，骨骼模型可扩展）
    node = ET.SubElement(root, 'node')
    ET.SubElement(node, 'identifier').text = visual_data.get('node', 'root')
    transform = ET.SubElement(node, 'transform')
    ET.SubElement(transform, 'row0').text = '1.000000 0.000000 0.000000'
    ET.SubElement(transform, 'row1').text = '0.000000 1.000000 0.000000'
    ET.SubElement(transform, 'row2').text = '0.000000 0.000000 1.000000'
    ET.SubElement(transform, 'row3').text = '0.000000 0.000000 0.000000'
    # renderSet
    rset = ET.SubElement(root, 'renderSet')
    ET.SubElement(rset, 'treatAsWorldSpaceObject').text = str(visual_data.get('world_space', 'false')).lower()
    ET.SubElement(rset, 'node').text = visual_data.get('node', 'root')
    geometry = ET.SubElement(rset, 'geometry')
    # 相对路径文件名
    vertices_name = visual_data.get('primitives', '').replace('.primitives', '.vertices').split('/')[-1]
    indices_name = visual_data.get('primitives', '').replace('.primitives', '.indices').split('/')[-1]
    ET.SubElement(geometry, 'vertices').text = vertices_name
    ET.SubElement(geometry, 'primitive').text = indices_name
    # primitiveGroup
    prim_group = ET.SubElement(geometry, 'primitiveGroup')
    prim_group.text = '0'
    # 嵌套材质信息（最简化，实际可扩展）
    mat = ET.SubElement(prim_group, 'material')
    ET.SubElement(mat, 'identifier').text = visual_data.get('material', '').replace('.mfm', '')
    ET.SubElement(mat, 'fx').text = 'shaders/std_effects.fx'
    # boundingBox
    bbox = ET.SubElement(root, 'boundingBox')
    ET.SubElement(bbox, 'min').text = visual_data.get('bbox_min', '-1.0 -1.0 -1.0')
    ET.SubElement(bbox, 'max').text = visual_data.get('bbox_max', '1.0 1.0 1.0')
    # Write XML file
    from ..utils.xml_writer import write_xml_file
    write_xml_file(root, filepath)

def export_visual_file_legacy(filepath, visual_data):
    """Legacy visual export function for backward compatibility"""
    logger.warning("Using legacy visual export format")
    
    from ..utils.xml_writer import create_xml_root, add_xml_child, write_xml_file
    
    root = create_xml_root()
    render_set = add_xml_child(root, 'renderSet')
    add_xml_child(render_set, 'treatAsWorldSpaceObject', str(visual_data.get('world_space', 'false')))
    add_xml_child(render_set, 'node', visual_data.get('node', 'root'))
    
    geometry = add_xml_child(render_set, 'geometry')
    add_xml_child(geometry, 'vertices', visual_data.get('primitives', ''))
    add_xml_child(geometry, 'primitive', 'triangles')
    
    group = add_xml_child(geometry, 'primitiveGroup')
    add_xml_child(group, 'material', visual_data.get('material', ''))
    add_xml_child(group, 'startIndex', str(visual_data.get('start_index', 0)))
    add_xml_child(group, 'endIndex', str(visual_data.get('end_index', 0)))
    add_xml_child(group, 'startVertex', str(visual_data.get('start_vertex', 0)))
    add_xml_child(group, 'endVertex', str(visual_data.get('end_vertex', 0)))
    
    bbox = add_xml_child(root, 'boundingBox')
    add_xml_child(bbox, 'min', visual_data.get('bbox_min', '-1.0 -1.0 -1.0'))
    add_xml_child(bbox, 'max', visual_data.get('bbox_max', '1.0 1.0 1.0'))
    
    write_xml_file(root, filepath)
