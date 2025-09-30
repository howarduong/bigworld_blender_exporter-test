# 文件位置: bigworld_blender_exporter/formats/primitives_format.py
# Primitives file format for BigWorld export

import struct
from ..config import PRIMITIVES_MAGIC, VERTEX_FORMATS
from ..utils.binary_writer import write_uint32, write_bytes, create_directory
from ..utils.logger import get_logger

logger = get_logger("primitives_format")

def export_primitives_file(filepath, vertices, indices, vertex_format='STANDARD'):
    """Export vertex and index data to BigWorld .primitives file"""
    logger.info(f"Exporting primitives file: {filepath}")
    
    # Create directory if it doesn't exist
    create_directory(filepath)
    
    # Determine vertex size from packing to avoid header mismatch
    vertex_size = 0
    if vertices:
        vertex_size = len(pack_vertex_data(vertices[0], vertex_format))
    
    with open(filepath, 'wb') as f:
        # Write header (using computed vertex_size)
        write_primitives_header(f, vertices, indices, vertex_size, vertex_format)
        
        # Write vertex data
        write_vertex_buffer(f, vertices, vertex_format)
        
        # Write index data
        write_index_buffer(f, indices)

def write_primitives_header(f, vertices, indices, vertex_size, vertex_format):
    """Write primitives file header"""
    # Magic number
    write_uint32(f, PRIMITIVES_MAGIC)
    
    # Format string (64 bytes, null-padded)
    fmt_str = VERTEX_FORMATS[vertex_format]['format'].encode('ascii').ljust(64, b'\0')
    write_bytes(f, fmt_str)
    
    # Vertex count
    write_uint32(f, len(vertices))
    
    # Index count
    write_uint32(f, len(indices))
    
    # Vertex size in bytes
    write_uint32(f, vertex_size)
    
    # Padding to align to 16-byte boundary
    f.write(b'\0' * 4)

def write_vertex_buffer(f, vertices, vertex_format):
    """Write vertex buffer data"""
    logger.info(f"Writing {len(vertices)} vertices in {vertex_format} format")
    
    for vertex in vertices:
        # Pack vertex data according to format
        packed_vertex = pack_vertex_data(vertex, vertex_format)
        write_bytes(f, packed_vertex)

def write_index_buffer(f, indices):
    """Write index buffer data"""
    logger.info(f"Writing {len(indices)} indices")
    
    for index in indices:
        # Write as 16-bit unsigned integer
        f.write(struct.pack('<H', index))

def pack_vertex_data(vertex_data, format_type='STANDARD'):
    """Pack vertex data according to BigWorld format"""
    if format_type == 'SIMPLE':
        return pack_simple_vertex(vertex_data)
    elif format_type == 'SKINNED':
        return pack_skinned_vertex(vertex_data)
    else:  # STANDARD
        return pack_standard_vertex(vertex_data)

def pack_simple_vertex(vertex_data):
    """Pack simple vertex format: xyznuv"""
    data = bytearray()
    
    # Position (x, y, z) - 3 * float32
    pos = vertex_data['position']
    data.extend(struct.pack('<fff', pos[0], pos[1], pos[2]))
    
    # Normal (n) - short2 (compressed)
    from ..utils.math_utils import compress_normal
    normal = compress_normal(vertex_data['normal'])
    data.extend(normal)
    
    # UV (u, v) - 2 * float32
    uv = vertex_data['uv']
    data.extend(struct.pack('<ff', uv[0], uv[1]))
    
    return bytes(data)

def pack_skinned_vertex(vertex_data):
    """Pack skinned vertex format: xyznuviiiww"""
    data = bytearray()
    
    # Position (x, y, z) - 3 * float32
    pos = vertex_data['position']
    data.extend(struct.pack('<fff', pos[0], pos[1], pos[2]))
    
    # Normal (n) - short2 (compressed)
    from ..utils.math_utils import compress_normal
    normal = compress_normal(vertex_data['normal'])
    data.extend(normal)
    
    # UV (u, v) - 2 * float32
    uv = vertex_data['uv']
    data.extend(struct.pack('<ff', uv[0], uv[1]))
    
    # Bone indices (i, i, i) - 3 * uint8
    bone_indices = vertex_data['bone_indices']
    data.extend(struct.pack('<BBB', bone_indices[0], bone_indices[1], bone_indices[2]))
    
    # Bone weights (w, w) - 2 * uint8 (third weight calculated)
    bone_weights = vertex_data['bone_weights']
    w1 = int(bone_weights[0] * 255)
    w2 = int(bone_weights[1] * 255)
    data.extend(struct.pack('<BB', w1, w2))
    
    return bytes(data)

def pack_standard_vertex(vertex_data):
    """Pack standard vertex format: xyznuviiiwwtb"""
    data = bytearray()
    
    # Position (x, y, z) - 3 * float32
    pos = vertex_data['position']
    data.extend(struct.pack('<fff', pos[0], pos[1], pos[2]))
    
    # Normal (n) - short2 (compressed)
    from ..utils.math_utils import compress_normal, compress_tangent, compress_binormal
    normal = compress_normal(vertex_data['normal'])
    data.extend(normal)
    
    # UV (u, v) - 2 * float32
    uv = vertex_data['uv']
    data.extend(struct.pack('<ff', uv[0], uv[1]))
    
    # Bone indices (i, i, i) - 3 * uint8
    bone_indices = vertex_data['bone_indices']
    data.extend(struct.pack('<BBB', bone_indices[0], bone_indices[1], bone_indices[2]))
    
    # Bone weights (w, w) - 2 * uint8
    bone_weights = vertex_data['bone_weights']
    w1 = int(bone_weights[0] * 255)
    w2 = int(bone_weights[1] * 255)
    data.extend(struct.pack('<BB', w1, w2))
    
    # Tangent (t) - short2 (compressed)
    tangent = compress_tangent(vertex_data['tangent'])
    data.extend(tangent)
    
    # Binormal (b) - short2 (compressed)
    binormal = compress_binormal(vertex_data['binormal'])
    data.extend(binormal)
    
    return bytes(data)
