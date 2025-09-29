# 文件位置: bigworld_blender_exporter/formats/primitives_format.py
# Primitives file format for BigWorld export (改进版)

import os
import struct
from ..config import PRIMITIVES_MAGIC, VERTEX_FORMATS
from ..utils.binary_writer import write_uint32, write_bytes, create_directory
from ..utils.logger import get_logger
from ..utils.math_utils import compress_normal, compress_tangent, compress_binormal

logger = get_logger("primitives_format")


def _normalize_vertex(v):
    """兼容 tuple/list/dict 顶点，统一转成 dict"""
    if isinstance(v, dict):
        return v
    elif isinstance(v, (list, tuple)):
        x = float(v[0]) if len(v) > 0 else 0.0
        y = float(v[1]) if len(v) > 1 else 0.0
        z = float(v[2]) if len(v) > 2 else 0.0
        return {
            "position": (x, y, z),
            "normal": (0.0, 0.0, 1.0),
            "uv": (0.0, 0.0),
            "bone_indices": [0, 0, 0],
            "bone_weights": [1.0, 0.0],
            "tangent": (1.0, 0.0, 0.0),
            "binormal": (0.0, 1.0, 0.0),
        }
    else:
        raise TypeError(f"Unsupported vertex type: {type(v)}")


def export_primitives_file(filepath, vertices, indices, vertex_format='STANDARD'):
    """Export vertex and index data to BigWorld .primitives file"""
    try:
        logger.info(f"Exporting primitives file: {filepath}")
        create_directory(filepath)

        # Normalize vertices
        vertices = [_normalize_vertex(v) for v in vertices]

        # Determine vertex size
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
    write_uint32(f, PRIMITIVES_MAGIC)
    fmt_str = VERTEX_FORMATS[vertex_format]['format'].encode('ascii').ljust(64, b'\0')
    write_bytes(f, fmt_str)
    write_uint32(f, len(vertices))
    write_uint32(f, len(indices))
    write_uint32(f, vertex_size)
    f.write(b'\0' * 4)


def write_vertex_buffer(f, vertices, vertex_format):
    logger.info(f"Writing {len(vertices)} vertices in {vertex_format} format")
    for vertex in vertices:
        packed = pack_vertex_data(vertex, vertex_format)
        write_bytes(f, packed)


def write_index_buffer(f, indices, vertex_count):
    logger.info(f"Writing {len(indices)} indices")
    use_32bit = vertex_count > 65535
    for index in indices:
        if use_32bit:
            f.write(struct.pack('<I', index))
        else:
            f.write(struct.pack('<H', index))


def pack_vertex_data(vertex_data, format_type='STANDARD'):
    if format_type == 'SIMPLE':
        return pack_simple_vertex(vertex_data)
    elif format_type == 'SKINNED':
        return pack_skinned_vertex(vertex_data)
    else:
        return pack_standard_vertex(vertex_data)


def pack_simple_vertex(v):
    data = bytearray()
    pos = v['position']
    data.extend(struct.pack('<fff', *pos))
    data.extend(compress_normal(v['normal']))
    uv = v['uv']
    data.extend(struct.pack('<ff', *uv))
    return bytes(data)


def pack_skinned_vertex(v):
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
    return bytes(data)


def pack_standard_vertex(v):
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
