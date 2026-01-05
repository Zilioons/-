import os
import time
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AutoCleaner:
    def __init__(self, config: dict):
        self.config = config
        self.running = False
        self.cleaner_thread = None
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.cleaner_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleaner_thread.start()
        logger.info("自动清理器已启动")
    
    def stop(self):
        self.running = False
        if self.cleaner_thread:
            self.cleaner_thread.join(timeout=2.0)
        logger.info("自动清理器已停止")
    
    def _cleanup_loop(self):
        while self.running:
            try:
                self._clean_temp_files()
            except Exception as e:
                logger.error(f"清理循环错误: {e}")
            
            time.sleep(self.config.get('cleanup_interval', 300))
    
    def _clean_temp_files(self):
        try:
            from ..core.constants import SystemPaths
            
            temp_dir = os.path.join(SystemPaths.ROOT, "temp")
            if not os.path.exists(temp_dir):
                return
            
            retention_time = self.config.get('retention_rules', {}).get('temp_files', 600)
            cutoff_time = time.time() - retention_time
            
            files_cleaned = 0
            for filepath in Path(temp_dir).iterdir():
                if filepath.is_file():
                    try:
                        mtime = filepath.stat().st_mtime
                        if mtime < cutoff_time:
                            filepath.unlink()
                            files_cleaned += 1
                    except Exception as e:
                        logger.warning(f"无法清理文件 {filepath}: {e}")
            
            if files_cleaned > 0:
                logger.info(f"清理了 {files_cleaned} 个临时文件")
                
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")