import os
import yaml
import logging

logger = logging.getLogger(__name__)

class DirectoryManager:
    def __init__(self, config_path: str = "config/system_config.yaml"):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def initialize_system(self) -> bool:
        try:
            system_root = self.config['system_root']
            os.makedirs(system_root, exist_ok=True)
            
            # 创建所有需要的目录
            directories = [
                os.path.join(system_root, "uid_system", "inbox"),
                os.path.join(system_root, "uid_system", "outbox"),
                os.path.join(system_root, "uid_system", "registry"),
                os.path.join(system_root, "uid_system", "errors"),
                os.path.join(system_root, "instruction_system", "inbox"),
                os.path.join(system_root, "instruction_system", "cursors"),
                os.path.join(system_root, "instruction_system", "selections"),
                os.path.join(system_root, "instruction_system", "clipboard"),
                os.path.join(system_root, "instruction_system", "results"),
                os.path.join(system_root, "instruction_system", "errors"),
                os.path.join(system_root, "documents", "default"),
                os.path.join(system_root, "temp"),
                os.path.join(system_root, "logs"),
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"目录已创建: {directory}")
            
            logger.info("系统目录初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"目录初始化失败: {e}")
            return False
    
    def get_config(self):
        return self.config