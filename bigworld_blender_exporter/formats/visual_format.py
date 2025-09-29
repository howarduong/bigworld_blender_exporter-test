# 文件位置: bigworld_blender_exporter/formats/visual_format.py
# Visual file format for BigWorld export

import os
import xml.etree.ElementTree as ET
from ..utils.xml_writer import write_xml_file
from ..utils.logger import get_logger

logger = get_logger("visual_format")


def export_visual_file(filepath, visual_data):
    """
    Export visual data to BigWorld .visual file
    """
    try:
        logger.info(f"Exporting visual file: {filepath}")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        root = ET.Element('visual')

        # node
        node = ET.SubElement(root, 'node')
        ET.SubElement(node, 'identifier').text = visual_data.get('node', 'root')
        transform = ET.SubElement(node, 'transform')
        ET.SubElement(transform, 'row0').text = '1.000000 0.000000 0.000000'
        ET.SubElement(transform, 'row1').text = '0.000000 1.000000 0.000000'
        ET.SubElement(transform, 'row2').text = '0.000000 0.000000 1.000000'
        ET.SubElement(transform, 'row3').text = '0.000000 0.000000 0.000000'

        # renderSet
        rset = ET.SubElement(root, 'renderSet')
        ET.SubElement(rset, 'treatAsWorldSpaceObject').text = str(
            visual_data.get('world_space', 'false')
        ).lower()
        ET.SubElement(rset, 'node').text = visual_data.get('node', 'root')

        geometry = ET.SubElement(rset, 'geometry')
        # 相对路径文件名
        vertices_name = visual_data.get('primitives', '').replace('.primitives', '.vertices').split('/')[-1]
        indices_name = visual_data.get('primitives', '').replace('.primitives', '.indices').split('/')[-1]
        ET.SubElement(geometry, 'vertices').text = vertices_name
        ET.SubElement(geometry, 'primitive').text = indices_name

        # primitiveGroup
        prim_group = ET.SubElement(geometry, 'primitiveGroup')
        ET.SubElement(prim_group, 'startIndex').text = str(visual_data.get('start_index', 0))
        ET.SubElement(prim_group, 'endIndex').text = str(visual_data.get('end_index', 0))
        ET.SubElement(prim_group, 'startVertex').text = str(visual_data.get('start_vertex', 0))
        ET.SubElement(prim_group, 'endVertex').text = str(visual_data.get('end_vertex', 0))

        # material
        mat = ET.SubElement(prim_group, 'material')
        ET.SubElement(mat, 'identifier').text = visual_data.get('material', '').replace('.mfm', '')
        ET.SubElement(mat, 'fx').text = 'shaders/std_effects.fx'
        props = ET.SubElement(mat, 'properties')
        for k, v in visual_data.get('parameters', {}).items():
            ET.SubElement(props, k).text = str(v)

        # boundingBox
        bbox = ET.SubElement(root, 'boundingBox')
        ET.SubElement(bbox, 'min').text = visual_data.get('bbox_min', '-1.0 -1.0 -1.0')
        ET.SubElement(bbox, 'max').text = visual_data.get('bbox_max', '1.0 1.0 1.0')

        # 写文件
        write_xml_file(root, filepath)
        logger.info(f"Visual file written: {filepath}")

    except Exception as e:
        logger.error(f"Failed to export visual file {filepath}: {str(e)}")
        raise


def export_visual_file_legacy(filepath, visual_data):
    """
    Legacy visual export function for backward compatibility
    """
    try:
        logger.warning("Using legacy visual export format")

        from ..utils.xml_writer import create_xml_root, add_xml_child

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
        logger.info(f"Legacy visual file written: {filepath}")

    except Exception as e:
        logger.error(f"Failed to export legacy visual file {filepath}: {str(e)}")
        raise
