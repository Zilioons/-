//! 预定义系统UID常量
//! 
//! 这些UID在系统初始化时注册，确保在整个系统中一致

use crate::core::types::UID;
use crate::core::symbol_map::{register_global_symbol, get_global_uid};

/// 预定义系统UID
/// 
/// 注意：这些是占位符，实际UID在系统初始化时动态生成
/// 使用对应的getter函数获取实际UID

// 关系标记
pub const REL_ROLE_SYMBOL: &str = "REL_ROLE";
pub const REL_CONTEXT_SYMBOL: &str = "REL_CONTEXT";
pub const REL_MEANING_SYMBOL: &str = "REL_MEANING";

// 模式元素
pub const PATTERN_WILDCARD_SYMBOL: &str = "PATTERN_WILDCARD";
pub const PATTERN_WILDCARD_MULTI_SYMBOL: &str = "PATTERN_WILDCARD_MULTI";
pub const PATTERN_SET_START_SYMBOL: &str = "PATTERN_SET_START";
pub const PATTERN_SET_END_SYMBOL: &str = "PATTERN_SET_END";
pub const PATTERN_NOT_SYMBOL: &str = "PATTERN_NOT";
pub const PATTERN_MIN_MAX_SYMBOL: &str = "PATTERN_MIN_MAX";

// 错误码
pub const ERROR_START_SYMBOL: &str = "ERROR_START";
pub const ERROR_FATAL_SYMBOL: &str = "ERROR_FATAL";
pub const ERROR_SEVERE_SYMBOL: &str = "ERROR_SEVERE";
pub const ERROR_WARNING_SYMBOL: &str = "ERROR_WARNING";
pub const ERROR_INFO_SYMBOL: &str = "ERROR_INFO";

// 指令操作码
pub const OP_MOVE_SYMBOL: &str = "OP_MOVE";
pub const OP_INSERT_SYMBOL: &str = "OP_INSERT";
pub const OP_DELETE_SYMBOL: &str = "OP_DELETE";
pub const OP_COPY_SYMBOL: &str = "OP_COPY";
pub const OP_RELATE_SYMBOL: &str = "OP_RELATE";
pub const OP_SEARCH_SYMBOL: &str = "OP_SEARCH";
pub const OP_EXECUTE_SYMBOL: &str = "OP_EXECUTE";

// 特殊标记
pub const ANCHOR_MARKER_SYMBOL: &str = "ANCHOR_MARKER";
pub const START_MARKER_SYMBOL: &str = "START_MARKER";
pub const EXEC_MARKER_SYMBOL: &str = "EXEC_MARKER";
pub const SUCCESS_MARKER_SYMBOL: &str = "SUCCESS";
pub const FAILURE_MARKER_SYMBOL: &str = "FAILURE";

// 获取预定义UID的函数
// 这些函数在第一次调用时初始化UID

/// 获取关系标记UID
pub fn rel_role() -> UID {
    get_global_uid(REL_ROLE_SYMBOL)
        .expect("REL_ROLE should be registered during system initialization")
}

pub fn rel_context() -> UID {
    get_global_uid(REL_CONTEXT_SYMBOL)
        .expect("REL_CONTEXT should be registered during system initialization")
}

pub fn rel_meaning() -> UID {
    get_global_uid(REL_MEANING_SYMBOL)
        .expect("REL_MEANING should be registered during system initialization")
}

/// 获取模式元素UID
pub fn pattern_wildcard() -> UID {
    get_global_uid(PATTERN_WILDCARD_SYMBOL)
        .expect("PATTERN_WILDCARD should be registered during system initialization")
}

pub fn pattern_wildcard_multi() -> UID {
    get_global_uid(PATTERN_WILDCARD_MULTI_SYMBOL)
        .expect("PATTERN_WILDCARD_MULTI should be registered during system initialization")
}

pub fn pattern_set_start() -> UID {
    get_global_uid(PATTERN_SET_START_SYMBOL)
        .expect("PATTERN_SET_START should be registered during system initialization")
}

