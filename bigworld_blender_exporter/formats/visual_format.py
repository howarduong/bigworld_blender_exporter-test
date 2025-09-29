# -*- coding: utf-8 -*-
import os
import xml.etree.ElementTree as ET


def create_visual_xml(base_name: str,
                      vertices_tag: str,
                      indices_tag: str,
                      material_rel_path: str,
                      shader_path: str,
                      textures: list,
                      bounding_box: tuple) -> ET.ElementTree:
    """
    创建符合 BigWorld 规范的 .visual XML 树

    Parameters:
        base_name: 模型基名 (e.g., "Chair")
        vertices_tag: 与 .primitives 内一致的标签 (e.g., "Chair.vertices")
        indices_tag: 与 .primitives 内一致的标签 (e.g., "Chair.indices")
        material_rel_path: 相对 res/ 的材质路径 (e.g., "materials/Chair.mfm")
        shader_path: 引擎 shader 路径 (e.g., "shaders/std_effects/normalmap_specmap.fx")
        textures: [(property_name, texture_rel_path), ...]
                  e.g., [("diffuseMap", "maps/chair_diffuse.dds")]
        bounding_box: ((minx, miny, minz), (maxx, maxy, maxz))

    Returns:
        xml.etree.ElementTree.ElementTree
    """

    root = ET.Element(f"{base_name}.visual")

    # renderSet
    render_set = ET.SubElement(root, "renderSet")
    geometry = ET.SubElement(render_set, "geometry")

    # vertices / primitive
    v_elem = ET.SubElement(geometry, "vertices")
    v_elem.text = vertices_tag

    p_elem = ET.SubElement(geometry, "primitive")
    p_elem.text = indices_tag

    # primitiveGroup
    prim_group = ET.SubElement(geometry, "primitiveGroup")
    prim_group.set("id", "0")

    material = ET.SubElement(prim_group, "material")

    # 材质引用
    mat_elem = ET.SubElement(material, "identifier")
    mat_elem.text = os.path.splitext(os.path.basename(material_rel_path))[0]

    fx_elem = ET.SubElement(material, "fx")
    fx_elem.text = shader_path

    # 材质属性 (贴图等)
    for prop_name, tex_path in textures:
        prop_elem = ET.SubElement(material, "property")
        prop_elem.set("name", prop_name)
        tex_elem = ET.SubElement(prop_elem, "Texture")
        tex_elem.text = tex_path

    # boundingBox
    bb_elem = ET.SubElement(root, "boundingBox")
    min_elem = ET.SubElement(bb_elem, "min")
    min_elem.text = " ".join(map(str, bounding_box[0]))
    max_elem = ET.SubElement(bb_elem, "max")
    max_elem.text = " ".join(map(str, bounding_box[1]))

    return ET.ElementTree(root)


def export_visual_file(filepath: str,
                       base_name: str,
                       vertices_tag: str,
                       indices_tag: str,
                       material_rel_path: str,
                       shader_path: str,
                       textures: list,
                       bounding_box: tuple):
    """
    导出 .visual 文件

    Parameters:
        filepath: 输出路径 (e.g., ".../Chair.visual")
        其他参数同 create_visual_xml
    """
    tree = create_visual_xml(base_name, vertices_tag, indices_tag,
                             material_rel_path, shader_path, textures, bounding_box)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)
