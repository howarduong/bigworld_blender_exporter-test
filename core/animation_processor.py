# 文件位置: bigworld_blender_exporter/core/animation_processor.py
# -*- coding: utf-8 -*-
"""
Animation data processing for BigWorld export (aligned to .animation format)

改进点：
- 收集骨骼层级
- 收集关键帧（TRS）
- 支持 markers（事件标记）
- 支持 loop/cognate/alpha/interpolation 标志
"""

import bpy
from typing import Dict, Any, List
from ..utils import logger, math_utils

LOG = logger.get_logger("animation_processor")


class AnimationProcessor:
    """负责从 Blender 动画数据中收集骨骼、关键帧和事件标记"""

    def process(self, armature_obj: bpy.types.Object, action: bpy.types.Action, settings) -> Dict[str, Any]:
        """
        收集动画数据，返回 animation_data dict，供 formats/animation_format 使用。

        返回结构：
        {
          "name": str,
          "bones": List[Dict{name,parent}],
          "keyframes": List[Dict{frame,time,bone_transforms}],
          "frame_rate": float,
          "duration": float,
          "loop": bool,
          "cognate": bool,
          "alpha": bool,
          "interpolation": int,
          "markers": List[Dict{time,name}]
        }
        """
        LOG.info(f"Processing animation: {action.name} for armature {armature_obj.name}")

        bones = self._collect_bones(armature_obj)
        keyframes = self._collect_keyframes(armature_obj, action, bones, settings)
        markers = self._collect_markers(action, settings)

        start_frame = settings.start_frame
        end_frame = settings.end_frame
        frame_rate = settings.frame_rate
        duration = (end_frame - start_frame + 1) / frame_rate

        anim_data = {
            "name": action.name,
            "bones": bones,
            "keyframes": keyframes,
            "frame_rate": frame_rate,
            "duration": duration,
            "loop": getattr(settings, "loop_animation", False),
            "cognate": getattr(settings, "cognate", False),
            "alpha": getattr(settings, "alpha", False),
            "interpolation": getattr(settings, "interpolation_mode", 0),
            "markers": markers,
        }

        LOG.info(f"Animation processed: {action.name}, frames={len(keyframes)}, markers={len(markers)}")
        return anim_data

    # ------------------------
    # Internal helpers
    # ------------------------
    def _collect_bones(self, armature_obj: bpy.types.Object) -> List[Dict[str, Any]]:
        bones = []
        for bone in armature_obj.data.bones:
            bones.append({
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None
            })
        return bones

    def _collect_keyframes(self, armature_obj, action, bones, settings) -> List[Dict[str, Any]]:
        """采样关键帧，收集每个骨骼的 TRS"""
        start = settings.start_frame
        end = settings.end_frame
        frame_rate = settings.frame_rate

        keyframes = []
        scene = bpy.context.scene
        prev_action = armature_obj.animation_data.action if armature_obj.animation_data else None
        if armature_obj.animation_data:
            armature_obj.animation_data.action = action

        for frame in range(start, end + 1):
            scene.frame_set(frame)
            time_sec = (frame - start) / frame_rate
            bone_transforms = {}
            for bone in bones:
                pose_bone = armature_obj.pose.bones.get(bone["name"])
                if not pose_bone:
                    continue
                mat = pose_bone.matrix
                pos, rot, scl = math_utils.decompose_matrix(mat)
                bone_transforms[bone["name"]] = {
                    "position": pos,
                    "rotation": rot,
                    "scale": scl,
                }
            keyframes.append({
                "frame": frame,
                "time": time_sec,
                "bone_transforms": bone_transforms,
            })

        if armature_obj.animation_data and prev_action:
            armature_obj.animation_data.action = prev_action

        return keyframes

    def _collect_markers(self, action: bpy.types.Action, settings) -> List[Dict[str, Any]]:
        """收集动画事件标记（markers）"""
        markers = []
        frame_rate = settings.frame_rate
        for marker in action.pose_markers:
            time_sec = (marker.frame - settings.start_frame) / frame_rate
            markers.append({
                "time": time_sec,
                "name": marker.name,
            })
        return markers
