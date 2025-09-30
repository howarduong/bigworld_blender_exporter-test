import xml.etree.ElementTree as ET
import os

def create_xml_root(tag="root"):
    return ET.Element(tag)

def add_xml_child(parent, tag, text=None, attrib=None):
    elem = ET.SubElement(parent, tag)
    if text is not None:
        elem.text = str(text)
    if attrib:
        for k, v in attrib.items():
            elem.set(k, str(v))
    return elem

def write_xml_file(root, filepath):
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(filepath, encoding='utf-8', xml_declaration=True)

# High-level builders for BigWorld formats
def create_model_xml(model_data: dict):
    root = create_xml_root("root")
    add_xml_child(root, 'nodefullVisual', model_data.get('visual', ''))
    add_xml_child(root, 'parent', model_data.get('parent', ''))
    add_xml_child(root, 'extent', f"{model_data.get('extent', 10.0):.6f}")
    bbox = add_xml_child(root, 'boundingBox')
    add_xml_child(bbox, 'min', model_data.get('bbox_min', '-1.0 -1.0 -1.0'))
    add_xml_child(bbox, 'max', model_data.get('bbox_max', '1.0 1.0 1.0'))
    editor = add_xml_child(root, 'editorOnly')
    bsp = add_xml_child(editor, 'bspModels')
    add_xml_child(bsp, 'model', model_data.get('bsp_model', ''))
    return root

def create_visual_xml(visual_data: dict):
    root = create_xml_root("root")
    render_set = add_xml_child(root, 'renderSet')
    add_xml_child(render_set, 'treatAsWorldSpaceObject', str(visual_data.get('world_space', 'false')).lower())
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
    return root

def create_material_xml(material_data: dict):
    root = create_xml_root("root")
    add_xml_child(root, 'fx', material_data.get('shader', 'shaders/std_effects.fx'))
    add_xml_child(root, 'technique', material_data.get('technique', 'default'))
    textures = add_xml_child(root, 'textures')
    for k, v in material_data.get('textures', {}).items():
        add_xml_child(textures, k, v)
    params = add_xml_child(root, 'parameters')
    for k, v in material_data.get('parameters', {}).items():
        add_xml_child(params, k, str(v))
    return root
