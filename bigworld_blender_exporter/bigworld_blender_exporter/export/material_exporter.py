# bigworld_blender_exporter/export/material_exporter.py

import os
import bpy

from ..utils.path import abs2res_relpath, norm_path
from ..utils.logger import logger

def export_materials(obj, res_root, target_dir):
    """
    从对象提取所有材质，导出成BigWorld标准.mfm文件，生成fx/贴图资源相对路径引用。
    :return: 材质列表 [{file: 路径, 类型等}, ...]
    """
    results = []
    for idx, mat in enumerate(obj.data.materials):
        mat_name = mat.name
        filename = f"{obj.name}_{mat_name}.mfm"
        mfm_path = os.path.join(target_dir, filename)
        fx_file = getattr(mat, "fx_file", "normalmap.fx")
        mfm_data = {
            "fx": fx_file,
            "params": {}
        }
        # 解析Node树，提取漫反射、法线、透明、位移、各贴图引用
        if hasattr(mat, "node_tree") and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    mfm_data["params"][node.label.lower() or node.name.lower()] = abs2res_relpath(node.image.filepath, res_root) if node.image else ""
        # 写为BigWorld标准mfm格式（XML/纯文本）
        write_mfm_file(mfm_path, mfm_data)
        results.append({"name": mat_name, "file": mfm_path, "type": "mfm"})
    return results

def write_mfm_file(path, data):
    """BigWorld .mfm为xml结构，字段详见官方文档。"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"""<material>
  <fx>{data["fx"]}</fx>
""")
        for k, v in data["params"].items():
            f.write(f"  <param name='{k}'>{v}</param>\n")
        f.write("</material>\n")
    logger.info(f"导出.mfm: {path}")
