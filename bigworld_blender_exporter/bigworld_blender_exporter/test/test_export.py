# bigworld_blender_exporter/test/test_export.py

import unittest
import tempfile
import os
import bpy

from bigworld_blender_exporter.export.model_exporter import ModelExporter

class TestModelExport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="bwexport_")
        # 保证有至少一个Mesh对象
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
        self.obj = bpy.context.active_object

    def test_export_model(self):
        exporter = ModelExporter(self.obj, self.temp_dir, self.temp_dir)
        path = exporter.export()
        self.assertTrue(os.path.exists(path), "模型文件应成功导出")

    def tearDown(self):
        import shutil; shutil.rmtree(self.temp_dir)

if __name__ == "__main__":
    unittest.main()
