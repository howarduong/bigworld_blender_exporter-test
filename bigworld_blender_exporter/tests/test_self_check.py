# 文件位置: bigworld_blender_exporter/tests/test_self_check.py
# 测试自动化自检脚本

import os
import unittest
from ..tools.self_check import run_self_check

class TestSelfCheck(unittest.TestCase):
    def setUp(self):
        self.export_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_exports'))
        os.makedirs(self.export_dir, exist_ok=True)
        # 创建假文件
        for ext in ['.model', '.visual', '.primitives', '.mfm']:
            with open(os.path.join(self.export_dir, 'test' + ext), 'w') as f:
                f.write('dummy')

    def tearDown(self):
        for fname in os.listdir(self.export_dir):
            os.remove(os.path.join(self.export_dir, fname))
        os.rmdir(self.export_dir)

    def test_level1(self):
        self.assertTrue(run_self_check(self.export_dir, level=1))

    def test_level2(self):
        self.assertTrue(run_self_check(self.export_dir, level=2))

    def test_level3(self):
        self.assertTrue(run_self_check(self.export_dir, level=3))

if __name__ == '__main__':
    unittest.main()
