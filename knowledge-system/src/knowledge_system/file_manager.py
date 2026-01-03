# src/knowledge_system/file_manager.py
"""
文件管理器模块
管理多个UID序列（文件）
"""

import time
from typing import Dict, List, Optional

from .uid_system import UIDRegistry, UIDSequence, UIDType


class FileManager:
    """文件管理器"""
    
    def __init__(self, registry: UIDRegistry):
        self.registry = registry
        self.files: Dict[str, UIDSequence] = {}
        self.current_file_id: Optional[str] = None
    
    def create_file(self, name: str, uids: List[str] = None) -> str:
        """创建新文件"""
        sequence = UIDSequence(uids or [], name=name)
        self.files[sequence.id] = sequence
        
        # 注册文件实体
        file_uid = self.registry.register(name, UIDType.FILE, {
            "sequence_id": sequence.id,
            "created": time.time()
        })
        
        print(f"📄 已创建文件：{name}")
        return sequence.id
    
    def load_file(self, file_id: str) -> Optional[UIDSequence]:
        """加载文件"""
        if file_id in self.files:
            self.current_file_id = file_id
            return self.files[file_id]
        return None
    
    def get_current_file(self) -> Optional[UIDSequence]:
        """获取当前文件"""
        if self.current_file_id:
            return self.files.get(self.current_file_id)
        return None