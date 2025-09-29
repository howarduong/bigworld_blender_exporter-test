import os
import json
import bpy
from datetime import datetime

from .config_utils import get_config
from .logger import setup_logger
from .path_utils import ensure_dir, normalize_path, exists_case_sensitive
from .fx_checker import resolve_fx_for_material
from .textures import export_image
from .primitives_binary_writer import write_primitives_binary
from .visual_writer import write_visual_for_object
from .model_writer import write_model_for_object

LOG = setup_logger()

def preflight_check(scene, config):
    res_root = os.path.abspath(config.get("res_root", "res"))
    checks = {"ok": [], "warn": [], "error": []}
    if not os.path.isdir(res_root):
        checks["error"].append(f"未找到 res 根目录: {res_root}")
    for m in bpy.data.materials:
        fx_hint = getattr(m, "bigworld_fx", "") if hasattr(m, "bigworld_fx") else ""
        resolved, status, candidates = resolve_fx_for_material(
            fx_hint, res_root,
            auto_mode=config.getboolean("auto_fx_mode"),
            default_fx=config.get("default_fx"),
            material_name=m.name
        )
        if status == "ok":
            checks["ok"].append(f"材质 {m.name} 使用 fx {resolved}")
        elif status == "candidate_used":
            checks["warn"].append(f"材质 {m.name} fx '{fx_hint}' → 候选 {resolved}")
        elif status == "default_used":
            checks["warn"].append(f"材质 {m.name} fx '{fx_hint}' 未找到，使用默认 {resolved}")
        else:
            checks["warn"].append(f"材质 {m.name} fx '{fx_hint}' 缺失，无候选")
    return checks

def create_tmp_dir():
    root = os.path.join(os.path.dirname(__file__), "..", "tmp_export")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.normpath(os.path.join(root, ts))
    ensure_dir(out)
    return out

def _case_exists(base_tmp_res, relpath, strict=False):
    full = os.path.normpath(os.path.join(base_tmp_res, relpath))
    if strict:
        return exists_case_sensitive(full), full
    return os.path.exists(full), full

class BIGWORLDEXPORTER_OT_export(bpy.types.Operator):
    bl_idname = "bigworld.export"
    bl_label = "Export BigWorld Model (enhanced)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        config = get_config()
        LOG.info("开始导出 BigWorld 模型")
        LOG.info(f"配置: unitScale={config.get('unitScale')} res_root={config.get('res_root')} default_fx={config.get('default_fx')} normal_mapped={config.get('normal_mapped')} primitives_binary={config.get('primitives_binary')} prefer_dds={config.get('prefer_dds')} max_uv_layers={config.get('max_uv_layers')} force_static_hierarchy={config.get('force_static_hierarchy')}")

        checks = preflight_check(context.scene, config)
        for k, lst in checks.items():
            for item in lst:
                if k == "error":
                    LOG.error(item)
                elif k == "warn":
                    LOG.warning(item)
                else:
                    LOG.info(item)
        if checks.get("error"):
            self.report({'ERROR'}, "预检失败，请查看日志")
            return {'CANCELLED'}

        tmp_dir = create_tmp_dir()
        tmp_res_root = os.path.join(tmp_dir, config.get("res_root", "res"))
        ensure_dir(tmp_res_root)
        LOG.info(f"临时导出目录: {tmp_dir}")

        res_root_abs = os.path.abspath(config.get("res_root", "res"))
        fx_map = {}
        material_fx_map = {}
        prefer_dds = bool(config.getboolean("prefer_dds"))

        for idx, mat in enumerate(bpy.data.materials):
            fx_hint = getattr(mat, "bigworld_fx", "") if hasattr(mat, "bigworld_fx") else ""
            resolved_fx, status, candidates = resolve_fx_for_material(
                fx_hint, res_root_abs,
                auto_mode=config.getboolean("auto_fx_mode"),
                default_fx=config.get("default_fx"),
                material_name=mat.name
            )
            fx_map[mat.name] = {
                "original": fx_hint,
                "resolved": resolved_fx,
                "status": status,
                "candidates": candidates
            }
            textures_list = []
            if mat.node_tree:
                for n in mat.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and getattr(n, "image", None):
                        name_lower = (n.name or "").lower()
                        color_space = "linear" if "normal" in name_lower else "srgb"
                        tex_rel = export_image(n.image, tmp_res_root, config.get("res_root","res"), prefer_dds=prefer_dds, color_space=color_space)
                        if tex_rel:
                            textures_list.append(tex_rel)
            material_fx_map[idx] = {"name": mat.name, "fx": resolved_fx or config.get("default_fx"), "textures": textures_list}

        with open(os.path.join(tmp_dir, "fx_map.json"), "w", encoding="utf-8") as f:
            json.dump(fx_map, f, indent=2, ensure_ascii=False)

        exported = []
        normal_mapped_flag = bool(config.getboolean("normal_mapped"))
        max_uv_layers = int(config.get("max_uv_layers", 2))
        force_static_hierarchy = bool(config.getboolean("force_static_hierarchy"))
        strict_case = bool(config.getboolean("strict_case_check"))

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                LOG.info(f"跳过非网格对象 {obj.name}")
                continue
            LOG.info(f"导出对象: {obj.name}")

            primitives_meta = write_primitives_binary(
                obj, tmp_res_root, rel_primitives_dir="primitives",
                config={"normal_mapped": normal_mapped_flag, "max_uv_layers": max_uv_layers}
            )
            visual_rel = write_visual_for_object(
                obj, primitives_meta, material_fx_map, tmp_res_root,
                rel_visual_dir="visuals",
                materialKind=int(config.get("materialKind", 0)),
                collisionFlags=int(config.get("collisionFlags", 0)),
                force_static_hierarchy=force_static_hierarchy
            )
            # materialNames：按 slots 顺序（以 material_fx_map 的 key 排序）
            mat_names = [material_fx_map.get(i, {}).get("name", f"mat_{i}") for i in range(len(material_fx_map))]
            model_rel = write_model_for_object(
                obj, visual_rel, tmp_res_root, rel_model_dir="models",
                bounding_box=primitives_meta.get("bounding_box"),
                material_names=mat_names
            )

            exported.append({
                "object": obj.name,
                "model": model_rel,
                "visual": visual_rel,
                "primitives": primitives_meta,
                "materials": material_fx_map
            })
            LOG.info(f"完成 {obj.name}: model={model_rel}, visual={visual_rel}")

        manifest_path = os.path.join(tmp_dir, "export_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(exported, mf, indent=2, ensure_ascii=False)
        LOG.info(f"清单已保存: {manifest_path}")

        errors = []
        for em in exported:
            pm = em["primitives"]
            needed = [pm["file"], em["visual"], em["model"]]
            for rel in needed:
                ok, full = _case_exists(tmp_res_root, rel, strict=strict_case)
                if not ok:
                    errors.append(f"缺失或大小写不匹配: {full}")

        if errors:
            for e in errors:
                LOG.error(e)
            LOG.error(f"导出存在问题，保留临时目录用于调试: {tmp_dir}")
            self.report({'WARNING'}, "导出完成但存在问题，请查看日志")
        else:
            LOG.info("导出自检通过，所有文件存在")
            self.report({'INFO'}, f"导出完成，临时目录: {tmp_dir}")

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(BIGWORLDEXPORTER_OT_export.bl_idname, text="Export BigWorld Model (enhanced)")

def register():
    bpy.utils.register_class(BIGWORLDEXPORTER_OT_export)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    bpy.utils.unregister_class(BIGWORLDEXPORTER_OT_export)

if __name__ == "__main__":
    register()
