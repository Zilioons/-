# src/knowledge_system/uid_system.py
"""
UID系统模块
实现全局唯一标识符的生成与管理
"""

import threading
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field


class UIDType(Enum):
    """UID类型枚举"""
    CONCEPT = "概念"
    PROPOSITION = "命题"
    STRUCTURE = "结构"
    RELATION = "关系"
    FILE = "文件"
    LINK = "链接"
    OPERATOR = "操作符"


@dataclass
class Entity:
    """实体基类"""
    uid: str
    name: str
    entity_type: UIDType
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def __str__(self):
        return f"{self.name}({self.uid})"


class UIDRegistry:
    """UID注册表"""
    
    def __init__(self):
        self._uid_to_entity: Dict[str, Entity] = {}
        self._word_to_uids: Dict[str, Set[str]] = {}
        self._type_to_uids: Dict[UIDType, Set[str]] = {}
        self._lock = threading.RLock()
        self._next_id = 1
        
        # 预定义特殊符号的UID
        self._init_special_symbols()
    
    def _init_special_symbols(self):
        """初始化特殊符号UID（用于逻辑链解析）"""
        special_symbols = {
            "左括号": ("(", UIDType.STRUCTURE),
            "右括号": (")", UIDType.STRUCTURE),
            "分隔符": ("/", UIDType.OPERATOR),
            "逻辑导向符": (">", UIDType.OPERATOR),
            "与操作符": ("&", UIDType.OPERATOR),
            "或操作符": ("|", UIDType.OPERATOR),
            "非操作符": ("~", UIDType.OPERATOR),
            "蕴含操作符": ("→", UIDType.OPERATOR),
            "等价操作符": ("≡", UIDType.OPERATOR),
        }
        
        for name, (symbol, uid_type) in special_symbols.items():
            self.register(symbol, uid_type, {"is_special": True, "display_name": name})
    
    def register(self, name: str, entity_type: UIDType, metadata=None) -> str:
        """注册新实体"""
        with self._lock:
            # 生成简短的UID：类型前缀 + 序号
            uid = f"{entity_type.value[:2]}{self._next_id:06d}"
            self._next_id += 1
            
            entity = Entity(uid=uid, name=name, entity_type=entity_type, 
                           metadata=metadata or {})
            
            self._uid_to_entity[uid] = entity
            
            # 更新类型索引
            if entity_type not in self._type_to_uids:
                self._type_to_uids[entity_type] = set()
            self._type_to_uids[entity_type].add(uid)
            
            # 更新词索引（支持中文分词）
            words = self._tokenize_chinese(name)
            for word in words:
                if word not in self._word_to_uids:
                    self._word_to_uids[word] = set()
                self._word_to_uids[word].add(uid)
            
            return uid
    
    def _tokenize_chinese(self, text: str) -> List[str]:
        """简单的中文分词"""
        # 按字符分割（中文每个字符都有意义）
        chars = list(text)
        
        # 同时考虑完整词
        words = chars + [text]
        
        return list(set(words))  # 去重
    
    def get_entity(self, uid: str) -> Optional[Entity]:
        """通过UID获取实体"""
        return self._uid_to_entity.get(uid)
    
    def get_uids_by_word(self, word: str) -> List[str]:
        """根据词获取UID列表（一词多义）"""
        return list(self._word_to_uids.get(word, set()))
    
    def get_uids_by_type(self, entity_type: UIDType) -> List[str]:
        """根据类型获取UID列表"""
        return list(self._type_to_uids.get(entity_type, set()))
    
    def get_special_symbol(self, symbol: str) -> Optional[Entity]:
        """获取特殊符号的UID"""
        for uid, entity in self._uid_to_entity.items():
            if entity.name == symbol and entity.metadata.get("is_special", False):
                return entity
        return None
    
    def __len__(self):
        return len(self._uid_to_entity)
    
    def __contains__(self, uid: str):
        return uid in self._uid_to_entity


class UIDSequence:
    """UID序列"""
    
    def __init__(self, uids: Optional[List[str]] = None, name: str = "未命名序列"):
        self.uids = uids or []
        self.name = name
        self.id = f"SEQ{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.metadata: Dict[str, Any] = {"created": time.time()}
    
    def append(self, uid: str):
        """添加UID"""
        self.uids.append(uid)
    
    def extend(self, uids: List[str]):
        """扩展序列"""
        self.uids.extend(uids)
    
    def insert(self, index: int, uid: str):
        """插入UID"""
        self.uids.insert(index, uid)
    
    def remove(self, uid: str):
        """移除UID"""
        if uid in self.uids:
            self.uids.remove(uid)
    
    def to_string(self, separator: str = " → ") -> str:
        """转换为字符串"""
        return separator.join(self.uids)
    
    def to_detailed_string(self, registry: 'UIDRegistry') -> str:
        """转换为详细字符串（显示名称）"""
        names = []
        for uid in self.uids:
            entity = registry.get_entity(uid)
            if entity:
                names.append(entity.name)
            else:
                names.append(f"[{uid}]")
        return " → ".join(names)
    
    def __len__(self):
        return len(self.uids)
    
    def __getitem__(self, index):
        return self.uids[index]
    
    def __iter__(self):
        return iter(self.uids)