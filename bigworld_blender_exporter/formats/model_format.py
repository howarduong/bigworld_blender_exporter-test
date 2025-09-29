# 文件位置: bigworld_blender_exporter/formats/model_format.py
# Model file format for BigWorld export

from ..utils.xml_writer import create_model_xml, write_xml_file
from ..utils.logger import get_logger

logger = get_logger("model_format")

def export_model_file(filepath, model_data):
    """Export model data to BigWorld .model file"""
    logger.info(f"Exporting model file: {filepath}")
    
    # 严格对齐BigWorld官方.model文件BNF/示例，支持多材质、动画、父节点、bsp等，顺序与嵌套完全一致
    import xml.etree.ElementTree as ET
    root = ET.Element('model')
    # 1. metaData
    meta = ET.SubElement(root, 'metaData')
    ET.SubElement(meta, 'copyright').text = 'Copyright BigWorld Pty Ltd.  Use freely in any BigWorld licensed game.'
    ET.SubElement(meta, 'created_by').text = model_data.get('created_by', 'blender_exporter')
    ET.SubElement(meta, 'created_on').text = str(model_data.get('created_on', '0'))
    ET.SubElement(meta, 'modified_by').text = model_data.get('modified_by', 'blender_exporter')
    ET.SubElement(meta, 'modified_on').text = str(model_data.get('modified_on', '0'))
    # 2. nodefullVisual
    ET.SubElement(root, 'nodefullVisual').text = model_data.get('visual', '')
    # 3. materialNames（支持多材质）
    mats = model_data.get('materials', [])
    mat_names = ','.join([m['name'] for m in mats]) if mats else ''
    ET.SubElement(root, 'materialNames').text = mat_names
    # 4. visibilityBox
    visbox = ET.SubElement(root, 'visibilityBox')
    ET.SubElement(visbox, 'min').text = model_data.get('bbox_min', '-1.0 -1.0 -1.0')
    ET.SubElement(visbox, 'max').text = model_data.get('bbox_max', '1.0 1.0 1.0')
    # 5. extent
    ET.SubElement(root, 'extent').text = f"{model_data.get('extent', 10.0):.6f}"
    # 6. parent
    ET.SubElement(root, 'parent').text = model_data.get('parent', '')
    # 7. action/animation（占位，支持动画列表）
    actions = model_data.get('actions', [])
    if actions:
        actions_elem = ET.SubElement(root, 'actions')
        for act in actions:
            act_elem = ET.SubElement(actions_elem, 'action')
            act_elem.text = act
    animations = model_data.get('animations', [])
    if animations:
        anims_elem = ET.SubElement(root, 'animations')
        for anim in animations:
            anim_elem = ET.SubElement(anims_elem, 'animation')
            anim_elem.text = anim
    # 8. editorOnly（可选保留）
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
