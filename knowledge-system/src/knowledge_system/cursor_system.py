# src/knowledge_system/cursor_system.py
"""
状态光标系统模块
用于在UID序列中导航和标记位置
"""

import time
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

from .uid_system import UIDRegistry, UIDSequence


class CursorState(Enum):
    """光标状态枚举"""
    NORMAL = "正常"
    CURSOR_LEFT = "←左侧"
    CURSOR_RIGHT = "右侧→"
    SELECTED = "【选中】"
    INSIDE_CURSOR = "█光标内"
    SEARCH_RESULT = "🔍结果"
    PATH_NODE = "🟢路径点"


class CursorSystem:
    """状态光标系统"""
    
    def __init__(self, registry: UIDRegistry):
        self.registry = registry
        self._sequence_states: Dict[str, Dict[int, List[CursorState]]] = {}
        self.current_sequence_id: Optional[str] = None
        self.cursor_position: int = 0
        self.selection_start: Optional[int] = None
        self.selection_end: Optional[int] = None
        self._state_locations: Dict[CursorState, Tuple[str, int]] = {}
        self._history: List[Dict] = []
        
        print("✅ 状态光标系统已启动")
    
    def set_current_sequence(self, sequence: UIDSequence) -> None:
        """设置当前序列"""
        self.current_sequence_id = sequence.id
        
        if sequence.id not in self._sequence_states:
            self._sequence_states[sequence.id] = {}
        
        self.cursor_position = 0
        self._update_cursor_states(sequence)
        
        print(f"📁 切换到序列：{sequence.name}")
    
    def _update_cursor_states(self, sequence: UIDSequence):
        """更新光标状态"""
        if not self.current_sequence_id:
            return
        
        seq_id = self.current_sequence_id
        
        # 清除旧的唯一状态
        for state in [CursorState.CURSOR_LEFT, CursorState.CURSOR_RIGHT, CursorState.INSIDE_CURSOR]:
            if state in self._state_locations:
                old_seq_id, old_idx = self._state_locations[state]
                if old_seq_id in self._sequence_states and old_idx in self._sequence_states[old_seq_id]:
                    if state in self._sequence_states[old_seq_id][old_idx]:
                        self._sequence_states[old_seq_id][old_idx].remove(state)
        
        # 设置新状态
        if 0 <= self.cursor_position < len(sequence):
            if self.cursor_position > 0:
                self._set_state(seq_id, self.cursor_position - 1, CursorState.CURSOR_LEFT)
            
            self._set_state(seq_id, self.cursor_position, CursorState.INSIDE_CURSOR)
            
            if self.cursor_position < len(sequence) - 1:
                self._set_state(seq_id, self.cursor_position + 1, CursorState.CURSOR_RIGHT)
    
    def _set_state(self, seq_id: str, index: int, state: CursorState):
        """设置状态"""
        if seq_id not in self._sequence_states:
            self._sequence_states[seq_id] = {}
        
        if index not in self._sequence_states[seq_id]:
            self._sequence_states[seq_id][index] = []
        
        if state not in self._sequence_states[seq_id][index]:
            self._sequence_states[seq_id][index].append(state)
        
        # 记录唯一状态位置
        if state in [CursorState.CURSOR_LEFT, CursorState.CURSOR_RIGHT, 
                    CursorState.INSIDE_CURSOR, CursorState.SEARCH_RESULT]:
            self._state_locations[state] = (seq_id, index)
    
    def MOVE_TO(self, position: int, relative: bool = False) -> bool:
        """移动光标"""
        if not self.current_sequence_id:
            print("❌ 请先设置当前序列")
            return False
        
        # 计算目标位置
        if relative:
            target = self.cursor_position + position
        else:
            target = position
        
        # 边界检查
        if target < 0:
            target = 0
        elif target >= len(self._get_current_sequence()):
            target = max(0, len(self._get_current_sequence()) - 1)
        
        # 更新位置
        old_pos = self.cursor_position
        self.cursor_position = target
        
        # 更新状态
        self._update_cursor_states(self._get_current_sequence())
        
        # 显示信息
        if 0 <= target < len(self._get_current_sequence()):
            uid = self._get_current_sequence()[target]
            entity = self.registry.get_entity(uid)
            name = entity.name if entity else "未知"
            print(f"📍 光标已移动：{old_pos} → {target} ({name})")
        
        return True
    
    def JUMP_TO(self, target: Union[str, int], sequence_id: Optional[str] = None) -> bool:
        """跳转到指定位置"""
        # 跨序列跳转
        if sequence_id and sequence_id != self.current_sequence_id:
            print(f"🔄 尝试跳转到序列：{sequence_id}")
            return False
        
        # 跳转到UID
        if isinstance(target, str):
            seq = self._get_current_sequence()
            if not seq:
                return False
            
            try:
                pos = seq.uids.index(target)
                return self.MOVE_TO(pos)
            except ValueError:
                print(f"❌ UID不在当前序列中")
                return False
        
        # 跳转到索引
        elif isinstance(target, int):
            return self.MOVE_TO(target)
        
        return False
    
    def SELECT(self, start: Optional[int] = None, end: Optional[int] = None) -> bool:
        """选中范围"""
        if not self.current_sequence_id:
            return False
        
        seq = self._get_current_sequence()
        if not seq:
            return False
        
        # 确定范围
        if start is None:
            start = self.cursor_position
        
        if end is None:
            end = start
        else:
            end = min(end, len(seq) - 1)
        
        if start > end:
            start, end = end, start
        
        # 清除旧选中
        self._clear_all_selected()
        
        # 设置新选中
        for idx in range(start, end + 1):
            self._set_state(self.current_sequence_id, idx, CursorState.SELECTED)
        
        self.selection_start = start
        self.selection_end = end
        
        # 显示选中内容
        selected = []
        for idx in range(start, end + 1):
            uid = seq[idx]
            entity = self.registry.get_entity(uid)
            selected.append(entity.name if entity else uid)
        
        print(f"✅ 已选中：位置 {start}-{end}")
        print(f"   内容：{'、'.join(selected[:3])}" + 
              (f"...等{len(selected)}项" if len(selected) > 3 else ""))
        
        return True
    
    def MARK_SEARCH_RESULT(self, positions: List[int]) -> None:
        """标记搜索结果"""
        if not self.current_sequence_id:
            return
        
        # 清除旧的搜索结果标记
        for seq_id in self._sequence_states:
            for idx in list(self._sequence_states[seq_id].keys()):
                if CursorState.SEARCH_RESULT in self._sequence_states[seq_id][idx]:
                    self._sequence_states[seq_id][idx].remove(CursorState.SEARCH_RESULT)
                    if not self._sequence_states[seq_id][idx]:
                        del self._sequence_states[seq_id][idx]
        
        # 标记新结果
        for pos in positions:
            if 0 <= pos < len(self._get_current_sequence()):
                self._set_state(self.current_sequence_id, pos, CursorState.SEARCH_RESULT)
    
    def SHOW(self, sequence: Optional[UIDSequence] = None) -> None:
        """显示序列状态"""
        if sequence is None:
            sequence = self._get_current_sequence()
            if not sequence:
                print("❌ 没有可显示的序列")
                return
        
        seq_id = sequence.id
        states = self._sequence_states.get(seq_id, {})
        
        print(f"\n📊 {sequence.name} 状态视图")
        print("=" * 70)
        
        for idx, uid in enumerate(sequence.uids):
            # 获取实体信息
            entity = self.registry.get_entity(uid)
            if entity:
                if entity.metadata.get("is_special", False):
                    display_name = f"「{entity.name}」"  # 特殊符号
                else:
                    display_name = entity.name
            else:
                display_name = f"[{uid[:8]}]"
            
            # 光标指示
            cursor_mark = "👆" if idx == self.cursor_position else "  "
            
            # 状态标记
            state_markers = []
            if idx in states:
                for state in states[idx]:
                    state_markers.append(state.value)
            
            state_str = "、".join(state_markers) if state_markers else "正常"
            
            # 显示行
            print(f"[{idx:3d}] {cursor_mark} {display_name:15} | 状态：{state_str}")
        
        print("=" * 70)
        print(f"统计：共{len(sequence)}个元素，光标位置：{self.cursor_position}")
    
    def _clear_all_selected(self):
        """清除所有选中"""
        if not self.current_sequence_id:
            return
        
        seq_id = self.current_sequence_id
        if seq_id in self._sequence_states:
            for idx in list(self._sequence_states[seq_id].keys()):
                if CursorState.SELECTED in self._sequence_states[seq_id][idx]:
                    self._sequence_states[seq_id][idx].remove(CursorState.SELECTED)
                    if not self._sequence_states[seq_id][idx]:
                        del self._sequence_states[seq_id][idx]
        
        self.selection_start = None
        self.selection_end = None
    
    def _get_current_sequence(self):
        """获取当前序列（简化）"""
        # 在实际系统中，这里应该从文件管理器获取
        return None