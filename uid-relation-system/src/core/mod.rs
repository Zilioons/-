//! 核心模块
//! 
//! 包含系统的基础类型和实现

pub mod types;
pub mod uid_gen;
pub mod symbol_map;
pub mod system_uids;

// 重新导出常用类型
pub use types::*;
pub use uid_gen::*;
pub use symbol_map::*;
pub use system_uids::*;

/// 初始化核心系统
/// 这应该在应用程序启动时调用
pub fn initialize_core_system() -> Result<(), Box<dyn std::error::Error>> {
    // 初始化系统UID
    system_uids::initialize_system_uids()?;
    
    log::info!("Core system initialized");
    Ok(())
}

/// 系统信息
pub fn system_info() -> SystemInfo {
    SystemInfo {
        version: crate::VERSION,
        uid_generator_ready: true,
        symbol_table_ready: true,
        system_uids_initialized: true,
    }
}

/// 系统信息结构
#[derive(Debug, Clone)]
pub struct SystemInfo {
    pub version: &'static str,
    pub uid_generator_ready: bool,
    pub symbol_table_ready: bool,
    pub system_uids_initialized: bool,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_core_initialization() {
        // 测试核心系统初始化
        let result = initialize_core_system();
        assert!(result.is_ok());
        
        let info = system_info();
        assert_eq!(info.version, crate::VERSION);
        assert!(info.uid_generator_ready);
        assert!(info.symbol_table_ready);
        assert!(info.system_uids_initialized);
    }
    
    #[test]
    fn test_end_to_end_uid_flow() {
        // 测试完整的UID流程
        initialize_core_system().unwrap();
        
        // 生成一个UID
        let uid = uid_gen::next_global_uid().unwrap();
        println!("Generated UID: {}", uid);
        
        // 解析UID信息
        let info = uid_gen::UIDGenerator::parse(uid);
        println!("UID Info: {:?}", info);
        
        // 创建符号映射
        let symbol = "test_symbol";
        let context = symbol_map::Context::Global;
        
        // 注册符号
        let registered_uid = symbol_map::register_global_symbol(symbol).unwrap();
        println!("Registered UID for '{}': {}", symbol, registered_uid);
        
        // 获取符号
        let retrieved_uid = symbol_map::get_global_uid(symbol).unwrap();
        assert_eq!(registered_uid, retrieved_uid);
        
        // 获取基础符号
        let base_symbol = symbol_map::get_base_symbol_for_uid(registered_uid).unwrap();
        assert_eq!(base_symbol, symbol.to_lowercase());
    }
}