pub fn pattern_set_end() -> UID {
    get_global_uid(PATTERN_SET_END_SYMBOL)
        .expect("PATTERN_SET_END should be registered during system initialization")
}

pub fn pattern_not() -> UID {
    get_global_uid(PATTERN_NOT_SYMBOL)
        .expect("PATTERN_NOT should be registered during system initialization")
}

pub fn pattern_min_max() -> UID {
    get_global_uid(PATTERN_MIN_MAX_SYMBOL)
        .expect("PATTERN_MIN_MAX should be registered during system initialization")
}

/// 获取错误码UID
pub fn error_start() -> UID {
    get_global_uid(ERROR_START_SYMBOL)
        .expect("ERROR_START should be registered during system initialization")
}

pub fn error_fatal() -> UID {
    get_global_uid(ERROR_FATAL_SYMBOL)
        .expect("ERROR_FATAL should be registered during system initialization")
}

pub fn error_severe() -> UID {
    get_global_uid(ERROR_SEVERE_SYMBOL)
        .expect("ERROR_SEVERE should be registered during system initialization")
}

pub fn error_warning() -> UID {
    get_global_uid(ERROR_WARNING_SYMBOL)
        .expect("ERROR_WARNING should be registered during system initialization")
}

pub fn error_info() -> UID {
    get_global_uid(ERROR_INFO_SYMBOL)
        .expect("ERROR_INFO should be registered during system initialization")
}

/// 获取指令操作码UID
pub fn op_move() -> UID {
    get_global_uid(OP_MOVE_SYMBOL)
        .expect("OP_MOVE should be registered during system initialization")
}

pub fn op_insert() -> UID {
    get_global_uid(OP_INSERT_SYMBOL)
        .expect("OP_INSERT should be registered during system initialization")
}

pub fn op_delete() -> UID {
    get_global_uid(OP_DELETE_SYMBOL)
        .expect("OP_DELETE should be registered during system initialization")
}

pub fn op_copy() -> UID {
    get_global_uid(OP_COPY_SYMBOL)
        .expect("OP_COPY should be registered during system initialization")
}

pub fn op_relate() -> UID {
    get_global_uid(OP_RELATE_SYMBOL)
        .expect("OP_RELATE should be registered during system initialization")
}

pub fn op_search() -> UID {
    get_global_uid(OP_SEARCH_SYMBOL)
        .expect("OP_SEARCH should be registered during system initialization")
}

pub fn op_execute() -> UID {
    get_global_uid(OP_EXECUTE_SYMBOL)
        .expect("OP_EXECUTE should be registered during system initialization")
}

/// 获取特殊标记UID
pub fn anchor_marker() -> UID {
    get_global_uid(ANCHOR_MARKER_SYMBOL)
        .expect("ANCHOR_MARKER should be registered during system initialization")
}

pub fn start_marker() -> UID {
    get_global_uid(START_MARKER_SYMBOL)
        .expect("START_MARKER should be registered during system initialization")
}

pub fn exec_marker() -> UID {
    get_global_uid(EXEC_MARKER_SYMBOL)
        .expect("EXEC_MARKER should be registered during system initialization")
}

pub fn success_marker() -> UID {
    get_global_uid(SUCCESS_MARKER_SYMBOL)
        .expect("SUCCESS should be registered during system initialization")
}

pub fn failure_marker() -> UID {
    get_global_uid(FAILURE_MARKER_SYMBOL)
        .expect("FAILURE should be registered during system initialization")
}

