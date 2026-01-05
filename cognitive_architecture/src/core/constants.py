# 核心常量定义
class UIDConstants:
    SYS_PREFIX = "SYS_"
    TASK_PREFIX = "TASK_"
    CURSOR_PREFIX = "CURSOR_"
    RESULT_PREFIX = "RESULT_"
    ERROR_PREFIX = "ERROR_"
    
    # 任务类型
    TASK_SCAN = "TASK_TYPE_SCAN"
    TASK_MATCH = "TASK_TYPE_MATCH"
    TASK_DECOMPILE = "TASK_TYPE_DECOMPILE"
    
    # 状态
    STATUS_SUCCESS = "STATUS_SUCCESS"
    STATUS_ERROR = "STATUS_ERROR"
    STATUS_PROCESSING = "STATUS_PROCESSING"

class SystemPaths:
    ROOT = ""
    
    @classmethod
    def initialize(cls, config):
        cls.ROOT = config['system_root']