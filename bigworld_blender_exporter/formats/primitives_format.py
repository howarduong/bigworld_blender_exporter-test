# 文件位置: bigworld_blender_exporter/formats/primitives_format.py
# Primitives file format for BigWorld export

import os
import struct
from ..config import PRIMITIVES_MAGIC, VERTEX_FORMATS
from ..utils.binary_writer import write_uint32, write_bytes, create_directory
from ..utils.logger import get_logger
from ..utils.math_utils import compress_normal, compress_tangent, compress_binormal

logger = get_logger("primitives_format")


def export_primitives_file(filepath, vertices, indices, vertex_format='STANDARD'):
    """
    Export vertex and index data to BigWorld .primitives file
    """
    try:
        logger.info(f"Exporting primitives file: {filepath}")
        create_directory(filepath)

        # Determine vertex size from packing
        vertex_size = 0
        if vertices:
            vertex_size = len(pack_vertex_data(vertices[0], vertex_format))

        with open(filepath, 'wb') as f:
            # Header
            write_primitives_header(f, vertices, indices, vertex_size, vertex_format)
            # Vertex buffer
            write_vertex_buffer(f, vertices, vertex_format)
            # Index buffer
            write_index_buffer(f, indices, len(vertices))

        logger.info(f"Primitives file written: {filepath} "
                    f"({len(vertices)} vertices, {len(indices)} indices, format={vertex_format})")
    except Exception as e:
        logger.error(f"Failed to export primitives file {filepath}: {str(e)}")
        raise


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
        packed = pack_vertex_data(vertex, vertex_format)
        write_bytes(f, packed)


def write_index_buffer(f, indices, vertex_count):
    """Write index buffer data"""
    logger.info(f"Writing {len(indices)} indices")
    use_32bit = vertex_count > 65535
    for index in indices:
        if use_32bit:
            f.write(struct.pack('<I', index))
        else:
            f.write(struct.pack('<H', index))


def pack_vertex_data(vertex_data, format_type='STANDARD'):
    """Pack vertex data according to BigWorld format"""
    if format_type == 'SIMPLE':
        return pack_simple_vertex(vertex_data)
    elif format_type == 'SKINNED':
        return pack_skinned_vertex(vertex_data)
    else:
        return pack_standard_vertex(vertex_data)


def pack_simple_vertex(v):
    """Pack simple vertex format: xyznuv"""
    data = bytearray()
    # Position
    pos = v['position']
    data.extend(struct.pack('<fff', *pos))
    # Normal (compressed short2)
    data.extend(compress_normal(v['normal']))
    # UV
    uv = v['uv']
    data.extend(struct.pack('<ff', *uv))
    return bytes(data)


def pack_skinned_vertex(v):
    """Pack skinned vertex format: xyznuviiiww"""
    data = bytearray()
    pos = v['position']
    data.extend(struct.pack('<fff', *pos))
    data.extend(compress_normal(v['normal']))
    uv = v['uv']
    data.extend(struct.pack('<ff', *uv))
    # Bone indices
    bi = v.get('bone_indices', [0, 0, 0])
    data.extend(struct.pack('<BBB', *bi))
    # Bone weights
    bw = v.get('bone_weights', [1.0, 0.0])
    w1 = int(bw[0] * 255)
    w2 = int(bw[1] * 255)
    data.extend(struct.pack('<BB', w1, w2))
    return bytes(data)


def pack_standard_vertex(v):
    """Pack standard vertex format: xyznuviiiwwtb"""
    data = bytearray()
    pos = v['position']
    data.extend(struct.pack('<fff', *pos))
    data.extend(compress_normal(v['normal']))
    uv = v['uv']
    data.extend(struct.pack('<ff', *uv))
    bi = v.get('bone_indices', [0, 0, 0])
    data.extend(struct.pack('<BBB', *bi))
    bw = v.get('bone_weights', [1.0, 0.0])
    w1 = int(bw[0] * 255)
    w2 = int(bw[1] * 255)
    data.extend(struct.pack('<BB', w1, w2))
    data.extend(compress_tangent(v['tangent']))
    data.extend(compress_binormal(v['binormal']))
    return bytes(data)
