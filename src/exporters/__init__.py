"""
导出模块。

包含数据导出功能。
"""

from src.exporters.excel import ExcelExporter

__all__ = ["ExcelExporter"]

# 本来设计了 src/exporters 模块来专门负责各种格式导出，实现单一职责原则（SRP）。
# 结果：功能在 database.py 里跑通了，就暂时没把逻辑拆分出去，导致 exporters 目录成了一个摆设。
# 处理：先保留着，后续如果需要导出其他格式的数据，再拆分出来。