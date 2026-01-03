# src/knowledge_system/logic_chain.py
"""
逻辑链解析模块
处理符号化逻辑表达式
"""

import time
import uuid
from typing import List, Optional, Dict, Any

from .uid_system import UIDRegistry, UIDSequence, UIDType


class LogicChain:
    """逻辑链表示"""
    
    def __init__(self, uid_sequence: List[str], registry: UIDRegistry):
        self.uid_sequence = uid_sequence
        self.registry = registry
        self.id = f"LOGIC_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # 解析出的组件
        self.start_uid: Optional[str] = None
        self.mediate_uid: Optional[str] = None
        self.end_uid: Optional[str] = None
        self.is_bidirectional: bool = False
        self.parse_error: Optional[str] = None
        
        # 尝试解析
        self._parse()
    
    def _parse(self):
        """解析逻辑链"""
        try:
            # 获取特殊符号的UID
            left_paren = self.registry.get_special_symbol("(")
            right_paren = self.registry.get_special_symbol(")")
            separator = self.registry.get_special_symbol("/")
            arrow = self.registry.get_special_symbol(">")
            double_arrow = self.registry.get_special_symbol("→")
            
            if not all([left_paren, right_paren, separator, arrow]):
                self.parse_error = "缺少必要的特殊符号"
                return
            
            # 检查基本结构
            if len(self.uid_sequence) < 7:
                self.parse_error = "序列太短，无法构成完整逻辑链"
                return
            
            # 检查括号匹配
            if self.uid_sequence[0] != left_paren.uid:
                self.parse_error = "缺少左括号"
                return
            
            # 查找右括号
            right_paren_pos = -1
            for i, uid in enumerate(self.uid_sequence):
                if uid == right_paren.uid:
                    right_paren_pos = i
                    break
            
            if right_paren_pos == -1:
                self.parse_error = "缺少右括号"
                return
            
            # 提取括号内的部分
            inner_sequence = self.uid_sequence[1:right_paren_pos]
            
            # 解析内部结构
            # 查找分隔符和箭头
            sep_pos = -1
            arrow_pos = -1
            
            for i, uid in enumerate(inner_sequence):
                if uid == separator.uid:
                    sep_pos = i
                elif uid == arrow.uid or (double_arrow and uid == double_arrow.uid):
                    arrow_pos = i
                    if uid == double_arrow.uid:
                        self.is_bidirectional = True
            
            if sep_pos == -1 or arrow_pos == -1:
                self.parse_error = "缺少分隔符或箭头"
                return
            
            if not (0 < sep_pos < arrow_pos < len(inner_sequence) - 1):
                self.parse_error = "结构顺序错误"
                return
            
            # 提取组件
            self.start_uid = inner_sequence[sep_pos - 1] if sep_pos > 0 else None
            self.mediate_uid = inner_sequence[arrow_pos - 1] if arrow_pos > sep_pos + 1 else None
            self.end_uid = inner_sequence[arrow_pos + 1] if arrow_pos < len(inner_sequence) - 1 else None
            
            # 验证组件存在
            if not self.start_uid or not self.end_uid:
                self.parse_error = "缺少起始或终结组件"
            
        except Exception as e:
            self.parse_error = f"解析错误：{str(e)}"
    
    def to_string(self) -> str:
        """转换为可读字符串"""
        if self.parse_error:
            return f"[解析错误：{self.parse_error}]"
        
        parts = []
        for uid in self.uid_sequence:
            entity = self.registry.get_entity(uid)
            if entity:
                parts.append(entity.name)
            else:
                parts.append(f"[{uid[:6]}]")
        
        return "".join(parts)
    
    def get_description(self) -> str:
        """获取逻辑链描述"""
        if self.parse_error:
            return f"无效逻辑链：{self.parse_error}"
        
        start = self.registry.get_entity(self.start_uid) if self.start_uid else None
        mediate = self.registry.get_entity(self.mediate_uid) if self.mediate_uid else None
        end = self.registry.get_entity(self.end_uid) if self.end_uid else None
        
        if mediate:
            return f"{start.name} 通过 {mediate.name} { '双向' if self.is_bidirectional else '导向' } {end.name}"
        else:
            return f"{start.name} { '↔' if self.is_bidirectional else '→' } {end.name}"
    
    def __str__(self):
        return self.get_description()


class LogicChainParser:
    """逻辑链解析器"""
    
    def __init__(self, registry: UIDRegistry):
        self.registry = registry
        
        # 获取特殊符号
        self.left_paren = registry.get_special_symbol("(")
        self.right_paren = registry.get_special_symbol(")")
        self.separator = registry.get_special_symbol("/")
        self.arrow = registry.get_special_symbol(">")
        self.double_arrow = registry.get_special_symbol("→")
        
        print("✅ 逻辑链解析器已启动")
    
    def parse_sequence(self, uid_sequence: List[str]) -> LogicChain:
        """解析UID序列为逻辑链"""
        logic_chain = LogicChain(uid_sequence, self.registry)
        return logic_chain
    
    def create_logic_chain(self, start: str, end: str, 
                          mediate: Optional[str] = None,
                          bidirectional: bool = False) -> LogicChain:
        """创建逻辑链UID序列"""
        if not self.left_paren or not self.right_paren or not self.separator or not self.arrow:
            raise ValueError("特殊符号未初始化")
        
        # 构建序列
        sequence = []
        
        # 左括号
        sequence.append(self.left_paren.uid)
        
        # 起始状态
        sequence.append(start)
        
        # 分隔符
        sequence.append(self.separator.uid)
        
        # 介导因素（如果有）
        if mediate:
            sequence.append(mediate)
        
        # 逻辑导向符
        arrow = self.double_arrow if bidirectional else self.arrow
        sequence.append(arrow.uid)
        
        # 终结状态
        sequence.append(end)
        
        # 右括号
        sequence.append(self.right_paren.uid)
        
        return LogicChain(sequence, self.registry)
    
    def parse_nested_expression(self, uid_sequence: List[str]) -> List[LogicChain]:
        """解析嵌套表达式（支持多层括号）"""
        chains = []
        
        # 使用栈处理嵌套
        stack = []
        current_pos = 0
        
        while current_pos < len(uid_sequence):
            uid = uid_sequence[current_pos]
            entity = self.registry.get_entity(uid)
            
            if entity and entity.name == "(":
                # 开始新的逻辑链
                stack.append(current_pos)
            
            elif entity and entity.name == ")":
                if stack:
                    start_pos = stack.pop()
                    # 提取逻辑链
                    chain_sequence = uid_sequence[start_pos:current_pos + 1]
                    
                    # 尝试解析
                    chain = self.parse_sequence(chain_sequence)
                    chains.append(chain)
                else:
                    # 括号不匹配
                    error_chain = LogicChain([uid], self.registry)
                    error_chain.parse_error = "括号不匹配"
                    chains.append(error_chain)
            
            current_pos += 1
        
        # 检查栈是否为空（是否有未匹配的左括号）
        if stack:
            for pos in stack:
                error_chain = LogicChain([uid_sequence[pos]], self.registry)
                error_chain.parse_error = "未匹配的左括号"
                chains.append(error_chain)
        
        return chains