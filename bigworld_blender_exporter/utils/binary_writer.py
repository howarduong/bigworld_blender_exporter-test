import struct
import os

def write_uint32(f, value):
    f.write(struct.pack('<I', value))

def write_float32(f, value):
    f.write(struct.pack('<f', value))

def write_float3(f, x, y, z):
    """Write three 32-bit floats (x, y, z)."""
    f.write(struct.pack('<fff', x, y, z))

def write_float4(f, w, x, y, z):
    """Write four 32-bit floats (w, x, y, z)."""
    f.write(struct.pack('<ffff', w, x, y, z))

def write_short2(f, u, v):
    f.write(struct.pack('<HH', u, v))

def write_bytes(f, data):
    f.write(data)

def create_directory(filepath: str):
    """Create parent directory of filepath if not exists."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
