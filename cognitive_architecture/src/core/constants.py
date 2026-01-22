"""
系统常量定义
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 特殊字符定义
class SpecialChars:
    """搜索特殊字符定义"""
    SPACE = '^'      # 表示空格字符
    ANY = '&'        # 表示任意单个字符
    
# 搜索方向
class SearchDirection:
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    
# 光标方向
class CursorDirection:
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    
# 指令类型
class InstructionType:
    COPY = "COPY"
    DELETE = "DELETE"
    SEARCH = "SEARCH"
    SEARCH_IN = "SEARCH_IN"
    LOCAL_SEARCH = "LOCAL_SEARCH"
    CREATE_FILE = "CREATE_FILE"
    CREATE_FOLDER = "CREATE_FOLDER"
    GENERATE = "GENERATE"
    
# 分隔符
class Separators:
    INSTRUCTION = ';'           # 指令分隔符
    CONTINUOUS = ';;'          # 连续分隔符
    PARAMETER = ' '            # 参数分隔符
    
# 文件扩展名
class FileExtensions:
    TEXT = ".txt"
    TRIGGER = ".txt"
    CURSOR = ".txt"
    RESULT = ".txt"
    
# 错误消息
class ErrorMessages:
    FILE_NOT_FOUND = "文件不存在"
    INVALID_FORMAT = "格式无效"
    INVALID_POSITION = "位置无效"
    SEARCH_TIMEOUT = "搜索超时"
    INSUFFICIENT_PARAMS = "参数不足"
    UNKNOWN_INSTRUCTION = "未知指令"