# 文件位置: bigworld_blender_exporter/core/animation_processor.py
# Animation data processing for BigWorld export (aligned to official .animation format)

import bpy
from mathutils import Vector, Quaternion, Matrix
from ..utils import logger
from ..utils.math_utils import blender_to_bigworld_matrix
from ..utils.validation import ValidationError
from ..formats.animation_format import export_animation_file


class AnimationProcessor:
    """
    Responsible for collecting and processing animation data
    and converting it into BigWorld .animation format.
    """

    def __init__(self):
        self.frame_cache = {}
        self.bone_cache = {}

    def process(self, obj, action, settings):
        """
        Process animation data for export.
        Returns animation_data dict ready for export_animation_file().
        """
        logger.info(f"Processing animation: {action.name} for object: {obj.name}")

        # 验证对象是否有骨架
        armature = obj.find_armature()
        if not armature:
            logger.error(f"No armature found for animated object: {obj.name}")
            return None

        # 动画数据结构
        animation_data = {
            "name": action.name,
            "frame_count": 0,
            "frame_rate": settings.frame_rate,
            "duration": 0.0,
            "bones": [],
            "keyframes": [],
            "loop": getattr(settings, "loop_animation", False),
        }

        # 处理骨骼层级
        bones_data = self._process_bones(armature)
        animation_data["bones"] = bones_data

        # 采样关键帧
        keyframes = self._sample_animation(obj, action, settings, armature, bones_data)
        animation_data["keyframes"] = keyframes
        animation_data["frame_count"] = len(keyframes)

        # 动画时长
        frame_range = settings.end_frame - settings.start_frame + 1
        animation_data["duration"] = frame_range / settings.frame_rate

        logger.info(f"Processed {len(keyframes)} keyframes for {len(bones_data)} bones")
        return animation_data

    def _process_bones(self, armature):
        """
        Collect bone hierarchy and assign stable indices.
        """
        bones_data = []
        for idx, bone in enumerate(armature.data.bones):
            bone_data = {
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
                "index": idx,
            }
            bones_data.append(bone_data)
        return bones_data

    def _sample_animation(self, obj, action, settings, armature, bones_data):
        """
        Sample animation frames into TRS per bone.
        """
        keyframes = []
        original_frame = bpy.context.scene.frame_current

        # 设置当前 Action
        if obj.animation_data:
            obj.animation_data.action = action

        # 遍历帧
        for frame in range(settings.start_frame, settings.end_frame + 1):
            bpy.context.scene.frame_set(frame)

            frame_data = {
                "frame": frame,
                "time": (frame - settings.start_frame) / settings.frame_rate,
                "bone_transforms": {}
            }

            # 遍历骨骼
            for bone in armature.pose.bones:
                transform_data = self._get_bone_transform(bone, settings)
                frame_data["bone_transforms"][bone.name] = transform_data

            keyframes.append(frame_data)

        # 恢复原始帧
        bpy.context.scene.frame_set(original_frame)

        # 关键帧优化
        if settings.optimize_keyframes:
            keyframes = self._optimize_keyframes(keyframes)

        return keyframes

    def _get_bone_transform(self, bone, settings):
        """
        Extract TRS for a bone at current frame, with coordinate system conversion.
        """
        matrix = bone.matrix

        # 提取 TRS
        position = list(matrix.to_translation())
        rotation = matrix.to_quaternion()
        scale = list(matrix.to_scale())

        # 坐标系转换
        if settings.coordinate_system == "Y_UP":
            M = blender_to_bigworld_matrix()
            # 位置
            pos_vec = Vector(position)
            position = list(M @ pos_vec)
            # 旋转
            rot_mat = M.to_3x3() @ rotation.to_matrix()
            rotation = rot_mat.to_quaternion()

        # 全局缩放
        if settings.global_scale != 1.0:
            position = [p * settings.global_scale for p in position]

        return {
            "position": position,
            "rotation": [rotation.x, rotation.y, rotation.z, rotation.w],
            "scale": scale,
        }

    def _optimize_keyframes(self, keyframes):
        """
        Remove redundant frames with no significant change.
        """
        if len(keyframes) < 3:
            return keyframes

        optimized = [keyframes[0]]
        for i in range(1, len(keyframes) - 1):
            current = keyframes[i]
            previous = keyframes[i - 1]
            next_frame = keyframes[i + 1]
            if self._is_frame_significant(current, previous, next_frame):
                optimized.append(current)
        optimized.append(keyframes[-1])

        logger.info(f"Optimized keyframes: {len(keyframes)} -> {len(optimized)}")
        return optimized

    def _is_frame_significant(self, current, previous, next_frame):
        """
        判断当前帧是否有显著变化。
        """
        threshold = 0.001
        rot_threshold = 0.01

        for bone_name in current["bone_transforms"]:
            if bone_name not in previous["bone_transforms"] or bone_name not in next_frame["bone_transforms"]:
                return True

            cur = current["bone_transforms"][bone_name]
            prev = previous["bone_transforms"][bone_name]

            # 位置差异
            pos_diff = Vector(cur["position"]) - Vector(prev["position"])
            if pos_diff.length > threshold:
                return True

            # 旋转差异
            cur_rot = Quaternion(cur["rotation"])
            prev_rot = Quaternion(prev["rotation"])
            if cur_rot.rotation_difference(prev_rot).angle > rot_threshold:
                return True

            # 缩放差异
            scale_diff = Vector(cur["scale"]) - Vector(prev["scale"])
            if scale_diff.length > threshold:
                return True

        return False

    def export_animation_data(self, animation_data, filepath):
        """
        Export animation data to .animation binary file
        """
        export_animation_file(filepath, animation_data)


def register():
    pass

def unregister():
    pass
