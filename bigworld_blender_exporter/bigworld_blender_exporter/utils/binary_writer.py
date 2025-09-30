# bigworld_blender_exporter/utils/binary_writer.py

import struct

class BinaryWriter:
    """通用二进制写入工具，支持大/小端，适配BigWorld模型动画二进制文件写入。"""
    def __init__(self, path, mode='wb', endian='<'):
        self.fp = open(path, mode)
        self.endian = endian

    def write_magic(self, magic: bytes):
        self.fp.write(magic)

    def write_uint32(self, val):
        self.fp.write(struct.pack(f'{self.endian}I', val))

    def write_uint16(self, val):
        self.fp.write(struct.pack(f'{self.endian}H', val))

    def write_float(self, val):
        self.fp.write(struct.pack(f'{self.endian}f', val))

    def write_vec2(self, v):
        self.fp.write(struct.pack(f'{self.endian}2f', *v))

    def write_vec3(self, v):
        self.fp.write(struct.pack(f'{self.endian}3f', *v))

    def write_vec4(self, v):
        self.fp.write(struct.pack(f'{self.endian}4f', *v))

    def write_quat(self, q):
        self.fp.write(struct.pack(f'{self.endian}4f', *q))

    def write_str(self, s):
        s = s or ""
        bs = s.encode("utf-8")
        self.write_uint16(len(bs))
        self.fp.write(bs)

    def write_block(self, block_tag, write_func):
        # 块式写入（Tag+长度+内容），BigWorld二进制文件结构常用
        self.write_str(block_tag)
        import io
        buf = io.BytesIO()
        sub_writer = type(self)(buf, endian=self.endian)
        write_func(sub_writer)
        sub_bytes = buf.getvalue()
        self.write_uint32(len(sub_bytes))
        self.fp.write(sub_bytes)

    def finalize(self):
        # 若有额外尾部处理可覆盖
        self.fp.flush()

    def close(self):
        self.fp.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
