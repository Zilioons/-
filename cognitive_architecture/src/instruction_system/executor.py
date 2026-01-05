import os
import json
import time
import logging
from typing import Dict, List

from ..core.uid_generator import uid_generator
from ..uid_system.query_processor import QueryProcessor
from .cursor_manager import CursorManager

logger = logging.getLogger(__name__)

class InstructionExecutor:
    def __init__(self, config: Dict, 
                 cursor_manager: CursorManager,
                 query_processor: QueryProcessor):
        
        self.config = config
        self.cursor_manager = cursor_manager
        self.query_processor = query_processor
        
        self.result_dir = os.path.join(config['system_root'], "instruction_system", "results")
        os.makedirs(self.result_dir, exist_ok=True)
        
        logger.info("指令执行器初始化完成")
    
    def execute_instruction(self, instruction_content: str) -> Dict:
        try:
            # 分割指令
            parts = instruction_content.strip().split()
            if not parts:
                return self._create_error_result("空指令")
            
            command = parts[0].upper()
            params = parts[1:] if len(parts) > 1 else []
            
            logger.info(f"执行指令: {command} {params}")
            
            # 执行对应指令
            if command == "CREATE_CURSOR":
                result = self._execute_create_cursor(params)
            elif command == "MOVE_CURSOR":
                result = self._execute_move_cursor(params)
            elif command == "FIND_CHAR":
                result = self._execute_find_char(params)
            elif command == "FIND_UID":
                result = self._execute_find_uid(params)
            else:
                result = self._create_error_result(f"未知指令: {command}")
            
            # 保存结果文件
            if result.get("status") == "SUCCESS":
                self._save_instruction_result(instruction_content, result)
            
            return result
            
        except Exception as e:
            logger.error(f"执行指令失败: {e}")
            return self._create_error_result(f"执行指令失败: {str(e)}")
    
    def _execute_create_cursor(self, params: List[str]) -> Dict:
        if len(params) < 1:
            return self._create_error_result("CREATE_CURSOR需要位置参数")
        
        try:
            position = int(params[0])
            name = params[1] if len(params) > 1 else None
            
            cursor_id = self.cursor_manager.create_cursor(position, name)
            
            return {
                "status": "SUCCESS",
                "cursor_id": cursor_id,
                "position": position,
                "name": name or f"cursor_{cursor_id[:8]}",
                "message": f"光标已创建: {cursor_id}"
            }
            
        except ValueError:
            return self._create_error_result("位置参数必须是整数")
    
    def _execute_move_cursor(self, params: List[str]) -> Dict:
        if len(params) < 3:
            return self._create_error_result("MOVE_CURSOR需要光标ID、方向和空格数")
        
        cursor_id = params[0]
        direction = params[1].upper()
        
        try:
            spaces = int(params[2])
        except ValueError:
            return self._create_error_result("空格数必须是整数")
        
        success = self.cursor_manager.move_cursor(cursor_id, direction, spaces)
        
        if success:
            cursor = self.cursor_manager.get_cursor(cursor_id)
            return {
                "status": "SUCCESS",
                "cursor_id": cursor_id,
                "new_position": cursor["position"],
                "direction": direction,
                "spaces": spaces,
                "message": f"光标 {cursor_id} 已移动"
            }
        else:
            return self._create_error_result(f"移动光标失败: {cursor_id}")
    
    def _execute_find_char(self, params: List[str]) -> Dict:
        if len(params) < 1:
            return self._create_error_result("FIND_CHAR需要UID参数")
        
        target_uid = params[0]
        search_path = params[1] if len(params) > 1 else None
        
        # 构建查询
        query_content = f"FIND_CHAR {target_uid}"
        if search_path:
            query_content += f" {search_path}"
        
        # 执行查询
        result_file = self.query_processor.process_query(query_content)
        
        if not result_file or not os.path.exists(result_file):
            return self._create_error_result(f"查询失败: {target_uid}")
        
        return {
            "status": "SUCCESS",
            "query_type": "FIND_CHAR",
            "target": target_uid,
            "result_file": result_file,
            "message": f"查询完成，结果在: {result_file}"
        }
    
    def _execute_find_uid(self, params: List[str]) -> Dict:
        if len(params) < 1:
            return self._create_error_result("FIND_UID需要字符参数")
        
        target_char = params[0]
        search_path = params[1] if len(params) > 1 else None
        
        # 构建查询
        query_content = f'FIND_UID "{target_char}"'
        if search_path:
            query_content += f" {search_path}"
        
        # 执行查询
        result_file = self.query_processor.process_query(query_content)
        
        if not result_file or not os.path.exists(result_file):
            return self._create_error_result(f"查询失败: {target_char}")
        
        return {
            "status": "SUCCESS",
            "query_type": "FIND_UID",
            "target": target_char,
            "result_file": result_file,
            "message": f"查询完成，结果在: {result_file}"
        }
    
    def _create_error_result(self, error_msg: str) -> Dict:
        return {
            "status": "ERROR",
            "error": error_msg,
            "timestamp": time.time()
        }
    
    def _save_instruction_result(self, instruction: str, result: Dict) -> str:
        result_id = uid_generator.generate_result_id()
        
        full_result = {
            "result_id": result_id,
            "instruction": instruction,
            "execution_result": result,
            "timestamp": time.time()
        }
        
        filename = f"instruction_result_{result_id}.json"
        filepath = os.path.join(self.result_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_result, f, indent=2)
        
        logger.debug(f"指令结果已保存: {filepath}")
        return filepath
    
    def get_system_status(self) -> Dict:
        cursor_count = len(self.cursor_manager.cursors)
        registry_stats = self.query_processor.get_registry_stats()
        
        return {
            "cursors": {
                "total_cursors": cursor_count,
                "active_cursors": sum(1 for c in self.cursor_manager.cursors.values() 
                                    if c.get("is_active", True))
            },
            "queries": registry_stats,
            "timestamp": time.time()
        }