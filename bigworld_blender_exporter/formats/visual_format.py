# 文件位置: bigworld_blender_exporter/formats/visual_format.py
# Visual file format for BigWorld export

from ..utils.xml_writer import create_visual_xml, write_xml_file
from ..utils.logger import get_logger

logger = get_logger("visual_format")

def export_visual_file(filepath, visual_data):
    """Export visual data to BigWorld .visual file"""
    logger.info(f"Exporting visual file: {filepath}")
    
    # 严格对齐BigWorld官方.visual文件BNF/示例，支持多材质、骨骼节点树、完整嵌套
    import xml.etree.ElementTree as ET
    root = ET.Element('visual')
    # 1. NodeSection（支持骨骼树/静态树，递归）
    def build_node_tree(node_data):
        node_elem = ET.Element('node')
        ET.SubElement(node_elem, 'identifier').text = node_data.get('name', 'root')
        transform = ET.SubElement(node_elem, 'transform')
        for i in range(4):
            ET.SubElement(transform, f'row{i}').text = node_data.get(f'row{i}', ['1.000000 0.000000 0.000000', '0.000000 1.000000 0.000000', '0.000000 0.000000 1.000000', '0.000000 0.000000 0.000000'][i])
        # 递归子节点
        for child in node_data.get('children', []):
            node_elem.append(build_node_tree(child))
        return node_elem
    node_tree = visual_data.get('node_tree')
    if node_tree:
        root.append(build_node_tree(node_tree))
    else:
        # 默认root节点
        node = ET.SubElement(root, 'node')
        ET.SubElement(node, 'identifier').text = visual_data.get('node', 'root')
        transform = ET.SubElement(node, 'transform')
        ET.SubElement(transform, 'row0').text = '1.000000 0.000000 0.000000'
        ET.SubElement(transform, 'row1').text = '0.000000 1.000000 0.000000'
        ET.SubElement(transform, 'row2').text = '0.000000 0.000000 1.000000'
        ET.SubElement(transform, 'row3').text = '0.000000 0.000000 0.000000'

    # 2. renderSet（支持多材质/多geometry）
    render_set = ET.SubElement(root, 'renderSet')
    ET.SubElement(render_set, 'treatAsWorldSpaceObject').text = str(visual_data.get('world_space', 'false')).lower()
    ET.SubElement(render_set, 'node').text = visual_data.get('node', 'root')
    geometries = visual_data.get('geometries') or [visual_data]
    for geo in geometries:
        geometry = ET.SubElement(render_set, 'geometry')
        # 顶点/索引文件名
        vertices_name = geo.get('primitives', '').replace('.primitives', '.vertices').split('/')[-1]
        indices_name = geo.get('primitives', '').replace('.primitives', '.indices').split('/')[-1]
        ET.SubElement(geometry, 'vertices').text = vertices_name
        ET.SubElement(geometry, 'primitive').text = indices_name
        # 3. primitiveGroup（支持多组/多材质）
        prim_groups = geo.get('primitive_groups') or [{}]
        for group in prim_groups:
            prim_group = ET.SubElement(geometry, 'primitiveGroup')
            # startIndex/endIndex/startVertex/endVertex可选
            for k in ['startIndex','endIndex','startVertex','endVertex']:
                if k in group:
                    ET.SubElement(prim_group, k).text = str(group[k])
            # 4. material嵌套
            mat = ET.SubElement(prim_group, 'material')
            ET.SubElement(mat, 'identifier').text = group.get('material', geo.get('material','')).replace('.mfm','')
            ET.SubElement(mat, 'fx').text = group.get('fx', geo.get('fx','shaders/std_effects.fx'))
            # 可扩展更多材质属性，如texture、property等
            for tex in group.get('textures', []):
                tex_elem = ET.SubElement(mat, 'texture')
                tex_elem.text = tex
            for prop_name, prop_val in group.get('properties', {}).items():
                prop_elem = ET.SubElement(mat, prop_name)
                prop_elem.text = str(prop_val)

    # 5. boundingBox
    bbox = ET.SubElement(root, 'boundingBox')
    ET.SubElement(bbox, 'min').text = visual_data.get('bbox_min', '-1.0 -1.0 -1.0')
    ET.SubElement(bbox, 'max').text = visual_data.get('bbox_max', '1.0 1.0 1.0')

    # 6. 其他可选字段（如skeleton、animation等，留作扩展）

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
