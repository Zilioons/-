import os
import json
import time
import logging
from typing import Dict, List, Optional

from ..core.uid_generator import uid_generator

logger = logging.getLogger(__name__)

class CursorManager:
    def __init__(self, cursor_dir: str):
        self.cursor_dir = cursor_dir
        os.makedirs(cursor_dir, exist_ok=True)
        self.cursors: Dict[str, Dict] = {}
        self._load_cursors()
        
        if not self.cursors:
            self.create_cursor(position=0, name="main")
    
    def _load_cursors(self):
        try:
            for filename in os.listdir(self.cursor_dir):
                if filename.endswith(".cursor"):
                    filepath = os.path.join(self.cursor_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        cursor_data = json.load(f)
                    
                    cursor_id = cursor_data.get("cursor_id")
                    if cursor_id:
                        self.cursors[cursor_id] = cursor_data
        except Exception as e:
            logger.error(f"加载光标失败: {e}")
    
    def create_cursor(self, position: int = 0, name: str = None) -> str:
        cursor_id = uid_generator.generate_cursor_id()
        
        cursor_data = {
            "cursor_id": cursor_id,
            "position": position,
            "name": name or f"cursor_{cursor_id[:8]}",
            "created_at": time.time(),
            "last_updated": time.time(),
            "is_active": True
        }
        
        # 保存到文件
        filename = f"{cursor_id}.cursor"
        filepath = os.path.join(self.cursor_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cursor_data, f, indent=2)
        
        self.cursors[cursor_id] = cursor_data
        logger.info(f"创建光标: {cursor_id} (位置: {position}, 名称: {cursor_data['name']})")
        return cursor_id
    
    def get_cursor(self, cursor_id: str) -> Optional[Dict]:
        return self.cursors.get(cursor_id)
    
    def move_cursor(self, cursor_id: str, direction: str, spaces: int = 1) -> bool:
        cursor = self.get_cursor(cursor_id)
        if not cursor:
            logger.error(f"光标不存在: {cursor_id}")
            return False
        
        if direction.upper() == "RIGHT":
            new_position = cursor["position"] + spaces
        elif direction.upper() == "LEFT":
            new_position = max(0, cursor["position"] - spaces)
        else:
            logger.error(f"无效方向: {direction}")
            return False
        
        # 更新光标
        cursor["position"] = new_position
        cursor["last_updated"] = time.time()
        
        # 保存文件
        filename = f"{cursor_id}.cursor"
        filepath = os.path.join(self.cursor_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cursor, f, indent=2)
        
        logger.debug(f"移动光标 {cursor_id}: {new_position} ({direction} {spaces})")
        return True