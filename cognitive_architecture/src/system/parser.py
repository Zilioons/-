"""
指令解析器
解析和执行各种指令
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from ..core.constants import (
    InstructionType, SearchDirection, Separators,
    SpecialChars, ErrorMessages
)
from ..core.formats import FormatConverter
from ..core.positions import PositionManager

class InstructionParser:
    """指令解析器"""
    
    def __init__(self):
        self.format_converter = FormatConverter()
        self.position_manager = PositionManager()
        
    def parse_instruction(self, instruction_text: str, cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析指令文本
        
        Args:
            instruction_text: 指令文本
            cursor_data: 当前光标数据
            
        Returns:
            (成功标志, 解析结果)
        """
        try:
            # 清理指令文本
            instruction_text = instruction_text.strip()
            
            if not instruction_text:
                return False, {"error": "空指令"}
            
            # 检查连续分隔符
            has_continuous_separator = instruction_text.endswith(Separators.CONTINUOUS)
            
            # 移除分隔符
            if has_continuous_separator:
                instruction_text = instruction_text[:-2]
            elif instruction_text.endswith(Separators.INSTRUCTION):
                instruction_text = instruction_text[:-1]
            
            # 分割指令和参数
            parts = instruction_text.strip().split()
            if not parts:
                return False, {"error": "无效指令"}
            
            instruction_type = parts[0]
            
            # 根据指令类型解析
            if instruction_type == InstructionType.COPY:
                result = self._parse_copy_instruction(parts[1:], cursor_data)
            elif instruction_type == InstructionType.DELETE:
                result = self._parse_delete_instruction(parts[1:], cursor_data)
            elif instruction_type == InstructionType.SEARCH:
                result = self._parse_search_instruction(parts[1:], cursor_data)
            elif instruction_type == InstructionType.SEARCH_IN:
                result = self._parse_search_in_instruction(parts[1:], cursor_data)
            elif instruction_type == InstructionType.LOCAL_SEARCH:
                result = self._parse_local_search_instruction(parts[1:], cursor_data)
            elif instruction_type == InstructionType.CREATE_FILE:
                result = self._parse_create_file_instruction(parts[1:], cursor_data)
            elif instruction_type == InstructionType.CREATE_FOLDER:
                result = self._parse_create_folder_instruction(parts[1:], cursor_data)
            elif instruction_type == InstructionType.GENERATE:
                result = self._parse_generate_instruction(parts[1:], cursor_data)
            else:
                return False, {"error": ErrorMessages.UNKNOWN_INSTRUCTION}
            
            if result[0]:
                # 添加连续分隔符标记
                result[1]["has_continuous_separator"] = has_continuous_separator
                return result
            else:
                return result
                
        except Exception as e:
            return False, {"error": f"解析指令时出错: {e}"}
    
    def _parse_copy_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析复制指令
        格式: 数字 数字 路径 数字 分隔符
        """
        if len(params) < 5:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            # 解析参数
            start_pos = int(params[0])
            end_pos = int(params[1])
            target_path = self.format_converter.parse_path_format(params[2])
            target_pos = int(params[3])
            separator = params[4]  # 分隔符，用于验证格式
            
            # 验证参数
            document = cursor_data.get("document")
            if not document:
                return False, {"error": "光标缺少文档信息"}
            
            if start_pos > end_pos:
                return False, {"error": "起始位置不能大于结束位置"}
            
            return True, {
                "type": InstructionType.COPY,
                "document": document,
                "start_position": start_pos,
                "end_position": end_pos,
                "target_document": target_path,
                "target_position": target_pos,
                "separator": separator
            }
            
        except ValueError:
            return False, {"error": "位置参数必须是数字"}
        except Exception as e:
            return False, {"error": f"解析复制指令出错: {e}"}
    
    def _parse_delete_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析删除指令
        格式: 数字 数字 分隔符
        """
        if len(params) < 3:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            start_pos = int(params[0])
            end_pos = int(params[1])
            separator = params[2]
            
            document = cursor_data.get("document")
            if not document:
                return False, {"error": "光标缺少文档信息"}
            
            if start_pos > end_pos:
                return False, {"error": "起始位置不能大于结束位置"}
            
            return True, {
                "type": InstructionType.DELETE,
                "document": document,
                "start_position": start_pos,
                "end_position": end_pos,
                "separator": separator
            }
            
        except ValueError:
            return False, {"error": "位置参数必须是数字"}
        except Exception as e:
            return False, {"error": f"解析删除指令出错: {e}"}
    
    def _parse_search_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析搜索指令
        格式: 搜索目标 最大时间 输出位置
        """
        if len(params) < 3:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            search_target = params[0]
            max_time = int(params[1])
            output_path = self.format_converter.parse_path_format(params[2])
            
            # 验证输出路径
            if not self.format_converter.validate_output_path(output_path):
                return False, {"error": "输出路径无效"}
            
            return True, {
                "type": InstructionType.SEARCH,
                "search_target": search_target,
                "max_time_ms": max_time,
                "output_path": output_path
            }
            
        except ValueError:
            return False, {"error": "最大时间必须是数字"}
        except Exception as e:
            return False, {"error": f"解析搜索指令出错: {e}"}
    
    def _parse_search_in_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析精准搜索指令
        格式: 光标位置 搜索目标 最大时间 输出位置
        """
        if len(params) < 4:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            # 解析光标位置
            cursor_text = " ".join(params[:3])  # 光标格式有三个部分
            cursor_data = self.format_converter.parse_cursor_format(cursor_text)
            
            if not cursor_data:
                return False, {"error": "无效的光标格式"}
            
            search_target = params[3]
            max_time = int(params[4])
            output_path = self.format_converter.parse_path_format(params[5])
            
            # 验证输出路径
            if not self.format_converter.validate_output_path(output_path):
                return False, {"error": "输出路径无效"}
            
            return True, {
                "type": InstructionType.SEARCH_IN,
                "cursor": cursor_data,
                "search_target": search_target,
                "max_time_ms": max_time,
                "output_path": output_path
            }
            
        except (ValueError, IndexError):
            return False, {"error": "参数格式错误"}
        except Exception as e:
            return False, {"error": f"解析精准搜索指令出错: {e}"}
    
    def _parse_local_search_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析局部搜索指令
        格式: 光标位置 方向 计数 搜索目标 输出位置
        """
        if len(params) < 5:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            # 解析光标位置
            cursor_text = " ".join(params[:3])  # 光标格式有三个部分
            base_cursor = self.format_converter.parse_cursor_format(cursor_text)
            
            if not base_cursor:
                return False, {"error": "无效的光标格式"}
            
            direction = params[3]
            if direction not in [SearchDirection.LEFT, SearchDirection.RIGHT]:
                return False, {"error": "方向必须是LEFT或RIGHT"}
            
            count = int(params[4])
            if count <= 0:
                return False, {"error": "计数必须大于0"}
            
            search_target = params[5]
            output_path = self.format_converter.parse_path_format(params[6])
            
            # 验证输出路径
            if not self.format_converter.validate_output_path(output_path):
                return False, {"error": "输出路径无效"}
            
            return True, {
                "type": InstructionType.LOCAL_SEARCH,
                "base_cursor": base_cursor,
                "direction": direction,
                "count": count,
                "search_target": search_target,
                "output_path": output_path
            }
            
        except (ValueError, IndexError):
            return False, {"error": "参数格式错误"}
        except Exception as e:
            return False, {"error": f"解析局部搜索指令出错: {e}"}
    
    def _parse_create_file_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析创建文件指令
        格式: 路径 [内容]
        """
        if len(params) < 1:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            file_path = self.format_converter.parse_path_format(params[0])
            
            # 可选内容
            content = ""
            if len(params) > 1:
                content = " ".join(params[1:])
            
            return True, {
                "type": InstructionType.CREATE_FILE,
                "file_path": file_path,
                "content": content
            }
            
        except Exception as e:
            return False, {"error": f"解析创建文件指令出错: {e}"}
    
    def _parse_create_folder_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析创建文件夹指令
        格式: 路径
        """
        if len(params) < 1:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            folder_path = self.format_converter.parse_path_format(params[0])
            
            return True, {
                "type": InstructionType.CREATE_FOLDER,
                "folder_path": folder_path
            }
            
        except Exception as e:
            return False, {"error": f"解析创建文件夹指令出错: {e}"}
    
    def _parse_generate_instruction(self, params: List[str], cursor_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        解析生成指令
        格式: 目标文字 输出位置
        """
        if len(params) < 2:
            return False, {"error": ErrorMessages.INSUFFICIENT_PARAMS}
        
        try:
            target_text = params[0]
            output_path = self.format_converter.parse_path_format(params[1])
            
            return True, {
                "type": InstructionType.GENERATE,
                "target_text": target_text,
                "output_path": output_path
            }
            
        except Exception as e:
            return False, {"error": f"解析生成指令出错: {e}"}
    
    def execute_instruction(self, parsed_instruction: Dict) -> Tuple[bool, str]:
        """
        执行解析后的指令
        
        Returns:
            (成功标志, 结果消息)
        """
        try:
            instruction_type = parsed_instruction.get("type")
            
            if instruction_type == InstructionType.COPY:
                return self._execute_copy(parsed_instruction)
            elif instruction_type == InstructionType.DELETE:
                return self._execute_delete(parsed_instruction)
            elif instruction_type == InstructionType.CREATE_FILE:
                return self._execute_create_file(parsed_instruction)
            elif instruction_type == InstructionType.CREATE_FOLDER:
                return self._execute_create_folder(parsed_instruction)
            else:
                return False, f"尚未实现的指令类型: {instruction_type}"
                
        except Exception as e:
            return False, f"执行指令时出错: {e}"
    
    def _execute_copy(self, instruction: Dict) -> Tuple[bool, str]:
        """执行复制指令"""
        try:
            # 复制源内容
            content = self.position_manager.copy_range(
                instruction["document"],
                instruction["start_position"],
                instruction["end_position"]
            )
            
            if content is None:
                return False, "复制失败: 无法读取源内容"
            
            # 添加后空格
            content_with_space = content + " "
            
            # 插入到目标位置
            success = self.position_manager.insert_at_position(
                instruction["target_document"],
                instruction["target_position"],
                content_with_space
            )
            
            if success:
                return True, f"已复制 {len(content)} 个字符到 {instruction['target_document']}"
            else:
                return False, "复制失败: 无法插入到目标位置"
                
        except Exception as e:
            return False, f"复制操作失败: {e}"
    
    def _execute_delete(self, instruction: Dict) -> Tuple[bool, str]:
        """执行删除指令"""
        try:
            # 删除指定范围
            success, deleted_content = self.position_manager.delete_range(
                instruction["document"],
                instruction["start_position"],
                instruction["end_position"]
            )
            
            if not success:
                return False, "删除失败"
            
            # 删除光标位置的空格
            cursor_pos = instruction.get("cursor_position", instruction["start_position"])
            # 注意：删除范围后，位置可能已变化，这里简化处理
            # 实际应该重新计算位置
            
            return True, f"已删除 {len(deleted_content)} 个字符"
            
        except Exception as e:
            return False, f"删除操作失败: {e}"
    
    def _execute_create_file(self, instruction: Dict) -> Tuple[bool, str]:
        """执行创建文件指令"""
        try:
            file_path = Path(instruction["file_path"])
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建文件并写入内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(instruction.get("content", ""))
            
            return True, f"已创建文件: {file_path}"
            
        except Exception as e:
            return False, f"创建文件失败: {e}"
    
    def _execute_create_folder(self, instruction: Dict) -> Tuple[bool, str]:
        """执行创建文件夹指令"""
        try:
            folder_path = Path(instruction["folder_path"])
            folder_path.mkdir(parents=True, exist_ok=True)
            
            return True, f"已创建文件夹: {folder_path}"
            
        except Exception as e:
            return False, f"创建文件夹失败: {e}"