/// 初始化所有系统UID
/// 这应该在系统启动时调用
pub fn initialize_system_uids() -> Result<(), crate::core::symbol_map::SymbolError> {
    use crate::core::symbol_map::pre_register_system_symbols;
    
    // 注册所有预定义符号
    pre_register_system_symbols()?;
    
    // 注册额外的系统符号
    register_global_symbol(ERROR_START_SYMBOL)?;
    register_global_symbol(OP_SEARCH_SYMBOL)?;
    register_global_symbol(OP_EXECUTE_SYMBOL)?;
    register_global_symbol(ANCHOR_MARKER_SYMBOL)?;
    register_global_symbol(START_MARKER_SYMBOL)?;
    register_global_symbol(EXEC_MARKER_SYMBOL)?;
    register_global_symbol(SUCCESS_MARKER_SYMBOL)?;
    register_global_symbol(FAILURE_MARKER_SYMBOL)?;
    
    Ok(())
}

/// UID范围常量（用于验证和过滤）
pub mod uid_ranges {
    use crate::core::types::UID;
    
    /// 系统UID范围起始
    pub const SYSTEM_UID_START: u64 = 0x0000000100000000;
    
    /// 用户UID范围起始
    pub const USER_UID_START: u64 = 0x1000000000000000;
    
    /// 临时UID范围起始
    pub const TEMP_UID_START: u64 = 0xF000000000000000;
    
    /// 检查是否为系统UID
    pub fn is_system_uid(uid: UID) -> bool {
        uid.0 >= SYSTEM_UID_START && uid.0 < USER_UID_START
    }
    
    /// 检查是否为用户UID
    pub fn is_user_uid(uid: UID) -> bool {
        uid.0 >= USER_UID_START && uid.0 < TEMP_UID_START
    }
    
    /// 检查是否为临时UID
    pub fn is_temp_uid(uid: UID) -> bool {
        uid.0 >= TEMP_UID_START
    }
    
    /// 生成临时UID（不保证唯一性，用于测试）
    pub fn generate_temp_uid(counter: u64) -> UID {
        UID(TEMP_UID_START + counter)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::symbol_map;
    
    #[test]
    fn test_system_uid_initialization() {
        // 初始化系统UID
        symbol_map::pre_register_system_symbols().unwrap();
        
        // 测试获取UID
        let role_uid = rel_role();
        let context_uid = rel_context();
        
        assert_ne!(role_uid, context_uid);
        
        // 验证它们是有效的UID
        assert!(role_uid.0 > 0);
        assert!(context_uid.0 > 0);
    }
    
    #[test]
    fn test_uid_ranges() {
        use uid_ranges::*;
        
        // 测试范围检查
        let system_uid = UID(SYSTEM_UID_START + 100);
        let user_uid = UID(USER_UID_START + 100);
        let temp_uid = UID(TEMP_UID_START + 100);
        
        assert!(is_system_uid(system_uid));
        assert!(!is_user_uid(system_uid));
        assert!(!is_temp_uid(system_uid));
        
        assert!(!is_system_uid(user_uid));
        assert!(is_user_uid(user_uid));
        assert!(!is_temp_uid(user_uid));
        
        assert!(!is_system_uid(temp_uid));
        assert!(!is_user_uid(temp_uid));
        assert!(is_temp_uid(temp_uid));
        
        // 测试临时UID生成
        let temp1 = generate_temp_uid(1);
        let temp2 = generate_temp_uid(2);
        
        assert_ne!(temp1, temp2);
        assert!(is_temp_uid(temp1));
        assert!(is_temp_uid(temp2));
    }
    
    #[test]
    fn test_uid_getters() {
        // 初始化
        initialize_system_uids().unwrap();
        
        // 测试所有getter函数
        let uids = vec![
            (rel_role(), "REL_ROLE"),
            (rel_context(), "REL_CONTEXT"),
            (pattern_wildcard(), "PATTERN_WILDCARD"),
            (error_fatal(), "ERROR_FATAL"),
            (op_move(), "OP_MOVE"),
            (anchor_marker(), "ANCHOR_MARKER"),
        ];
        
        // 验证所有UID都是唯一的
        let mut uid_set = std::collections::HashSet::new();
        for (uid, name) in &uids {
            assert!(uid.0 > 0, "{} should have valid UID", name);
            assert!(!uid_set.contains(uid), "{} should have unique UID", name);
            uid_set.insert(*uid);
        }
    }
}