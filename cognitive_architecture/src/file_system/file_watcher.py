import os
import time
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileWatcher:
    def __init__(self, watch_dir: str, poll_interval_ms: int = 1000):
        self.watch_dir = Path(watch_dir)
        self.poll_interval = poll_interval_ms / 1000.0
        self.handlers = {}
        self.running = False
        self.watcher_thread = None
        
        self.watch_dir.mkdir(parents=True, exist_ok=True)
    
    def register_handler(self, file_pattern: str, handler):
        self.handlers[file_pattern] = handler
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()
        logger.info(f"文件监视器已启动: {self.watch_dir}")
    
    def stop(self):
        self.running = False
        if self.watcher_thread:
            self.watcher_thread.join(timeout=2.0)
        logger.info(f"文件监视器已停止: {self.watch_dir}")
    
    def _watch_loop(self):
        while self.running:
            try:
                if self.watch_dir.exists():
                    for filepath in self.watch_dir.iterdir():
                        if filepath.is_file():
                            self._process_file(filepath)
            except Exception as e:
                logger.error(f"文件监视错误: {e}")
            
            time.sleep(self.poll_interval)
    
    def _process_file(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = filepath.name
            logger.info(f"处理文件: {filename}")
            
            # 查找处理函数
            for pattern, handler in self.handlers.items():
                if self._match_pattern(filename, pattern):
                    success = handler(str(filepath), content)
                    if success:
                        filepath.unlink()
                        logger.debug(f"文件处理成功，已删除: {filename}")
                    else:
                        logger.warning(f"文件处理失败: {filename}")
                    return
            
            logger.warning(f"没有找到处理函数: {filename}")
            
        except Exception as e:
            logger.error(f"处理文件失败 {filepath}: {e}")
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        elif pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1] in filename
        elif pattern.startswith("*"):
            return filename.endswith(pattern[1:])
        elif pattern.endswith("*"):
            return filename.startswith(pattern[:-1])
        else:
            return filename == pattern