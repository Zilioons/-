"""
主系统整合模块
将UID系统、光标系统、寻路搜索和逻辑链解析整合在一起
"""

import time
from typing import Optional

from .uid_system import UIDRegistry, UIDSequence, UIDType
from .cursor_system import CursorSystem, CursorState
from .search_system import GraphSearchSystem
from .logic_chain import LogicChain, LogicChainParser
from .file_manager import FileManager


class KnowledgeSystem:
    """知识系统（整合所有功能）"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        初始化知识系统
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 初始化核心组件
        self.registry = UIDRegistry()
        self.file_manager = FileManager(self.registry)
        self.cursor_system = CursorSystem(self.registry)
        self.graph_search = GraphSearchSystem(self.registry)
        self.logic_parser = LogicChainParser(self.registry)
        
        # 当前文件引用
        self.current_file: Optional[UIDSequence] = None
        
        print("=" * 60)
        print("🧠 知识系统 v2.0 已启动")
        print("包含：UID系统、光标系统、寻路搜索、逻辑链解析")
        print("=" * 60)
    
    def setup_demo(self):
        """设置演示数据"""
        print("\n正在设置演示数据...")
        
        # 注册一些概念
        concepts = ["数学", "逻辑", "推理", "证明", "集合", "函数", "方程", "几何"]
        concept_uids = {}
        
        for concept in concepts:
            uid = self.registry.register(concept, UIDType.CONCEPT)
            concept_uids[concept] = uid
        
        # 创建逻辑链
        logic_chains = [
            ("数学", "逻辑", "推理", False),
            ("集合", "函数", "方程", False),
            ("推理", None, "证明", True),
        ]
        
        for start, med, end, bidir in logic_chains:
            try:
                start_uid = concept_uids.get(start) or self.registry.get_uids_by_word(start)[0]
                med_uid = concept_uids.get(med) if med else None
                end_uid = concept_uids.get(end) or self.registry.get_uids_by_word(end)[0]
                
                chain = self.logic_parser.create_logic_chain(
                    start_uid, end_uid, med_uid, bidir
                )
                
                self.graph_search.add_logic_chain(chain)
            except Exception as e:
                print(f"创建逻辑链失败：{e}")
        
        # 创建文件
        file_uids = [
            concept_uids["数学"],
            concept_uids["逻辑"],
            concept_uids["推理"],
            concept_uids["证明"],
        ]
        
        file_id = self.file_manager.create_file("数学基础教程", file_uids)
        self.current_file = self.file_manager.load_file(file_id)
        
        # 设置光标系统
        self.cursor_system.set_current_sequence(self.current_file)
        
        print("✅ 演示数据设置完成")
        return self
    
    def create_concept(self, name: str, concept_type: str = "概念") -> str:
        """创建新概念"""
        uid_type = UIDType(concept_type) if concept_type in UIDType.__members__ else UIDType.CONCEPT
        return self.registry.register(name, uid_type)
    
    def create_relation(self, start: str, mediate: Optional[str], end: str, 
                       bidirectional: bool = False) -> Optional[LogicChain]:
        """创建逻辑关系"""
        try:
            start_uids = self.registry.get_uids_by_word(start)
            end_uids = self.registry.get_uids_by_word(end)
            
            if not start_uids or not end_uids:
                return None
            
            start_uid = start_uids[0]
            end_uid = end_uids[0]
            med_uid = None
            
            if mediate:
                med_uids = self.registry.get_uids_by_word(mediate)
                if med_uids:
                    med_uid = med_uids[0]
            
            chain = self.logic_parser.create_logic_chain(
                start_uid, end_uid, med_uid, bidirectional
            )
            
            if not chain.parse_error:
                self.graph_search.add_logic_chain(chain)
                return chain
            
        except Exception as e:
            print(f"创建关系失败：{e}")
        
        return None
    
    def find_paths(self, start: str, end: str, must_pass: Optional[list] = None,
                  max_paths: int = 5) -> list:
        """查找所有路径"""
        start_uids = self.registry.get_uids_by_word(start)
        end_uids = self.registry.get_uids_by_word(end)
        
        if not start_uids or not end_uids:
            return []
        
        start_uid = start_uids[0]
        end_uid = end_uids[0]
        
        # 转换必须经过的UID
        must_pass_uids = []
        if must_pass:
            for word in must_pass:
                uids = self.registry.get_uids_by_word(word)
                if uids:
                    must_pass_uids.append(uids[0])
        
        if must_pass_uids:
            # 如果有必须经过的节点，使用寻路算法
            path = self.graph_search.find_path(
                start_uid, end_uid, must_pass_uids
            )
            return [path] if path else []
        else:
            # 否则查找所有路径
            return self.graph_search.find_all_paths(
                start_uid, end_uid, max_paths
            )
    
    def parse_logic(self, expression: str) -> list:
        """解析逻辑表达式"""
        try:
            # 将表达式转换为UID序列
            uid_sequence = []
            
            for char in expression:
                if char in "()/>&|~→≡":
                    entity = self.registry.get_special_symbol(char)
                    if entity:
                        uid_sequence.append(entity.uid)
                else:
                    uids = self.registry.get_uids_by_word(char)
                    if uids:
                        uid_sequence.append(uids[0])
            
            # 解析逻辑链
            chains = self.logic_parser.parse_nested_expression(uid_sequence)
            return chains
            
        except Exception as e:
            print(f"解析错误：{e}")
            return []
    
    def interactive_mode(self):
        """交互式模式"""
        # 这里实现交互式命令行界面
        # 由于代码较长，这里简化为导入cli模块
        from .cli import interactive_mode
        interactive_mode(self)