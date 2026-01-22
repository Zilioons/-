"""
标准格式转换系统
处理光标格式、路径格式等标准化转换
"""

import os
import re
from typing import Dict, Optional, Tuple, List
from pathlib import Path

from .constants import CursorDirection, SpecialChars, PROJECT_ROOT

class FormatConverter:
    """格式转换器"""
    
    @staticmethod
    def parse_cursor_format(cursor_text: str) -> Optional[Dict]:
        """
        解析标准光标格式
        格式: DOCUMENT:路径 SPACE_INDEX:位置 DIRECTION:方向
        
        返回: {
            "document": 文档路径,
            "position": 字符位置,
            "direction": 方向
        }
        """
        try:
            # 按空格分割为三部分
            parts = cursor_text.strip().split()
            if len(parts) != 3:
                return None
            
            # 解析第一部分: 文档路径
            doc_part = parts[0]
            if not doc_part.startswith("DOCUMENT:"):
                return None
            document_path = doc_part[9:]  # 去掉"DOCUMENT:"
            
            # 转换为绝对路径
            if not os.path.isabs(document_path):
                # 假设路径相对于项目根目录
                document_path = str(PROJECT_ROOT / document_path)
            
            # 解析第二部分: 位置
            pos_part = parts[1]
            if not pos_part.startswith("SPACE_INDEX:"):
                return None
            try:
                position = int(pos_part[12:])  # 去掉"SPACE_INDEX:"
            except ValueError:
                return None
            
            # 解析第三部分: 方向
            dir_part = parts[2]
            if not dir_part.startswith("DIRECTION:"):
                return None
            direction = dir_part[10:]  # 去掉"DIRECTION:"
            if direction not in [CursorDirection.LEFT, CursorDirection.RIGHT]:
                return None
            
            return {
                "document": document_path,
                "position": position,
                "direction": direction
            }
            
        except Exception as e:
            print(f"解析光标格式时出错: {e}")
            return None
    
    @staticmethod
    def create_cursor_format(document: str, position: int, direction: str) -> str:
        """
        创建标准光标格式字符串
        """
        return f"DOCUMENT:{document} SPACE_INDEX:{position} DIRECTION:{direction}"
    
    @staticmethod
    def parse_path_format(path_text: str) -> str:
        """
        将标准路径格式转换为系统路径
        """
        # 如果已经是绝对路径，直接返回
        if os.path.isabs(path_text):
            return path_text
        
        # 否则，假设是相对于文档目录的路径
        documents_dir = PROJECT_ROOT / "documents"
        full_path = documents_dir / path_text
        
        return str(full_path)
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        规范化路径
        """
        return os.path.normpath(path)
    
    @staticmethod
    def parse_search_target(target: str) -> str:
        """
        解析搜索目标，将特殊符号转换为内部表示
        注意：这里只做简单转换，实际匹配由搜索器实现
        """
        return target  # 保持原样，搜索器会处理特殊字符
    
    @staticmethod
    def validate_output_path(path: str) -> bool:
        """
        验证输出路径是否有效
        """
        try:
            # 检查父目录是否存在或可创建
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # 尝试写入一个测试文件（然后删除）
            test_file = path + ".test"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            return True
        except Exception as e:
            print(f"输出路径验证失败: {e}")
            return False