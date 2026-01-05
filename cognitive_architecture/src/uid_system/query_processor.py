import os
import json
import time
import shlex
import logging
from typing import Dict, Optional

from ..core.uid_generator import uid_generator
from ..core.constants import SystemPaths

logger = logging.getLogger(__name__)

class QueryProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.root_dir = config['system_root']
        
        self.outbox_dir = os.path.join(self.root_dir, "uid_system", "outbox")
        os.makedirs(self.outbox_dir, exist_ok=True)
        
        self.documents_root = os.path.join(self.root_dir, "documents")
        os.makedirs(self.documents_root, exist_ok=True)
        
        # 示例UID注册表（简化）
        self.uid_registry = {
            "UID_ALPHA": "苹果",
            "UID_BETA": "香蕉",
            "UID_GAMMA": "橙子",
            "UID_HELLO": "Hello World",
        }
        
        logger.info("查询处理器初始化完成")
    
    def process_query(self, task_content: str) -> str:
        try:
            # 解析查询任务
            parts = shlex.split(task_content.strip())
            
            if len(parts) < 2:
                return self._create_error_result("查询任务必须包含指令和目标")
            
            task_type = parts[0].upper()
            target = parts[1]
            search_path = parts[2] if len(parts) > 2 else None
            
            logger.info(f"处理查询: {task_type} {target}")
            
            # 执行查询
            if task_type == "FIND_CHAR":
                result = self._find_char(target, search_path)
            elif task_type == "FIND_UID":
                result = self._find_uid(target, search_path)
            else:
                return self._create_error_result(f"未知查询类型: {task_type}")
            
            # 创建结果文件
            result_file = self._create_result_file(task_type, target, result)
            return result_file
            
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            return self._create_error_result(f"处理查询失败: {str(e)}")
    
    def _find_char(self, uid: str, search_path: Optional[str]) -> Dict:
        """查找UID对应的字符"""
        result = {
            "query_type": "FIND_CHAR",
            "target": uid,
            "timestamp": time.time()
        }
        
        # 在注册表中查找
        if uid in self.uid_registry:
            result["found"] = True
            result["char"] = self.uid_registry[uid]
            result["source"] = "registry"
        else:
            result["found"] = False
            result["message"] = "UID未找到"
        
        return result
    
    def _find_uid(self, char: str, search_path: Optional[str]) -> Dict:
        """查找字符对应的UID"""
        result = {
            "query_type": "FIND_UID",
            "target": char,
            "timestamp": time.time()
        }
        
        # 在注册表中查找
        uids = []
        for uid, registered_char in self.uid_registry.items():
            if registered_char == char:
                uids.append(uid)
        
        if uids:
            result["found"] = True
            result["uids"] = uids
            result["uid_count"] = len(uids)
        else:
            result["found"] = False
            result["message"] = "字符未找到对应的UID"
        
        return result
    
    def _create_result_file(self, task_type: str, target: str, query_result: Dict) -> str:
        """创建结果文件"""
        result_id = uid_generator.generate_result_id()
        
        full_result = {
            "result_id": result_id,
            "task_type": task_type,
            "target": target,
            "query_result": query_result,
            "status": "SUCCESS" if query_result.get("found") else "NOT_FOUND",
            "timestamp": time.time(),
            "processor_version": "1.0"
        }
        
        filename = f"result_{result_id}.uid"
        filepath = os.path.join(self.outbox_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"查询结果已保存: {filepath}")
        return filepath
    
    def _create_error_result(self, error_msg: str) -> str:
        """创建错误结果文件"""
        result_id = uid_generator.generate_result_id()
        
        error_result = {
            "result_id": result_id,
            "status": "ERROR",
            "error": error_msg,
            "timestamp": time.time()
        }
        
        filename = f"error_{result_id}.uid"
        filepath = os.path.join(self.outbox_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2)
        
        logger.error(f"创建错误结果: {filepath}")
        return filepath
    
    def get_registry_stats(self) -> Dict:
        """获取注册表统计信息"""
        return {
            "total_uids": len(self.uid_registry),
            "total_chars": len(set(self.uid_registry.values()))
        }