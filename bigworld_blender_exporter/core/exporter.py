import bpy
from ..utils import logger
from .model_processor import ModelProcessor
from .animation_processor import AnimationProcessor
from .material_processor import MaterialProcessor

class BigWorldExporter:
    """
    主导出器类，负责整体导出流程。
    """
    def __init__(self, context, settings):
        self.context = context
        self.settings = settings
        self.model_data = {}
        self.visual_data = {}
        self.primitives_data = {}

    def export(self):
        logger.info("开始导出流程 Start export process")
        try:
            self.collect_data()
            self.validate()
            self.write_files()
            self._write_manifest()
            logger.info("导出完成 Export finished")
        except Exception as e:
            logger.error(f"导出流程异常: {e}")
            raise

    def _write_manifest(self):
        """生成导出清单manifest，包含所有导出文件及统计信息。"""
        import os
        export_root = self.settings.export_path or '.'
        manifest_path = os.path.join(export_root, "export_manifest.txt")
        files = []
        for root, _, filenames in os.walk(export_root):
            for fname in filenames:
                if not fname.endswith('.log'):
                    files.append(os.path.relpath(os.path.join(root, fname), export_root))
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write("BigWorld导出清单\n")
            f.write(f"总文件数: {len(files)}\n")
            for fname in files:
                f.write(fname + "\n")
        logger.info(f"导出清单已生成: {manifest_path}")

    def collect_data(self):
        logger.info("收集数据 Collecting data")
        # 这里只做示例，实际应遍历 context 中所有需要导出的对象
        for obj in self.context.selected_objects:
            # 模型
            from .model_processor import ModelProcessor
            model = ModelProcessor().process(obj, self.settings)
            self.model_data[obj.name] = model
            # 材质
            from .material_processor import MaterialProcessor
            mats = MaterialProcessor().process(obj, self.settings)
            self.visual_data[obj.name] = mats
        # 动画（如有）
        if self.settings.export_animation:
            for obj in self.context.selected_objects:
                if hasattr(obj, 'animation_data') and obj.animation_data and obj.animation_data.action:
                    from .animation_processor import AnimationProcessor
                    anim_data = AnimationProcessor().process(obj, obj.animation_data.action, self.settings)
                    self.primitives_data[obj.name] = anim_data

    def validate(self):
        logger.info("验证数据 Validating data")
        # TODO: 实现更详细的数据完整性检查
        pass

    def write_files(self):
        logger.info("写入文件 Writing files")
        from ..formats import model_format, visual_format, primitives_format, animation_format, material_format
        from ..config import MODELS_SUBFOLDER, ANIMATIONS_SUBFOLDER, MATERIALS_SUBFOLDER
        import os
        export_root = self.settings.export_path or '.'
        models_dir = os.path.join(export_root, MODELS_SUBFOLDER)
        anims_dir = os.path.join(export_root, ANIMATIONS_SUBFOLDER)
        mats_dir = os.path.join(export_root, MATERIALS_SUBFOLDER)
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(anims_dir, exist_ok=True)
        os.makedirs(mats_dir, exist_ok=True)

        for obj_name, model in self.model_data.items():
            if not model:
                continue
            base_name = obj_name

            # .primitives
            primitives_path_rel = f"{MODELS_SUBFOLDER}/{base_name}.primitives"
            primitives_path = os.path.join(export_root, primitives_path_rel)
            vertices = model.get('vertices', [])
            indices = model.get('indices', [])
            primitives_format.export_primitives_file(primitives_path, vertices, indices, getattr(self.settings, 'vertex_format', 'STANDARD'))

            # .mfm (aggregate first material or default)
            material_info = self._build_material_file_data(obj_name)
            material_rel = f"{MATERIALS_SUBFOLDER}/{base_name}.mfm"
            material_path = os.path.join(export_root, material_rel)
            material_format.export_material_file(material_path, material_info)

            # .visual
            visual_info = {
                'world_space': 'false',
                'node': 'root',
                'primitives': primitives_path_rel,
                'material': material_rel,
                'start_index': 0,
                'end_index': len(indices),
                'start_vertex': 0,
                'end_vertex': len(vertices),
                'bbox_min': f"{model['bbox_min'][0]:.6f} {model['bbox_min'][1]:.6f} {model['bbox_min'][2]:.6f}",
                'bbox_max': f"{model['bbox_max'][0]:.6f} {model['bbox_max'][1]:.6f} {model['bbox_max'][2]:.6f}"
            }
            visual_path_rel = f"{MODELS_SUBFOLDER}/{base_name}.visual"
            visual_path = os.path.join(export_root, visual_path_rel)
            visual_format.export_visual_file(visual_path, visual_info)

            # .model
            model_info = {
                'visual': visual_path_rel,
                'parent': '',
                'extent': model.get('extent', 10.0),
                'bbox_min': f"{model['bbox_min'][0]:.6f} {model['bbox_min'][1]:.6f} {model['bbox_min'][2]:.6f}",
                'bbox_max': f"{model['bbox_max'][0]:.6f} {model['bbox_max'][1]:.6f} {model['bbox_max'][2]:.6f}",
                'bsp_model': ''
            }
            model_path = os.path.join(export_root, f"{MODELS_SUBFOLDER}/{base_name}.model")
            model_format.export_model_file(model_path, model_info)

        # .animation
        for obj_name, anim in self.primitives_data.items():
            if anim:
                animation_format.export_animation_file(os.path.join(anims_dir, f"{obj_name}.animation"), anim)

    def _build_material_file_data(self, obj_name: str):
        """Aggregate object material data into a single .mfm definition."""
        mats = self.visual_data.get(obj_name, [])
        # Default material
        merged = {
            'name': obj_name,
            'shader': 'shaders/std_effects.fx',
            'technique': 'default',
            'textures': {},
            'parameters': {}
        }
        for m in mats:
            # Merge textures if present
            for k, v in m.get('textures', {}).items():
                merged['textures'][k] = v
        return merged

def register():
    pass

def unregister():
    pass
