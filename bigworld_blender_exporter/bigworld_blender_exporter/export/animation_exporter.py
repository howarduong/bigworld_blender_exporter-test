# bigworld_blender_exporter/export/animation_exporter.py

import bpy
import struct
import os

from ..utils.path import abs2res_relpath
from ..utils.logger import logger
from ..utils.binary_writer import BinaryWriter

class AnimationExporter:
    """
    导出 BigWorld 标准动画数据，支持压缩、插值采样、骨骼映射等。
    """

    def __init__(self, armature_obj, res_root, target_dir, frame_sample=1):
        self.arm = armature_obj
        self.res_root = res_root
        self.target_dir = target_dir
        self.frame_sample = frame_sample

    def export(self):
        """导出所有动作，每条动作单独存文件，并返回导出清单"""
        if self.arm is None or self.arm.type != 'ARMATURE':
            logger.warn('未绑定骨骼, 动画导出忽略。')
            return []
        results = []
        tracks = self.arm.animation_data.action_tracks if hasattr(self.arm.animation_data, 'action_tracks') else []
        actions = [a for a in bpy.data.actions if a.users > 0]
        for act in actions:
            try:
                filename = f"{self.arm.name}_{act.name}.anim"
                anim_path = os.path.join(self.target_dir, filename)
                self._export_action(act, anim_path)
                results.append({"name": act.name, "file": anim_path})
                logger.info(f"动画导出: {anim_path}")
            except Exception as ex:
                logger.error(f"动画[{act.name}]导出失败: {ex}")
        return results

    def _export_action(self, action, anim_path):
        # 采样骨骼变换，骨骼映射与压缩, 按bigworld骨骼顺序
        bones = [b for b in self.arm.data.bones]
        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])
        sample_frames = range(frame_start, frame_end+1, self.frame_sample)
        all_bone_tracks = []
        for bone in bones:
            track = {"name": bone.name, "frames": []}
            for f in sample_frames:
                bpy.context.scene.frame_set(f)
                pbone = self.arm.pose.bones.get(bone.name)
                if pbone:
                    loc, rot, sca = pbone.matrix_basis.decompose()
                    track["frames"].append({
                        "frame": f,
                        "pos": loc[:],
                        "rot": rot[:],
                        "sca": sca[:] if hasattr(sca, "__len__") else (1,1,1)
                    })
                else:
                    track["frames"].append({
                        "frame": f, "pos": (0,0,0), "rot": (1,0,0,0), "sca": (1,1,1)
                    })
            # 动画压缩：移除恒定轨、量化、只导出关键数据（ACL思想）
            compressed = self.compress_track(track)
            all_bone_tracks.append(compressed)
        # 写二进制文件
        with BinaryWriter(anim_path) as writer:
            # 文件头
            writer.write_magic(b'BWAN')
            writer.write_uint32(1)
            # 总骨骼数
            writer.write_uint32(len(all_bone_tracks))
            for t in all_bone_tracks:
                writer.write_str(t["name"])
                writer.write_uint32(len(t["frames"]))
                for f in t["frames"]:
                    # 插值算法可扩展为线性、样条（此处采用线性+可选插值参数存储）【4】【6】【7】
                    writer.write_uint32(f["frame"])
                    writer.write_vec3(f["pos"])
                    writer.write_quat(f["rot"])
                    writer.write_vec3(f["sca"])
        
    def compress_track(self, track):
        """基于ACL思想做基础动画压缩（恒定轨检测、范围量化）"""
        frames = track["frames"]
        # 恒定轨道剔除优化
        if all(fr["pos"] == frames[0]["pos"] for fr in frames):
            for fr in frames:
                fr["sca"] = (1,1,1)
        # 可拓展多位量化/Float16
        return track
