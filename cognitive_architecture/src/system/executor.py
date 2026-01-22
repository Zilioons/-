"""
指令执行器
协调指令的完整执行流程
"""

import os
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

from .parser import InstructionParser
from .searcher import Searcher
from ..core.formats import FormatConverter
from ..core.constants import PROJECT_ROOT

logger = logging.getLogger(__name__)

class InstructionExecutor:
    """指令执行器"""
    
    def __init__(self):
        self.parser = InstructionParser()
        self.searcher = Searcher()
        self.format_converter = FormatConverter()
        
        # 操作历史
        self.history = []
        
    def execute_from_trigger(self, unit_path: str, cursor_file_path: str) -> bool:
        """
        从触发执行完整流程
        
        Args:
            unit_path: 触发单元路径
            cursor_file_path: 光标文件路径
            
        Returns:
            执行是否成功
        """
        try:
            logger.info(f"执行触发: {unit_path}")
            
            # 1. 读取光标文件
            cursor_data = self._read_cursor_file(cursor_file_path)
            if not cursor_data:
                logger.error(f"无法读取光标文件: {cursor_file_path}")
                return False
            
            # 2. 从光标位置读取指令
            instruction_text = self._read_instruction_at_cursor(cursor_data)
            if not instruction_text:
                logger.warning(f"在光标位置未找到指令")
                return False
            
            # 3. 解析指令
            success, parsed = self.parser.parse_instruction(instruction_text, cursor_data)
            if not success:
                error_msg = parsed.get("error", "未知错误")
                logger.error(f"解析指令失败: {error_msg}")
                return False
            
            # 4. 执行指令
            execution_success, message = self._execute_parsed_instruction(parsed)
            
            if execution_success:
                logger.info(f"指令执行成功: {message}")
                
                # 5. 检查连续分隔符
                if parsed.get("has_continuous_separator", False):
                    logger.info("检测到连续分隔符，准备下一次执行")
                    # 这里应该触发下一次执行
                    # 实际实现需要与监控系统协调
            else:
                logger.error(f"指令执行失败: {message}")
            
            # 6. 记录历史
            self.history.append({
                "unit": unit_path,
                "cursor": cursor_data,
                "instruction": instruction_text,
                "success": execution_success,
                "message": message,
                "timestamp": time.time()
            })
            
            return execution_success
            
        except Exception as e:
            logger.error(f"执行触发时出错: {e}")
            return False
    
    def _read_cursor_file(self, cursor_file_path: str) -> Optional[Dict]:
        """读取光标文件"""
        try:
            if not os.path.exists(cursor_file_path):
                return None
            
            with open(cursor_file_path, 'r', encoding='utf-8') as f:
                cursor_text = f.read().strip()
            
            return self.format_converter.parse_cursor_format(cursor_text)
            
        except Exception as e:
            logger.error(f"读取光标文件失败: {e}")
            return None
    
    def _read_instruction_at_cursor(self, cursor_data: Dict) -> Optional[str]:
        """
        从光标位置读取指令
        
        策略：读取光标位置右侧的内容，直到遇到分隔符
        """
        try:
            document_path = cursor_data["document"]
            position = cursor_data["position"]
            
            if not os.path.exists(document_path):
                return None
            
            with open(document_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if position >= len(content):
                return None
            
            # 从位置开始读取，直到遇到分隔符
            end_pos = position
            while end_pos < len(content):
                char = content[end_pos]
                
                # 检查是否遇到指令分隔符
                if char == ';':
                    # 检查是否是连续分隔符
                    if end_pos + 1 < len(content) and content[end_pos + 1] == ';':
                        end_pos += 2  # 跳过连续分隔符
                        break
                    else:
                        end_pos += 1  # 跳过单个分隔符
                        break
                
                end_pos += 1
            
            # 提取指令文本
            instruction_text = content[position:end_pos].strip()
            
            return instruction_text
            
        except Exception as e:
            logger.error(f"读取指令失败: {e}")
            return None
    
    def _execute_parsed_instruction(self, parsed_instruction: Dict) -> Tuple[bool, str]:
        """执行解析后的指令"""
        instruction_type = parsed_instruction.get("type")
        
        if instruction_type in ["COPY", "DELETE", "CREATE_FILE", "CREATE_FOLDER"]:
            return self.parser.execute_instruction(parsed_instruction)
        
        elif instruction_type == "SEARCH":
            return self._execute_search(parsed_instruction)
        
        elif instruction_type == "SEARCH_IN":
            return self._execute_search_in(parsed_instruction)
        
        elif instruction_type == "LOCAL_SEARCH":
            return self._execute_local_search(parsed_instruction)
        
        elif instruction_type == "GENERATE":
            return self._execute_generate(parsed_instruction)
        
        else:
            return False, f"不支持的指令类型: {instruction_type}"
    
    def _execute_search(self, instruction: Dict) -> Tuple[bool, str]:
        """执行全局搜索"""
        try:
            results = self.searcher.search(
                instruction["search_target"],
                instruction["max_time_ms"]
            )
            
            # 保存结果
            success = self.searcher.save_search_results(
                results, instruction["output_path"]
            )
            
            if success:
                return True, f"搜索完成，找到 {len(results)} 个匹配，结果保存在 {instruction['output_path']}"
            else:
                return False, "保存搜索结果失败"
                
        except Exception as e:
            return False, f"搜索失败: {e}"
    
    def _execute_search_in(self, instruction: Dict) -> Tuple[bool, str]:
        """执行精准搜索"""
        try:
            results = self.searcher.search_in(
                instruction["cursor"],
                instruction["search_target"],
                instruction["max_time_ms"]
            )
            
            # 保存结果
            success = self.searcher.save_search_results(
                results, instruction["output_path"]
            )
            
            if success:
                return True, f"精准搜索完成，找到 {len(results)} 个匹配"
            else:
                return False, "保存搜索结果失败"
                
        except Exception as e:
            return False, f"精准搜索失败: {e}"
    
    def _execute_local_search(self, instruction: Dict) -> Tuple[bool, str]:
        """执行局部搜索"""
        try:
            result = self.searcher.local_search(
                instruction["base_cursor"],
                instruction["direction"],
                instruction["count"],
                instruction["search_target"]
            )
            
            if result:
                # 保存结果
                cursor_format = self.format_converter.create_cursor_format(
                    result["document"], result["position"], result["direction"]
                )
                
                output_path = instruction["output_path"]
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(cursor_format)
                
                return True, f"局部搜索完成，结果保存在 {output_path}"
            else:
                return False, "局部搜索未找到匹配"
                
        except Exception as e:
            return False, f"局部搜索失败: {e}"
    
    def _execute_generate(self, instruction: Dict) -> Tuple[bool, str]:
        """执行生成指令"""
        try:
            # 简化的生成：将目标文字保存到文件
            output_path = instruction["output_path"]
            target_text = instruction["target_text"]
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(target_text)
            
            return True, f"已生成内容到 {output_path}"
            
        except Exception as e:
            return False, f"生成失败: {e}"