# src/knowledge_system/search_system.py
"""
寻路与搜索系统模块
在概念网络中查找路径和关系
"""

import heapq
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict

from .logic_chain import LogicChain
from .uid_system import UIDRegistry


class GraphSearchSystem:
    """图搜索系统"""
    
    def __init__(self, registry: UIDRegistry):
        self.registry = registry
        
        # 图结构：节点UID -> [ (邻居UID, 逻辑链UID, 权重) ]
        self.graph: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        
        # 逻辑链索引
        self.chain_start_index: Dict[str, List[str]] = defaultdict(list)
        self.chain_mediate_index: Dict[str, List[str]] = defaultdict(list)
        self.chain_end_index: Dict[str, List[str]] = defaultdict(list)
        
        # 逻辑链存储：逻辑链ID -> 逻辑链对象
        self.chains: Dict[str, LogicChain] = {}
        
        print("✅ 图搜索系统已启动")
    
    def add_logic_chain(self, logic_chain: LogicChain) -> None:
        """添加逻辑链到图索引"""
        chain_id = logic_chain.id
        
        # 存储逻辑链
        self.chains[chain_id] = logic_chain
        
        # 更新索引
        if logic_chain.start_uid:
            self.chain_start_index[logic_chain.start_uid].append(chain_id)
        
        if logic_chain.mediate_uid:
            self.chain_mediate_index[logic_chain.mediate_uid].append(chain_id)
        
        if logic_chain.end_uid:
            self.chain_end_index[logic_chain.end_uid].append(chain_id)
        
        # 更新图结构
        if logic_chain.start_uid and logic_chain.end_uid:
            # 添加边（从起始到终结）
            weight = 1.0
            # 如果有介导因素，权重可能调整
            if logic_chain.mediate_uid:
                weight = 0.8  # 介导路径可能更间接
            
            self.graph[logic_chain.start_uid].append(
                (logic_chain.end_uid, chain_id, weight)
            )
            
            # 如果是双向关系，也添加反向边
            if logic_chain.is_bidirectional:
                self.graph[logic_chain.end_uid].append(
                    (logic_chain.start_uid, chain_id, weight)
                )
    
    def search_by_pattern(self, start_uid: Optional[str] = None, 
                         mediate_uid: Optional[str] = None,
                         end_uid: Optional[str] = None) -> List[LogicChain]:
        """模式搜索：根据模板查找逻辑链"""
        result_chain_ids = set()
        
        # 根据提供的条件过滤
        if start_uid:
            result_chain_ids.update(self.chain_start_index.get(start_uid, []))
        
        if mediate_uid:
            if result_chain_ids:
                # 取交集
                result_chain_ids.intersection_update(self.chain_mediate_index.get(mediate_uid, []))
            else:
                result_chain_ids.update(self.chain_mediate_index.get(mediate_uid, []))
        
        if end_uid:
            if result_chain_ids:
                result_chain_ids.intersection_update(self.chain_end_index.get(end_uid, []))
            else:
                result_chain_ids.update(self.chain_end_index.get(end_uid, []))
        
        # 转换为逻辑链对象
        return [self.chains[chain_id] for chain_id in result_chain_ids]
    
    def find_path(self, start_uid: str, end_uid: str, 
                  must_pass: Optional[List[str]] = None,
                  avoid: Optional[List[str]] = None,
                  max_depth: int = 10) -> Optional[List[str]]:
        """
        寻路算法：查找从起始到终结的路径
        
        Args:
            start_uid: 起始UID
            end_uid: 终结UID
            must_pass: 必须经过的UID列表
            avoid: 需要避开的UID列表
            max_depth: 最大搜索深度
        """
        # 使用A*算法寻路
        if start_uid not in self.graph or end_uid not in self.graph:
            return None
        
        # 避免列表
        avoid_set = set(avoid or [])
        
        # 优先级队列：(估计总代价, 实际代价, 当前节点, 路径, 经过的必须节点)
        heap = [(0, 0, start_uid, [start_uid], set())]
        
        # 已访问节点
        visited = set()
        
        while heap:
            est_total_cost, actual_cost, current, path, passed_must = heapq.heappop(heap)
            
            # 检查是否到达终点
            if current == end_uid:
                # 检查是否经过了所有必须节点
                if must_pass and not all(m in passed_must for m in must_pass):
                    continue
                return path
            
            # 如果已访问过，跳过
            if current in visited:
                continue
            
            visited.add(current)
            
            # 如果路径太长，跳过
            if len(path) > max_depth:
                continue
            
            # 探索邻居
            for neighbor, chain_id, weight in self.graph.get(current, []):
                # 检查是否要避开
                if neighbor in avoid_set:
                    continue
                
                # 计算新代价
                new_cost = actual_cost + weight
                
                # 计算启发式代价（到终点的估计距离）
                heuristic = self._calculate_heuristic(neighbor, end_uid)
                
                # 更新必须经过的节点集合
                new_passed_must = passed_must.copy()
                if must_pass and neighbor in must_pass:
                    new_passed_must.add(neighbor)
                
                # 将新状态加入堆
                heapq.heappush(heap, (
                    new_cost + heuristic,
                    new_cost,
                    neighbor,
                    path + [neighbor],
                    new_passed_must
                ))
        
        return None
    
    def _calculate_heuristic(self, node: str, target: str) -> float:
        """计算启发式代价（简化版）"""
        # 在实际系统中，可以使用更复杂的启发式函数
        # 这里使用1.0作为基础代价
        return 1.0
    
    def find_all_paths(self, start_uid: str, end_uid: str, 
                       max_paths: int = 5, max_depth: int = 6) -> List[List[str]]:
        """查找所有路径"""
        all_paths = []
        
        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current == end_uid:
                all_paths.append(path.copy())
                return
            
            if len(all_paths) >= max_paths:
                return
            
            for neighbor, _, _ in self.graph.get(current, []):
                if neighbor not in path:  # 避免循环
                    dfs(neighbor, path + [neighbor], depth + 1)
        
        dfs(start_uid, [start_uid], 0)
        return all_paths
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图统计信息"""
        node_count = len(self.graph)
        edge_count = sum(len(neighbors) for neighbors in self.graph.values())
        chain_count = len(self.chains)
        
        return {
            "节点数": node_count,
            "边数": edge_count,
            "逻辑链数": chain_count,
            "起始索引大小": len(self.chain_start_index),
            "介导索引大小": len(self.chain_mediate_index),
            "终结索引大小": len(self.chain_end_index),
        }