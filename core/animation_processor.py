# 文件位置: bigworld_blender_exporter/core/animation_processor.py
# Animation data processing for BigWorld export

import bpy
from mathutils import Vector, Quaternion, Matrix
from ..utils import logger
from ..utils.math_utils import blender_to_bigworld_matrix
from .. import config

class AnimationProcessor:
    """
    Responsible for collecting and processing animation data.
    负责动画数据的收集与处理。
    """
    
    def __init__(self):
        self.frame_cache = {}
        self.bone_cache = {}

    def process(self, obj, action, settings):
        """Process animation data for export"""
        logger.info(f"Processing animation: {action.name} for object: {obj.name}")
        
        # Validate object has armature
        armature = obj.find_armature()
        if not armature:
            logger.error(f"No armature found for animated object: {obj.name}")
            return None
        
        # Get animation data
        animation_data = {
            'name': action.name,
            'frame_count': 0,
            'frame_rate': settings.frame_rate,
            'duration': 0.0,
            'bones': [],
            'keyframes': [],
            'loop': getattr(settings, 'loop_animation', False)
        }
        
        # Process bones
        bones_data = self._process_bones(armature)
        animation_data['bones'] = bones_data
        
        # Sample animation frames
        keyframes = self._sample_animation(obj, action, settings, armature)
        animation_data['keyframes'] = keyframes
        animation_data['frame_count'] = len(keyframes)
        
        # Calculate duration
        frame_range = settings.end_frame - settings.start_frame + 1
        animation_data['duration'] = frame_range / settings.frame_rate
        
        logger.info(f"Processed {len(keyframes)} keyframes for {len(bones_data)} bones")
        return animation_data

    def _process_bones(self, armature):
        """Process bone hierarchy for animation"""
        bones_data = []
        
        for bone in armature.data.bones:
            bone_data = {
                'name': bone.name,
                'parent': bone.parent.name if bone.parent else None,
                'index': len(bones_data),
                'head': list(bone.head_local),
                'tail': list(bone.tail_local),
                'length': bone.length
            }
            bones_data.append(bone_data)
        
        return bones_data

    def _sample_animation(self, obj, action, settings, armature):
        """Sample animation frames"""
        keyframes = []
        original_frame = bpy.context.scene.frame_current
        
        # Set action
        if obj.animation_data:
            obj.animation_data.action = action
        
        # Sample frames
        for frame in range(settings.start_frame, settings.end_frame + 1):
            bpy.context.scene.frame_set(frame)
            
            # Get bone transforms
            frame_data = {
                'frame': frame,
                'time': (frame - settings.start_frame) / settings.frame_rate,
                'bone_transforms': {}
            }
            
            # Sample each bone
            for bone in armature.pose.bones:
                transform_data = self._get_bone_transform(bone, settings)
                frame_data['bone_transforms'][bone.name] = transform_data
            
            keyframes.append(frame_data)
        
        # Restore original frame
        bpy.context.scene.frame_set(original_frame)
        
        # Optimize keyframes if requested
        if settings.optimize_keyframes:
            keyframes = self._optimize_keyframes(keyframes)
        
        return keyframes

    def _get_bone_transform(self, bone, settings):
        """Get bone transform data for current frame"""
        matrix = bone.matrix
        
        # Extract position, rotation, scale
        position = list(matrix.to_translation())
        rotation = list(matrix.to_quaternion())
        scale = list(matrix.to_scale())
        
        # Apply coordinate system transformation
        if settings.coordinate_system == 'Y_UP':
            transform_matrix = blender_to_bigworld_matrix()
            position = list(transform_matrix @ Vector(position))
            
            # Transform rotation
            rot_matrix = transform_matrix.to_3x3()
            rotation = list(Quaternion(rotation).to_matrix().to_quaternion())
        
        # Apply global scale
        if settings.global_scale != 1.0:
            position = [p * settings.global_scale for p in position]
        
        return {
            'position': position,
            'rotation': rotation,
            'scale': scale
        }

    def _optimize_keyframes(self, keyframes):
        """Optimize keyframes by removing redundant data"""
        if len(keyframes) < 3:
            return keyframes
        
        optimized = [keyframes[0]]  # Always keep first frame
        
        for i in range(1, len(keyframes) - 1):
            current = keyframes[i]
            previous = keyframes[i - 1]
            next_frame = keyframes[i + 1]
            
            # Check if current frame is significantly different
            if self._is_frame_significant(current, previous, next_frame):
                optimized.append(current)
        
        optimized.append(keyframes[-1])  # Always keep last frame
        
        logger.info(f"Optimized keyframes: {len(keyframes)} -> {len(optimized)}")
        return optimized

    def _is_frame_significant(self, current, previous, next_frame):
        """Check if current frame contains significant changes"""
        threshold = 0.001  # Position threshold
        rot_threshold = 0.01  # Rotation threshold
        
        for bone_name in current['bone_transforms']:
            if bone_name not in previous['bone_transforms'] or bone_name not in next_frame['bone_transforms']:
                return True
            
            current_transform = current['bone_transforms'][bone_name]
            prev_transform = previous['bone_transforms'][bone_name]
            next_transform = next_frame['bone_transforms'][bone_name]
            
            # Check position change
            pos_diff = Vector(current_transform['position']) - Vector(prev_transform['position'])
            if pos_diff.length > threshold:
                return True
            
            # Check rotation change
            current_rot = Quaternion(current_transform['rotation'])
            prev_rot = Quaternion(prev_transform['rotation'])
            rot_diff = current_rot.rotation_difference(prev_rot).angle
            if rot_diff > rot_threshold:
                return True
            
            # Check scale change
            scale_diff = Vector(current_transform['scale']) - Vector(prev_transform['scale'])
            if scale_diff.length > threshold:
                return True
        
        return False

    def export_animation_data(self, animation_data, filepath):
        """Export animation data to file"""
        from ..formats.animation_format import export_animation_file
        export_animation_file(filepath, animation_data)

def register():
    pass

def unregister():
    pass
