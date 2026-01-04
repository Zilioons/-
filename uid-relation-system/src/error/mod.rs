//! 错误处理模块

use crate::core::types::{SystemError, ErrorLevel};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum CoreError {
    #[error("UID未找到: {0:?}")]
    UIDNotFound(crate::core::types::UID),
    
    #[error("位置无效: {0}")]
    InvalidPosition(String),
    
    #[error("序列版本不匹配: 期望{expected}, 实际{actual}")]
    VersionMismatch {
        expected: crate::core::types::SequenceVersion,
        actual: crate::core::types::SequenceVersion,
    },
    
    #[error("锚点未找到: {0:?}")]
    AnchorNotFound(crate::core::types::UID),
    
    #[error("存储错误: {0}")]
    StorageError(#[from] std::io::Error),
    
    #[error("解析错误: {0}")]
    ParseError(String),
    
    #[error("系统错误: {0:?}")]
    SystemError(SystemError),
}

impl From<SystemError> for CoreError {
    fn from(err: SystemError) -> Self {
        CoreError::SystemError(err)
    }
}

/// 生成错误序列
pub fn make_error_sequence(
    level: ErrorLevel,
    error_code: SystemError,
    context: Vec<crate::core::types::UID>,
    details: Vec<crate::core::types::UID>,
) -> Vec<crate::core::types::UID> {
    use crate::core::types::UID;
    
    // 错误序列格式: [ERROR_START, level, error_code, context_len, context..., details...]
    let mut result = Vec::new();
    
    // 这些UID将在后续步骤中定义
    result.push(UID(0xE000000000000001)); // ERROR_START
    result.push(match level {
        ErrorLevel::Fatal => UID(0xE000000000000002),
        ErrorLevel::Severe => UID(0xE000000000000003),
        ErrorLevel::Warning => UID(0xE000000000000004),
        ErrorLevel::Info => UID(0xE000000000000005),
    });
    
    // 错误码转换
    let error_uid = match error_code {
        SystemError::UIDNotFound(uid) => uid,
        SystemError::InvalidPosition => UID(0xE000000000000101),
        SystemError::VersionMismatch => UID(0xE000000000000102),
        SystemError::AnchorNotFound(uid) => uid,
        SystemError::OperationNotSupported => UID(0xE000000000000103),
        SystemError::StorageError => UID(0xE000000000000104),
        SystemError::ParseError => UID(0xE000000000000105),
    };
    result.push(error_uid);
    
    // 上下文长度和内容
    result.push(UID(context.len() as u64));
    result.extend(context);
    result.extend(details);
    
    result
}