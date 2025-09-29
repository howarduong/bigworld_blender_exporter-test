# -*- coding: utf-8 -*-
# 文件位置: bigworld_blender_exporter/formats/model_format.py
# Model file format for BigWorld export

import os
import xml.etree.ElementTree as ET
from ..utils.logger import get_logger
from ..utils.xml_writer import write_xml_file

logger = get_logger("model_format")


def export_model_file(filepath, model_data):
    """
    导出 BigWorld .model 文件（符合官方规范 ch11）

    参数:
        filepath: 输出路径 (e.g., ".../chair.model")
        model_data: {
            "visual": "models/props/chair/chair",   # 相对res路径，不带扩展名
            "materials": ["chair_mat"],             # 可选材质名列表
            "bbox_min": "-1.0 -1.0 -1.0",
            "bbox_max": "1.0 1.0 1.0",
            "extent": 10.0,
            "parent": "",                           # 可选父模型
            "bsp_model": ""                         # 可选 BSP 模型
        }
    """

    logger.info(f"Exporting model file: {filepath}")

    # 根标签名必须与文件名一致
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    root = ET.Element(f"{base_name}.model")

    # metaData（可选）
    meta = ET.SubElement(root, "metaData")
    ET.SubElement(meta, "copyright").text = "Copyright BigWorld Pty Ltd. Use freely in any BigWorld licensed game."
    ET.SubElement(meta, "created_by").text = "blender_exporter"
    ET.SubElement(meta, "created_on").text = "0"
    ET.SubElement(meta, "modified_by").text = "blender_exporter"
    ET.SubElement(meta, "modified_on").text = "0"

    # nodefullVisual（必须，相对路径，不带扩展名）
    visual_path = model_data.get("visual", "")
    if visual_path.endswith(".visual"):
        visual_path = visual_path[:-7]
    ET.SubElement(root, "nodefullVisual").text = visual_path

    # materialNames（可选，支持多个材质名）
    mats = model_data.get("materials", [])
    ET.SubElement(root, "materialNames").text = " ".join(mats)

    # visibilityBox（必须）
    visbox = ET.SubElement(root, "visibilityBox")
    ET.SubElement(visbox, "min").text = model_data.get("bbox_min", "-1.0 -1.0 -1.0")
    ET.SubElement(visbox, "max").text = model_data.get("bbox_max", "1.0 1.0 1.0")

    # extent（必须，默认10.0）
    ET.SubElement(root, "extent").text = f"{float(model_data.get('extent', 10.0)):.6f}"

    # parent（可选）
    parent_val = model_data.get("parent", "")
    if parent_val:
        ET.SubElement(root, "parent").text = parent_val

    # editorOnly（可选，BSP 模型）
    bsp_model = model_data.get("bsp_model", "")
    if bsp_model:
        editor = ET.SubElement(root, "editorOnly")
        bsp = ET.SubElement(editor, "bspModels")
        ET.SubElement(bsp, "model").text = bsp_model

    # 写入文件
    write_xml_file(root, filepath)


def export_model_file_legacy(filepath, model_data):
    """
    旧版导出函数（仅兼容用，不推荐）
    """
    logger.warning("Using legacy model export format")

    from ..utils.xml_writer import create_xml_root, add_xml_child

    root = create_xml_root()

    visual_path = model_data.get("visual", "")
    if visual_path.endswith(".visual"):
        visual_path = visual_path[:-7]
    add_xml_child(root, "nodefullVisual", visual_path)

    add_xml_child(root, "parent", model_data.get("parent", ""))
    add_xml_child(root, "extent", f"{float(model_data.get('extent', 10.0)):.6f}")

    bbox = add_xml_child(root, "boundingBox")
    add_xml_child(bbox, "min", model_data.get("bbox_min", "-1.0 -1.0 -1.0"))
    add_xml_child(bbox, "max", model_data.get("bbox_max", "1.0 1.0 1.0"))

    if model_data.get("bsp_model", ""):
        editor = add_xml_child(root, "editorOnly")
        bsp = add_xml_child(editor, "bspModels")
        add_xml_child(bsp, "model", model_data.get("bsp_model", ""))

    write_xml_file(root, filepath)
