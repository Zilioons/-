import os
import sys
import time
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.file_system.directory_manager import DirectoryManager
from src.file_system.file_watcher import FileWatcher
from src.file_system.cleaner import AutoCleaner

from src.uid_system.query_processor import QueryProcessor
from src.instruction_system.cursor_manager import CursorManager
from src.instruction_system.executor import InstructionExecutor

from src.core.uid_generator import uid_generator

# 设置日志
def setup_logging():
    log_dir = project_root / "system_root" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "system.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

class CognitiveArchitectureSystem:
    def __init__(self, config_path: str = "config/system_config.yaml"):
        self.config_path = config_path
        self.config = None
        self.directory_manager = None
        self.query_processor = None
        self.cursor_manager = None
        self.instruction_executor = None
        self.file_watchers = {}
        self.cleaner = None
        self.running = False
        
        import signal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger = logging.getLogger(__name__)
        logger.info("系统初始化开始")
    
    def initialize(self) -> bool:
        try:
            logger = logging.getLogger(__name__)
            
            logger.info("=" * 60)
            logger.info("认知架构系统 - 简化版")
            logger.info("=" * 60)
            
            # 1. 初始化目录管理器
            logger.info("步骤1: 初始化目录管理器...")
            self.directory_manager = DirectoryManager(self.config_path)
            
            if not self.directory_manager.initialize_system():
                logger.error("目录管理器初始化失败")
                return False
            
            # 获取配置
            self.config = self.directory_manager.get_config()
            
            # 2. 初始化UID系统
            logger.info("步骤2: 初始化UID系统...")
            self.query_processor = QueryProcessor(self.config)
            
            # 3. 初始化指令系统
            logger.info("步骤3: 初始化指令系统...")
            
            # 光标管理器
            cursor_dir = os.path.join(self.config['system_root'], "instruction_system", "cursors")
            self.cursor_manager = CursorManager(cursor_dir)
            
            # 指令执行器
            self.instruction_executor = InstructionExecutor(
                self.config,
                self.cursor_manager,
                self.query_processor
            )
            
            # 4. 初始化文件监视器
            logger.info("步骤4: 初始化文件监视器...")
            self._initialize_watchers()
            
            # 5. 初始化清理器
            logger.info("步骤5: 初始化自动清理器...")
            self.cleaner = AutoCleaner(self.config['cleaner'])
            
            logger.info("系统初始化完成!")
            return True
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"系统初始化失败: {e}", exc_info=True)
            return False
    
    def _initialize_watchers(self):
        watcher_config = self.config['file_watcher']
        
        # UID系统监视器
        uid_inbox = os.path.join(self.config['system_root'], "uid_system", "inbox")
        self.file_watchers['uid_system'] = FileWatcher(
            watch_dir=uid_inbox,
            poll_interval_ms=watcher_config['poll_interval_ms']
        )
        
        self.file_watchers['uid_system'].register_handler(
            "*.uid", 
            self._handle_uid_query
        )
        
        # 指令系统监视器
        instruction_inbox = os.path.join(self.config['system_root'], "instruction_system", "inbox")
        self.file_watchers['instruction_system'] = FileWatcher(
            watch_dir=instruction_inbox,
            poll_interval_ms=watcher_config['poll_interval_ms']
        )
        
        self.file_watchers['instruction_system'].register_handler(
            "*.uid",
            self._handle_instruction
        )
    
    def start(self):
        if self.running:
            logger = logging.getLogger(__name__)
            logger.warning("系统已经在运行")
            return
        
        logger = logging.getLogger(__name__)
        logger.info("启动系统组件...")
        
        # 启动文件监视器
        for name, watcher in self.file_watchers.items():
            watcher.start()
            logger.info(f"已启动 {name} 文件监视器")
        
        # 启动清理器
        self.cleaner.start()
        logger.info("已启动自动清理器")
        
        self.running = True
        
        # 创建示例文件
        self._create_example_files()
        
        # 显示系统状态
        self._show_system_status()
        
        logger.info("系统已启动，按 Ctrl+C 停止")
        logger.info("-" * 60)
        logger.info("使用说明:")
        logger.info("  1. 将查询任务文件放入 system_root/uid_system/inbox/")
        logger.info("  2. 将指令文件放入 system_root/instruction_system/inbox/")
        logger.info("  3. 查看结果在对应的outbox目录中")
        logger.info("-" * 60)
        
        # 保持运行
        try:
            while self.running:
                time.sleep(1)
                
                # 定期显示状态（每分钟）
                if int(time.time()) % 60 == 0:
                    self._show_system_status(brief=True)
                    
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        if not self.running:
            return
        
        logger = logging.getLogger(__name__)
        logger.info("停止系统组件...")
        
        # 停止清理器
        if self.cleaner:
            self.cleaner.stop()
        
        # 停止文件监视器
        for name, watcher in self.file_watchers.items():
            watcher.stop()
            logger.info(f"已停止 {name} 文件监视器")
        
        self.running = False
        logger.info("系统已停止")
    
    def _handle_uid_query(self, filepath: str, content: str) -> bool:
        logger = logging.getLogger(__name__)
        logger.info(f"处理UID查询文件: {os.path.basename(filepath)}")
        
        try:
            result_file = self.query_processor.process_query(content)
            
            if result_file and os.path.exists(result_file):
                logger.info(f"查询处理完成，结果保存到: {os.path.basename(result_file)}")
                return True
            else:
                logger.error("查询处理失败")
                return False
                
        except Exception as e:
            logger.error(f"处理UID查询失败: {e}")
            return False
    
    def _handle_instruction(self, filepath: str, content: str) -> bool:
        logger = logging.getLogger(__name__)
        logger.info(f"处理指令文件: {os.path.basename(filepath)}")
        
        try:
            result = self.instruction_executor.execute_instruction(content)
            
            if result.get("status") == "SUCCESS":
                logger.info(f"指令执行成功: {result.get('message', '完成')}")
                
                # 显示详细信息
                if "cursor_id" in result:
                    cursor = self.cursor_manager.get_cursor(result["cursor_id"])
                    if cursor:
                        logger.debug(f"  光标位置: {cursor['position']}")
                
                if "result_file" in result:
                    logger.debug(f"  结果文件: {result['result_file']}")
                
            else:
                logger.error(f"指令执行失败: {result.get('error', '未知错误')}")
            
            return result.get("status") == "SUCCESS"
            
        except Exception as e:
            logger.error(f"处理指令失败: {e}")
            return False
    
    def _create_example_files(self):
        logger = logging.getLogger(__name__)
        
        try:
            # 1. 创建示例文档
            documents_dir = os.path.join(self.config['system_root'], "documents", "default")
            os.makedirs(documents_dir, exist_ok=True)
            
            example_doc = os.path.join(documents_dir, "example.txt")
            if not os.path.exists(example_doc):
                content = """这是一个示例文档。
包含一些UID引用: UID_ALPHA, UID_BETA, UID_GAMMA。
和一些普通文本: Hello World。
"""
                with open(example_doc, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"示例文档已创建: {example_doc}")
            
            # 2. 创建示例查询任务
            uid_inbox = os.path.join(self.config['system_root'], "uid_system", "inbox")
            
            example_queries = [
                ("FIND_CHAR UID_ALPHA", "query_find_char_alpha.uid"),
                ("FIND_UID \"苹果\"", "query_find_uid_apple.uid"),
                ("FIND_CHAR UID_NOT_EXIST", "query_find_char_nonexist.uid")
            ]
            
            for content, filename in example_queries:
                filepath = os.path.join(uid_inbox, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            logger.info(f"已创建 {len(example_queries)} 个示例查询任务")
            
            # 3. 创建示例指令
            instruction_inbox = os.path.join(self.config['system_root'], "instruction_system", "inbox")
            
            # 获取主光标ID
            main_cursor = None
            for cursor in self.cursor_manager.cursors.values():
                if cursor.get("name") == "main":
                    main_cursor = cursor
                    break
            
            if main_cursor:
                main_cursor_id = main_cursor["cursor_id"]
            else:
                main_cursor_id = self.cursor_manager.create_cursor(name="main")
            
            # 创建另一个光标
            secondary_cursor_id = self.cursor_manager.create_cursor(name="secondary", position=50)
            
            example_instructions = [
                (f"MOVE_CURSOR {main_cursor_id} RIGHT 10", "cmd_move_right.uid"),
                (f"CREATE_CURSOR 100", "cmd_create_cursor.uid"),
                (f"FIND_CHAR UID_ALPHA", "cmd_find_char.uid"),
                (f"FIND_UID \"苹果\"", "cmd_find_uid.uid")
            ]
            
            for content, filename in example_instructions:
                filepath = os.path.join(instruction_inbox, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            logger.info(f"已创建 {len(example_instructions)} 个示例指令")
            
        except Exception as e:
            logger.error(f"创建示例文件失败: {e}")
    
    def _show_system_status(self, brief: bool = False):
        logger = logging.getLogger(__name__)
        
        try:
            system_status = self.instruction_executor.get_system_status()
            
            if brief:
                cursors = system_status.get("cursors", {}).get("total_cursors", 0)
                uids = system_status.get("queries", {}).get("total_uids", 0)
                logger.info(f"状态 - 光标: {cursors}, UID: {uids}")
                
            else:
                logger.info("=" * 40)
                logger.info("系统状态报告")
                logger.info("=" * 40)
                
                cursors = system_status.get("cursors", {})
                logger.info(f"光标: {cursors.get('total_cursors', 0)} 个")
                
                queries = system_status.get("queries", {})
                logger.info(f"UID注册表: {queries.get('total_uids', 0)} 个UID")
                
                logger.info("-" * 40)
                
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
    
    def _signal_handler(self, signum, frame):
        logger = logging.getLogger(__name__)
        logger.info(f"接收到信号 {signum}, 正在停止系统...")
        self.stop()
        sys.exit(0)

def main():
    setup_logging()
    
    system = CognitiveArchitectureSystem()
    
    if system.initialize():
        system.start()
    else:
        logger = logging.getLogger(__name__)
        logger.error("系统初始化失败，程序退出")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())