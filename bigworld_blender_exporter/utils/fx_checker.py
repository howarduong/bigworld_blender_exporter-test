# 文件位置: bigworld_blender_exporter/utils/fx_checker.py
# Blender材质节点自动映射BigWorld FX property，缺失时给出候选

import bpy
import json
import os
from ..utils.logger import get_logger

logger = get_logger("fx_checker")

FX_MAP_PATH = os.path.join(os.path.dirname(__file__), '../config/fx_map.json')

def load_fx_map():
    if not os.path.exists(FX_MAP_PATH):
        logger.warning(f"未找到FX映射表: {FX_MAP_PATH}")
        return {}
    with open(FX_MAP_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_fx_for_material(material):
    """
    自动解析Blender材质节点，映射到BigWorld FX property
    :param material: bpy.types.Material
    :return: fx字符串或候选列表
    """
    fx_map = load_fx_map()
    if not material or not material.use_nodes:
        return fx_map.get('default', 'shaders/std_effects.fx')
    for node in material.node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree:
            fx = fx_map.get(node.node_tree.name)
            if fx:
                return fx
        elif node.type == 'BSDF_PRINCIPLED':
            return fx_map.get('Principled BSDF', 'shaders/std_effects.fx')
    # 未匹配，返回候选
    return list(fx_map.values())
