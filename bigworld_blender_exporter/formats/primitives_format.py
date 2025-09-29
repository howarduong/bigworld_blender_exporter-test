# -*- coding: utf-8 -*-
import io
import os
import struct
import time
from typing import List, Tuple


BINSECTION_MAGIC = 0x42A14E65  # Big-endian in file
# reserved_data layout (16 bytes, little-endian fields):
# preloadLen: uint32
# version:    uint32
# modified:   uint64


def _align4_len(length: int) -> int:
    """Return length padded to 4-byte alignment."""
    pad = (-length) & 3
    return length + pad


def _pad4(f: io.BufferedWriter, length_written: int) -> int:
    """Pad the file to 4-byte boundary based on the last write length, return total padded length."""
    pad = (-length_written) & 3
    if pad:
        f.write(b"\x00" * pad)
    return length_written + pad


def _write_magic(f: io.BufferedWriter):
    # BinSection magic is stored big-endian
    f.write(struct.pack(">I", BINSECTION_MAGIC))


def _u32le(value: int) -> bytes:
    return struct.pack("<I", value)


def _u64le(value: int) -> bytes:
    return struct.pack("<Q", value)


class PrimitiveSection:
    """A single section (vertices / indices) to be embedded in .primitives."""

    def __init__(self, tag: str, data: bytes, preload_len: int = 0, version: int = 1, modified_ts: int = None):
        self.tag = tag  # e.g., "MyModel.vertices" or "MyModel.indices"
        self.data = data or b""
        self.preload_len = int(preload_len)
        self.version = int(version)
        self.modified_ts = int(modified_ts if modified_ts is not None else int(time.time()))

        # These will be populated after writing the blob
        self.blob_len_padded = 0  # includes padding
        self._tag_bytes = self.tag.encode("ascii")


def write_primitives_file(
    filepath: str,
    base_name: str,
    vertices_bytes: bytes,
    indices_bytes: bytes,
    *,
    vertices_version: int = 1,
    indices_version: int = 1,
    preload_vertices: int = 0,
    preload_indices: int = 0,
    modified_ts: int = None,
) -> None:
    """
    Write a .primitives file in BinSection format with two sections:
    - "{base_name}.vertices"
    - "{base_name}.indices"

    Parameters:
        filepath: Output .primitives path (e.g., ".../MyModel.primitives")
        base_name: Label base (e.g., "MyModel")
        vertices_bytes: Serialized vertex buffer bytes (already packed per engine vertex layout)
        indices_bytes: Serialized index buffer bytes (uint16/uint32 contiguous data)
        vertices_version / indices_version: Version integers for each section
        preload_vertices / preload_indices: Optional preload lengths
        modified_ts: Unix timestamp for 'modified' field (default: current time)
    """
    # Prepare two sections
    sections: List[PrimitiveSection] = [
        PrimitiveSection(
            tag=f"{base_name}.vertices",
            data=vertices_bytes,
            preload_len=preload_vertices,
            version=vertices_version,
            modified_ts=modified_ts,
        ),
        PrimitiveSection(
            tag=f"{base_name}.indices",
            data=indices_bytes,
            preload_len=preload_indices,
            version=indices_version,
            modified_ts=modified_ts,
        ),
    ]

    # Write BinSection
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        # 1) Magic (big-endian)
        _write_magic(f)

        # 2) Write all binary blobs (each padded to 4-byte boundary)
        for sec in sections:
            f.write(sec.data)
            written = len(sec.data)
            sec.blob_len_padded = _pad4(f, written)

        # 3) Build and write index table (little-endian fields)
        index_table_buf = io.BytesIO()

        for sec in sections:
            # blob_length (including padding)
            index_table_buf.write(_u32le(sec.blob_len_padded))

            # reserved_data (16 bytes)
            index_table_buf.write(_u32le(sec.preload_len))   # preloadLen
            index_table_buf.write(_u32le(sec.version))       # version
            index_table_buf.write(_u64le(sec.modified_ts))   # modified (unix timestamp)

            # tag_length + tag_value (4-byte aligned)
            tag_len = len(sec._tag_bytes)
            index_table_buf.write(_u32le(tag_len))
            index_table_buf.write(sec._tag_bytes)
            # pad tag to 4-byte alignment
            pad = (-tag_len) & 3
            if pad:
                index_table_buf.write(b"\x00" * pad)

        index_table_bytes = index_table_buf.getvalue()

        # Write index_table
        f.write(index_table_bytes)

        # 4) Write index_table_length (uint32, little-endian)
        f.write(_u32le(len(index_table_bytes)))


# Convenience helpers for serializer integration
def serialize_vertices(mesh) -> bytes:
    """
    Serialize Blender mesh vertices into engine-expected layout.
    This function is a placeholder – implement per project’s vertex declaration.
    Typical layout may include:
      position (float32 * 3),
      normal (float32 * 3),
      tangent (float32 * 4),
      uv0 (float32 * 2),
      uv1 (float32 * 2),
      color (float32 * 4),
      skin indices/weights, etc.
    Ensure contiguous packing and 4-byte alignment naturally via field sizes.
    """
    # TODO: Implement per your pipeline. The following is an example stub.
    # Example for position-only layout:
    # buf = io.BytesIO()
    # for v in mesh.vertices:
    #     buf.write(struct.pack("<3f", v.co.x, v.co.y, v.co.z))
    # return buf.getvalue()
    raise NotImplementedError("serialize_vertices(mesh) must be implemented for your vertex layout.")


def serialize_indices(mesh) -> bytes:
    """
    Serialize Blender mesh polygon indices (tri-list) as uint32 or uint16.
    Ensure the format matches engine expectation (usually tri-list).
    """
    # TODO: Implement per your pipeline. The following is an example stub.
    # buf = io.BytesIO()
    # for poly in mesh.polygons:
    #     # Assuming triangles; if quads, triangulate first
    #     i0, i1, i2 = poly.vertices[0], poly.vertices[1], poly.vertices[2]
    #     buf.write(struct.pack("<III", i0, i1, i2))  # uint32
    # return buf.getvalue()
    raise NotImplementedError("serialize_indices(mesh) must be implemented for your index format.")


def export_primitives_for_object(res_root: str, models_dir_rel: str, base_name: str, mesh) -> str:
    """
    High-level helper: serialize mesh → write .primitives in models/ directory.
    Returns the res-relative path of the generated .primitives file.

    Parameters:
        res_root: absolute path to res/ root
        models_dir_rel: res-relative models subdir (e.g., "models/props/chair")
        base_name: model base name (e.g., "Chair")
        mesh: Blender mesh object

    Example:
        export_primitives_for_object(
            res_root="D:/Project/res",
            models_dir_rel="models/props/chair",
            base_name="chair",
            mesh=bpy.data.objects["ChairMesh"].data
        )
    """
    # Serialize
    vbytes = serialize_vertices(mesh)
    ibytes = serialize_indices(mesh)

    # Resolve output path
    out_dir_abs = os.path.join(res_root, models_dir_rel).replace("\\", "/")
    os.makedirs(out_dir_abs, exist_ok=True)
    out_path_abs = os.path.join(out_dir_abs, f"{base_name}.primitives").replace("\\", "/")

    # Write primitives
    write_primitives_file(
        filepath=out_path_abs,
        base_name=base_name,
        vertices_bytes=vbytes,
        indices_bytes=ibytes,
    )

    # Return res-relative path
    return f"{models_dir_rel}/{base_name}.primitives".replace("\\", "/")
