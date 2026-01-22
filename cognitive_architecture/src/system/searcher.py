"""
搜索系统
实现全局搜索、精准搜索和局部搜索
"""

import os
import time
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ..core.constants import (
    SpecialChars, SearchDirection, ErrorMessages,
    PROJECT_ROOT
)
from ..core.formats import FormatConverter
from ..core.positions import PositionManager

class Searcher:
    """搜索器"""
    
    def __init__(self):
        self.format_converter = FormatConverter()
        self.position_manager = PositionManager()
        
    def search(self, search_target: str, max_time_ms: int = 5000) -> List[Dict]:
        """
        全局搜索
        
        Args:
            search_target: 搜索目标，可包含^和&
            max_time_ms: 最大搜索时间（毫秒）
            
        Returns:
            匹配位置列表，每个位置是标准光标格式
        """
        start_time = time.time()
        results = []
        
        # 获取所有文档
        documents_dir = PROJECT_ROOT / "documents"
        documents = self._get_all_documents(documents_dir)
        
        for doc_path in documents:
            # 检查超时
            if (time.time() - start_time) * 1000 > max_time_ms:
                break
            
            # 搜索当前文档
            matches = self._search_in_document(str(doc_path), search_target)
            
            for pos in matches:
                cursor_format = self.format_converter.create_cursor_format(
                    str(doc_path), pos, SearchDirection.RIGHT
                )
                results.append(cursor_format)
        
        return results
    
    def search_in(self, cursor_data: Dict, search_target: str, max_time_ms: int) -> List[Dict]:
        """
        精准搜索
        
        Args:
            cursor_data: 光标数据，定义搜索范围
            search_target: 搜索目标
            max_time_ms: 最大搜索时间
            
        Returns:
            匹配位置列表
        """
        start_time = time.time()
        results = []
        
        document_path = cursor_data["document"]
        start_position = cursor_data["position"]
        
        if not os.path.exists(document_path):
            return results
        
        # 读取文档内容
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确定搜索范围
        search_range = content[start_position:]
        
        # 在范围内搜索
        pos = self._find_match(search_range, search_target, 0)
        
        while pos != -1:
            # 检查超时
            if (time.time() - start_time) * 1000 > max_time_ms:
                break
            
            # 计算在全文中的位置
            global_pos = start_position + pos
            
            cursor_format = self.format_converter.create_cursor_format(
                document_path, global_pos, SearchDirection.RIGHT
            )
            results.append(cursor_format)
            
            # 继续搜索
            pos = self._find_match(search_range, search_target, pos + 1)
        
        return results
    
    def local_search(self, base_cursor: Dict, direction: str, count: int, search_target: str) -> Optional[Dict]:
        """
        局部搜索
        
        Args:
            base_cursor: 基准光标
            direction: 搜索方向 (LEFT/RIGHT)
            count: 查找第几个匹配
            search_target: 搜索目标
            
        Returns:
            匹配位置的光标数据，或None
        """
        document_path = base_cursor["document"]
        base_position = base_cursor["position"]
        
        if not os.path.exists(document_path):
            return None
        
        # 读取文档内容
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if direction == SearchDirection.RIGHT:
            # 向右搜索
            search_range = content[base_position:]
            matches = self._find_all_matches(search_range, search_target)
            
            if len(matches) >= count:
                match_pos = matches[count - 1]  # 第count个匹配
                global_pos = base_position + match_pos
                
                return {
                    "document": document_path,
                    "position": global_pos,
                    "direction": SearchDirection.RIGHT
                }
                
        else:  # LEFT方向
            # 向左搜索
            left_content = content[:base_position]
            
            # 反转内容和搜索目标进行搜索
            reversed_content = left_content[::-1]
            reversed_target = search_target[::-1]
            
            matches = self._find_all_matches(reversed_content, reversed_target)
            
            if len(matches) >= count:
                match_pos = matches[count - 1]  # 第count个匹配
                # 计算在原文中的位置
                global_pos = base_position - match_pos - len(search_target)
                
                return {
                    "document": document_path,
                    "position": global_pos,
                    "direction": SearchDirection.LEFT
                }
        
        return None
    
    def _get_all_documents(self, directory: Path) -> List[Path]:
        """获取目录下的所有文档"""
        documents = []
        
        if directory.exists():
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".txt"):
                        documents.append(Path(root) / file)
        
        return documents
    
    def _search_in_document(self, document_path: str, search_target: str) -> List[int]:
        """
        在单个文档中搜索
        
        Returns:
            匹配开始位置列表
        """
        if not os.path.exists(document_path):
            return []
        
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self._find_all_matches(content, search_target)
    
    def _find_all_matches(self, text: str, pattern: str) -> List[int]:
        """
        在文本中查找所有匹配位置
        
        Args:
            text: 要搜索的文本
            pattern: 搜索模式，可包含^和&
            
        Returns:
            匹配开始位置列表
        """
        matches = []
        pos = 0
        
        while pos < len(text):
            match_pos = self._find_match(text, pattern, pos)
            if match_pos == -1:
                break
            
            matches.append(match_pos)
            pos = match_pos + 1
        
        return matches
    
    def _find_match(self, text: str, pattern: str, start_pos: int = 0) -> int:
        """
        查找单个匹配
        
        Returns:
            匹配开始位置，或-1表示未找到
        """
        for i in range(start_pos, len(text) - len(pattern) + 1):
            if self._match_at_position(text, pattern, i):
                return i
        
        return -1
    
    def _match_at_position(self, text: str, pattern: str, position: int) -> bool:
        """
        检查在指定位置是否匹配
        
        Args:
            text: 文本
            pattern: 模式
            position: 开始位置
            
        Returns:
            是否匹配
        """
        if position + len(pattern) > len(text):
            return False
        
        for i in range(len(pattern)):
            pattern_char = pattern[i]
            text_char = text[position + i]
            
            if pattern_char == SpecialChars.SPACE:
                # 必须匹配空格
                if text_char != ' ':
                    return False
            elif pattern_char == SpecialChars.ANY:
                # 匹配任意单个字符（包括空格）
                continue
            else:
                # 普通字符必须完全匹配
                if text_char != pattern_char:
                    return False
        
        return True
    
    def save_search_results(self, results: List[Dict], output_path: str):
        """
        保存搜索结果到文件
        """
        try:
            # 确保父目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, result in enumerate(results):
                    f.write(f"SEQUENCE:{i+1}\n")
                    if isinstance(result, dict):
                        cursor_format = self.format_converter.create_cursor_format(
                            result["document"], result["position"], result.get("direction", SearchDirection.RIGHT)
                        )
                    else:
                        cursor_format = str(result)
                    f.write(f"CURSOR:{cursor_format}\n\n")
            
            return True
        except Exception as e:
            print(f"保存搜索结果失败: {e}")
            return False