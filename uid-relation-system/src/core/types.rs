//! 核心类型定义

use serde::{Deserialize, Serialize};
use std::fmt;

/// 64位全局唯一标识符
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct UID(pub u64);

impl fmt::Display for UID {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "0x{:016x}", self.0)
    }
}

impl From<u64> for UID {
    fn from(value: u64) -> Self {
        Self(value)
    }
}

impl From<UID> for u64 {
    fn from(uid: UID) -> Self {
        uid.0
    }
}

/// 关系方向
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Direction {
    /// 左侧（在环形序列中，左指向前一个元素）
    Left,
    /// 右侧（在环形序列中，右指向后一个元素）
    Right,
    /// 在锚点之前（线性视图）
    Before,
    /// 在锚点之后（线性视图）
    After,
}

/// 关系位置表示
/// (锚点UID, 方向, 距离)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RelationalPosition {
    pub anchor_uid: UID,
    pub direction: Direction,
    pub distance: i64,  // 可以为负值
}

impl RelationalPosition {
    /// 创建一个起始位置
    pub fn start() -> Self {
        Self {
            anchor_uid: UID(0),  // 0表示序列起始
            direction: Direction::Right,
            distance: 0,
        }
    }
    
    /// 创建一个从特定锚点开始的位置
    pub fn from_anchor(anchor_uid: UID) -> Self {
        Self {
            anchor_uid,
            direction: Direction::Right,
            distance: 0,
        }
    }
}

/// 逻辑偏移表示
/// 用于实现虚拟环形序列
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct LogicOffset {
    /// 逻辑时间戳（插入时分配，永不回收）
    pub logical_timestamp: u64,
    /// 当前物理位置（可能因插入删除而变化）
    pub physical_position: usize,
    /// 是否已删除
    pub deleted: bool,
}

/// 序列版本号
/// 每次修改递增
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct SequenceVersion(pub u32);

/// 系统级错误码
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SystemError {
    /// 未找到指定UID
    UIDNotFound(UID),
    /// 位置无效
    InvalidPosition,
    /// 序列版本不匹配
    VersionMismatch,
    /// 锚点不存在
    AnchorNotFound(UID),
    /// 操作不支持
    OperationNotSupported,
    /// 存储错误
    StorageError,
    /// 解析错误
    ParseError,
}

/// 回滚策略
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FallbackStrategy {
    /// 重新计算位置
    Recalculate,
    /// 使用快照
    UseSnapshot,
    /// 返回错误
    Error,
}

/// 错误级别
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ErrorLevel {
    /// 致命错误，系统无法继续
    Fatal,
    /// 严重错误，需要用户干预
    Severe,
    /// 警告，操作部分成功
    Warning,
    /// 信息性消息
    Info,
}