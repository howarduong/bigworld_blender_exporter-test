# 文件位置: bigworld_blender_exporter/formats/model_format.py
# Model file format for BigWorld export

from ..utils.xml_writer import create_model_xml, write_xml_file
from ..utils.logger import get_logger

logger = get_logger("model_format")

def export_model_file(filepath, model_data):
    """Export model data to BigWorld .model file"""
    logger.info(f"Exporting model file: {filepath}")
    
    # Create XML structure（严格对齐BigWorld标准）
    import xml.etree.ElementTree as ET
    root = ET.Element('model')
    # metaData（可选，填默认值）
    meta = ET.SubElement(root, 'metaData')
    ET.SubElement(meta, 'copyright').text = 'Copyright BigWorld Pty Ltd.  Use freely in any BigWorld licensed game.'
    ET.SubElement(meta, 'created_by').text = 'blender_exporter'
    ET.SubElement(meta, 'created_on').text = '0'
    ET.SubElement(meta, 'modified_by').text = 'blender_exporter'
    ET.SubElement(meta, 'modified_on').text = '0'
    # nodefullVisual
    ET.SubElement(root, 'nodefullVisual').text = model_data.get('visual', '')
    # materialNames（可为空）
    ET.SubElement(root, 'materialNames').text = ''
    # visibilityBox（用原boundingBox数据填充）
    visbox = ET.SubElement(root, 'visibilityBox')
    ET.SubElement(visbox, 'min').text = model_data.get('bbox_min', '-1.0 -1.0 -1.0')
    ET.SubElement(visbox, 'max').text = model_data.get('bbox_max', '1.0 1.0 1.0')
    # extent（建议默认10.000000）
    ET.SubElement(root, 'extent').text = f"{model_data.get('extent', 10.0):.6f}"
    # parent
    ET.SubElement(root, 'parent').text = model_data.get('parent', '')
    # editorOnly（可选保留）
    editor = ET.SubElement(root, 'editorOnly')
    bsp = ET.SubElement(editor, 'bspModels')
    ET.SubElement(bsp, 'model').text = model_data.get('bsp_model', '')
    # Write XML file
    from ..utils.xml_writer import write_xml_file
    write_xml_file(root, filepath)

def export_model_file_legacy(filepath, model_data):
    """Legacy model export function for backward compatibility"""
    logger.warning("Using legacy model export format")
    
    from ..utils.xml_writer import create_xml_root, add_xml_child, write_xml_file
    
    root = create_xml_root()
    add_xml_child(root, 'nodefullVisual', model_data.get('visual', ''))
    add_xml_child(root, 'parent', model_data.get('parent', ''))
    add_xml_child(root, 'extent', model_data.get('extent', '10.0'))
    
    bbox = add_xml_child(root, 'boundingBox')
    add_xml_child(bbox, 'min', model_data.get('bbox_min', '-1.0 -1.0 -1.0'))
    add_xml_child(bbox, 'max', model_data.get('bbox_max', '1.0 1.0 1.0'))
    
    editor = add_xml_child(root, 'editorOnly')
    bsp = add_xml_child(editor, 'bspModels')
    add_xml_child(bsp, 'model', model_data.get('bsp_model', ''))
    
    write_xml_file(root, filepath)
