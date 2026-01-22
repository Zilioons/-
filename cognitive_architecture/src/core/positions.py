"""
位置索引系统
基于字符位置索引的文档操作
"""

import os
from typing import Optional, Tuple, List
from pathlib import Path

from .constants import SpecialChars

class PositionManager:
    """位置管理器"""
    
    @staticmethod
    def read_from_position(document_path: str, position: int, length: int = None) -> Optional[str]:
        """
        从指定位置读取文档内容
        """
        try:
            if not os.path.exists(document_path):
                return None
            
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证位置
            if position < 0 or position > len(content):
                return None
            
            # 读取指定长度的内容或到文件末尾
            if length is not None:
                end_pos = min(position + length, len(content))
            else:
                end_pos = len(content)
            
            return content[position:end_pos]
            
        except Exception as e:
            print(f"从位置读取文档失败: {e}")
            return None
    
    @staticmethod
    def insert_at_position(document_path: str, position: int, text: str) -> bool:
        """
        在指定位置插入文本
        """
        try:
            if not os.path.exists(document_path):
                return False
            
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证位置
            if position < 0 or position > len(content):
                return False
            
            # 插入文本
            new_content = content[:position] + text + content[position:]
            
            # 写回文件
            with open(document_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
            
        except Exception as e:
            print(f"在位置插入文本失败: {e}")
            return False
    
    @staticmethod
    def delete_range(document_path: str, start: int, end: int) -> Tuple[bool, Optional[str]]:
        """
        删除指定范围的文本
        返回: (成功标志, 删除的内容)
        """
        try:
            if not os.path.exists(document_path):
                return False, None
            
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证位置
            if start < 0 or end > len(content) or start > end:
                return False, None
            
            # 提取要删除的内容
            deleted_content = content[start:end]
            
            # 删除指定范围
            new_content = content[:start] + content[end:]
            
            # 写回文件
            with open(document_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True, deleted_content
            
        except Exception as e:
            print(f"删除范围失败: {e}")
            return False, None
    
    @staticmethod
    def copy_range(document_path: str, start: int, end: int) -> Optional[str]:
        """
        复制指定范围的文本
        """
        try:
            if not os.path.exists(document_path):
                return None
            
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证位置
            if start < 0 or end > len(content) or start > end:
                return None
            
            return content[start:end]
            
        except Exception as e:
            print(f"复制范围失败: {e}")
            return None
    
    @staticmethod
    def find_position_by_content(document_path: str, content: str, start_position: int = 0) -> List[int]:
        """
        在文档中查找内容的所有位置
        返回字符位置列表
        """
        try:
            if not os.path.exists(document_path):
                return []
            
            with open(document_path, 'r', encoding='utf-8') as f:
                document_content = f.read()
            
            positions = []
            pos = document_content.find(content, start_position)
            
            while pos != -1:
                positions.append(pos)
                pos = document_content.find(content, pos + 1)
            
            return positions
            
        except Exception as e:
            print(f"查找内容位置失败: {e}")
            return []