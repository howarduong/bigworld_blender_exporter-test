# bigworld_blender_exporter/utils/logger.py

import logging
import os

class Logger:
    def __init__(self):
        self.logger = logging.getLogger("bigworld_blender_exporter")
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            # 控制台输出
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter("[BigWorldExport][%(levelname)s] %(message)s")
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            # 文件log
            file_name = os.path.join(os.path.expanduser("~"), "bigworld_export.log")
            fh = logging.FileHandler(file_name, encoding='utf-8')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def info(self, msg): self.logger.info(str(msg))
    def warn(self, msg): self.logger.warning(str(msg))
    def error(self, msg): self.logger.error(str(msg))
    def debug(self, msg): self.logger.debug(str(msg))

logger = Logger()
