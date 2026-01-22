"""
文件监控系统
监控触发文件夹，检测状态变化
"""

import os
import time
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable

from ..core.constants import PROJECT_ROOT

logger = logging.getLogger(__name__)

class TriggerMonitor:
    """触发监控器"""
    
    def __init__(self, triggers_dir: str = None):
        """
        初始化监控器
        
        Args:
            triggers_dir: 触发目录路径
        """
        if triggers_dir is None:
            triggers_dir = str(PROJECT_ROOT / "triggers")
        
        self.triggers_dir = Path(triggers_dir)
        self.trigger_file_name = "trigger.txt"
        self.cursor_file_name = "cursor.txt"
        
        # 确保目录存在
        self.triggers_dir.mkdir(parents=True, exist_ok=True)
        
        # 状态跟踪
        self.last_states: Dict[str, str] = {}  # 路径 -> 状态 ("empty" 或 "non_empty")
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 回调函数
        self.on_trigger_callback: Optional[Callable] = None
        
        logger.info(f"初始化触发监控器，监控目录: {self.triggers_dir}")
    
    def set_callback(self, callback: Callable):
        """
        设置触发回调函数
        
        Args:
            callback: 回调函数，接收参数 (unit_path, cursor_path)
        """
        self.on_trigger_callback = callback
    
    def start(self):
        """启动监控"""
        if self.running:
            logger.warning("监控器已经在运行")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("触发监控器已启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None
        logger.info("触发监控器已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        logger.debug("开始监控循环")
        
        # 初始扫描，记录当前状态
        self._scan_initial_states()
        
        while self.running:
            try:
                self._check_triggers()
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
            
            # 等待下一次检查
            time.sleep(0.1)  # 100ms
    
    def _scan_initial_states(self):
        """扫描初始状态"""
        if not self.triggers_dir.exists():
            return
        
        for unit_dir in self.triggers_dir.iterdir():
            if unit_dir.is_dir():
                trigger_file = unit_dir / self.trigger_file_name
                state = self._get_file_state(trigger_file)
                self.last_states[str(trigger_file)] = state
        
        logger.debug(f"扫描了 {len(self.last_states)} 个触发文件的状态")
    
    def _check_triggers(self):
        """检查所有触发单元"""
        if not self.triggers_dir.exists():
            return
        
        # 获取所有触发单元目录
        unit_dirs = [d for d in self.triggers_dir.iterdir() if d.is_dir()]
        
        for unit_dir in unit_dirs:
            self._check_unit(unit_dir)
    
    def _check_unit(self, unit_dir: Path):
        """检查单个触发单元"""
        trigger_file = unit_dir / self.trigger_file_name
        cursor_file = unit_dir / self.cursor_file_name
        
        # 获取当前状态
        current_state = self._get_file_state(trigger_file)
        last_state = self.last_states.get(str(trigger_file), "not_exist")
        
        # 检查状态变化：从空变为非空
        if last_state == "empty" and current_state == "non_empty":
            logger.info(f"检测到触发: {unit_dir.name}")
            
            # 验证光标文件存在
            if not cursor_file.exists():
                logger.warning(f"触发单元 {unit_dir.name} 缺少光标文件")
                return
            
            # 调用回调函数
            if self.on_trigger_callback:
                try:
                    self.on_trigger_callback(str(unit_dir), str(cursor_file))
                except Exception as e:
                    logger.error(f"触发回调函数出错: {e}")
        
        # 更新状态记录
        self.last_states[str(trigger_file)] = current_state
    
    def _get_file_state(self, file_path: Path) -> str:
        """
        获取文件状态
        
        Returns:
            "not_exist": 文件不存在
            "empty": 文件存在但为空
            "non_empty": 文件存在且有内容
        """
        if not file_path.exists():
            return "not_exist"
        
        try:
            size = file_path.stat().st_size
            return "non_empty" if size > 0 else "empty"
        except Exception:
            return "not_exist"
    
    def create_trigger_unit(self, unit_name: str) -> str:
        """
        创建触发单元
        
        Returns:
            触发单元目录路径
        """
        unit_dir = self.triggers_dir / unit_name
        unit_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建触发文件（空）
        trigger_file = unit_dir / self.trigger_file_name
        trigger_file.touch()
        
        # 创建光标目录和文件
        cursor_file = unit_dir / self.cursor_file_name
        cursor_file.touch()
        
        # 初始状态记录
        self.last_states[str(trigger_file)] = "empty"
        
        logger.info(f"创建触发单元: {unit_name}")
        return str(unit_dir)
    
    def clear_trigger_file(self, unit_path: str):
        """清空触发文件内容"""
        trigger_file = Path(unit_path) / self.trigger_file_name
        
        if trigger_file.exists():
            try:
                # 清空文件内容
                trigger_file.write_text("")
                logger.debug(f"已清空触发文件: {trigger_file}")
            except Exception as e:
                logger.error(f"清空触发文件失败: {e}")