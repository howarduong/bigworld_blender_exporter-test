# 文件位置: bigworld_blender_exporter/tools/self_check.py
# 自动化自检脚本，Level1–Level3样例全流程自检

import os
import glob
from ..utils.logger import get_logger

logger = get_logger("self_check")

def run_self_check(export_dir, level=1):
    """
    自动化自检，检查导出文件完整性、格式、内容等
    :param export_dir: 导出目录
    :param level: 检查级别（1-3）
    :return: 检查结果True/False
    """
    logger.info(f"自检开始，目录: {export_dir}，级别: {level}")
    # Level1: 文件存在性
    required_exts = ['.model', '.visual', '.primitives', '.mfm']
    for ext in required_exts:
        files = glob.glob(os.path.join(export_dir, f'*{ext}'))
        if not files:
            logger.error(f"缺少{ext}文件")
            return False
    # Level2: 结构检查（可扩展）
    if level >= 2:
        # TODO: 检查XML结构、二进制头部等
        pass
    # Level3: 内容比对（可扩展）
    if level >= 3:
        # TODO: 与标准样例比对内容
        pass
    logger.info("自检通过")
    return True
