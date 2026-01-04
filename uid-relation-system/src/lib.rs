//! UID关系系统 - 基于关系网络的动态类型系统
//!
//! 核心概念:
//! 1. 所有数据都存储为UID序列
//! 2. 类型通过关系链动态定义
//! 3. 位置基于锚点和关系
//! 4. 序列是逻辑环形的

pub mod core;
pub mod error;

// 预导出常用类型
pub use crate::core::types::{
    UID, Direction, RelationalPosition, LogicOffset, 
    SequenceVersion, SystemError, FallbackStrategy, ErrorLevel
};
pub use crate::error::{CoreError, make_error_sequence};

/// 系统版本信息
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// 初始化日志系统
pub fn init_logger() {
    env_logger::init();
}

// 在src/lib.rs中添加：

/// 初始化整个系统
pub fn initialize() -> Result<(), Box<dyn std::error::Error>> {
    // 初始化日志
    init_logger();
    
    // 初始化核心系统
    core::initialize_core_system()?;
    
    log::info!("UID Relation System v{} initialized", VERSION);
    Ok(())
}

/// 获取系统状态
pub fn system_status() -> core::SystemInfo {
    core::system_info()
}