"""
知识系统 v2.0 - 完整的知识管理和推理系统
"""

from .core import KnowledgeSystem
from .uid_system import UIDRegistry, UIDSequence, UIDType
from .cursor_system import CursorSystem, CursorState
from .search_system import GraphSearchSystem
from .logic_chain import LogicChain, LogicChainParser
from .file_manager import FileManager

__version__ = "2.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "KnowledgeSystem",
    "UIDRegistry",
    "UIDSequence",
    "UIDType",
    "CursorSystem",
    "CursorState",
    "GraphSearchSystem",
    "LogicChain",
    "LogicChainParser",
    "FileManager",
]