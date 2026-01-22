"""
主程序 - 系统启动和协调
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.system.monitor import TriggerMonitor
from src.system.executor import InstructionExecutor
from src.core.constants import PROJECT_ROOT

def setup_logging():
    """设置日志系统"""
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_dir / "system.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

class CognitiveArchitectureSystem:
    """认知架构系统主类"""
    
    def __init__(self):
        self.monitor = None
        self.executor = None
        self.running = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """初始化系统"""
        logging.info("=" * 60)
        logging.info("认知架构系统 - 启动初始化")
        logging.info("=" * 60)
        
        # 创建必要的目录
        self._create_directories()
        
        # 初始化组件
        self.executor = InstructionExecutor()
        
        self.monitor = TriggerMonitor()
        self.monitor.set_callback(self._handle_trigger)
        
        logging.info("系统初始化完成")
    
    def _create_directories(self):
        """创建系统所需目录"""
        directories = [
            PROJECT_ROOT / "triggers",
            PROJECT_ROOT / "documents",
            PROJECT_ROOT / "operations",
            PROJECT_ROOT / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logging.info(f"创建/确认目录: {directory}")
    
    def _handle_trigger(self, unit_path: str, cursor_path: str):
        """
        处理触发回调
        
        Args:
            unit_path: 触发单元路径
            cursor_path: 光标文件路径
        """
        logging.info(f"处理触发: 单元={unit_path}, 光标={cursor_path}")
        
        # 执行指令
        success = self.executor.execute_from_trigger(unit_path, cursor_path)
        
        if success:
            # 清空触发文件，准备下一次触发
            self.monitor.clear_trigger_file(unit_path)
            logging.info(f"触发处理完成: {unit_path}")
        else:
            logging.error(f"触发处理失败: {unit_path}")
    
    def start(self):
        """启动系统"""
        if self.running:
            logging.warning("系统已经在运行")
            return
        
        logging.info("启动系统组件...")
        
        # 启动监控器
        self.monitor.start()
        
        # 创建示例触发单元用于测试
        self._create_example_units()
        
        self.running = True
        logging.info("系统已启动，按 Ctrl+C 停止")
        
        # 保持主线程运行
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止系统"""
        if not self.running:
            return
        
        logging.info("停止系统...")
        
        # 停止监控器
        if self.monitor:
            self.monitor.stop()
        
        self.running = False
        logging.info("系统已停止")
    
    def _create_example_units(self):
        """创建示例触发单元"""
        try:
            # 创建示例文档
            docs_dir = PROJECT_ROOT / "documents"
            example_doc = docs_dir / "example.txt"
            
            example_content = """这是一个示例文档。
用于测试系统的搜索和操作功能。
搜索示例：可以搜索"示例"这个词。
复制示例：10 20 /documents/target.txt 5 ;
删除示例：30 40 ;
搜索指令：SEARCH 示例 5000 /operations/search_result.txt
局部搜索：LOCAL_SEARCH DOCUMENT:/documents/example.txt SPACE_INDEX:0 DIRECTION:RIGHT RIGHT 1 示例 /operations/local_result.txt
"""
            
            with open(example_doc, 'w', encoding='utf-8') as f:
                f.write(example_content)
            
            logging.info(f"创建示例文档: {example_doc}")
            
            # 创建示例触发单元
            unit_path = self.monitor.create_trigger_unit("test_unit")
            
            # 创建光标文件
            cursor_file = Path(unit_path) / "cursor.txt"
            cursor_content = "DOCUMENT:/documents/example.txt SPACE_INDEX:0 DIRECTION:RIGHT"
            
            with open(cursor_file, 'w', encoding='utf-8') as f:
                f.write(cursor_content)
            
            # 创建触发文件（空）
            trigger_file = Path(unit_path) / "trigger.txt"
            trigger_file.touch()
            
            logging.info(f"创建示例触发单元: {unit_path}")
            
            # 创建目标文件
            target_doc = docs_dir / "target.txt"
            target_doc.touch()  # 创建空文件
            
            logging.info("示例设置完成。要测试系统，请在触发文件中写入任意内容。")
            
        except Exception as e:
            logging.error(f"创建示例单元失败: {e}")
    
    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        logging.info(f"接收到信号 {signum}, 正在停止系统...")
        self.stop()
        sys.exit(0)

def main():
    """主函数"""
    setup_logging()
    
    system = CognitiveArchitectureSystem()
    
    try:
        system.initialize()
        system.start()
    except Exception as e:
        logging.error(f"系统错误: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())