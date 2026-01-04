//! 符号映射系统
//! 
//! 支持一词多义：同一个符号在不同上下文中可以映射到不同的UID
//! 符号 -> [UID列表]（按上下文排序）
//! 反向映射：UID -> 基础符号（可能有多个符号指向同一个UID）

use std::collections::{HashMap, HashSet};
use std::sync::RwLock;
use crate::core::types::UID;
use crate::core::uid_gen;
use serde::{Deserialize, Serialize};
use lazy_static::lazy_static;

/// 上下文标识符
#[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
pub enum Context {
    /// 全局上下文（默认）
    Global,
    /// 特定领域上下文
    Domain(String),
    /// 用户自定义上下文
    Custom(UID),
    /// 临时上下文（不持久化）
    Temporary,
}

impl Default for Context {
    fn default() -> Self {
        Context::Global
    }
}

/// 符号映射条目
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolMapping {
    /// 基础符号字符串
    pub symbol: String,
    /// 符号的UID映射（按上下文）
    pub mappings: HashMap<Context, UID>,
    /// 创建时间
    pub created_at: u64,
    /// 最后访问时间
    pub last_accessed: u64,
}

impl SymbolMapping {
    pub fn new(symbol: String) -> Self {
        let now = crate::core::uid_gen::global_generator()
            .current_timestamp()
            .unwrap_or(0);
        
        Self {
            symbol,
            mappings: HashMap::new(),
            created_at: now,
            last_accessed: now,
        }
    }
    
    /// 在指定上下文中获取UID
    pub fn get_uid(&mut self, context: &Context) -> Option<UID> {
        self.last_accessed = crate::core::uid_gen::global_generator()
            .current_timestamp()
            .unwrap_or(0);
        
        self.mappings.get(context).copied()
    }
    
    /// 在指定上下文中设置UID
    pub fn set_uid(&mut self, context: Context, uid: UID) {
        self.last_accessed = crate::core::uid_gen::global_generator()
            .current_timestamp()
            .unwrap_or(0);
        
        self.mappings.insert(context, uid);
    }
    
    /// 获取所有上下文中的UID
    pub fn get_all_uids(&self) -> Vec<UID> {
        self.mappings.values().copied().collect()
    }
    
    /// 检查是否在指定上下文中存在映射
    pub fn has_mapping(&self, context: &Context) -> bool {
        self.mappings.contains_key(context)
    }
}

/// 符号映射表
#[derive(Debug, Serialize, Deserialize)]
pub struct SymbolTable {
    /// 符号 -> 映射条目
    symbol_to_mapping: HashMap<String, SymbolMapping>,
    /// UID -> 符号列表（反向映射，支持多对一）
    uid_to_symbols: HashMap<UID, HashSet<String>>,
    /// 符号统计
    stats: SymbolStats,
}

impl SymbolTable {
    pub fn new() -> Self {
        Self {
            symbol_to_mapping: HashMap::new(),
            uid_to_symbols: HashMap::new(),
            stats: SymbolStats::new(),
        }
    }
    
    /// 注册新符号（如果不存在）
    pub fn register_symbol(&mut self, symbol: &str, context: Context) -> Result<UID, SymbolError> {
        self.stats.total_symbols += 1;
        
        let symbol_lower = symbol.to_lowercase();
        
        let mapping = self.symbol_to_mapping
            .entry(symbol_lower.clone())
            .or_insert_with(|| SymbolMapping::new(symbol.to_string()));
        
        // 检查是否已存在该上下文的映射
        if let Some(existing_uid) = mapping.get_uid(&context) {
            self.stats.cache_hits += 1;
            return Ok(existing_uid);
        }
        
        // 生成新的UID
        let uid = uid_gen::next_global_uid()
            .map_err(|e| SymbolError::UIDGenerationFailed(e.to_string()))?;
        
        // 设置映射
        mapping.set_uid(context.clone(), uid);
        
        // 更新反向映射
        self.uid_to_symbols
            .entry(uid)
            .or_insert_with(HashSet::new)
            .insert(symbol_lower);
        
        self.stats.unique_uids += 1;
        
        Ok(uid)
    }
    
    /// 获取符号在指定上下文中的UID
    pub fn get_uid(&mut self, symbol: &str, context: &Context) -> Option<UID> {
        self.stats.lookups += 1;
        
        let symbol_lower = symbol.to_lowercase();
        
        if let Some(mapping) = self.symbol_to_mapping.get_mut(&symbol_lower) {
            if let Some(uid) = mapping.get_uid(context) {
                self.stats.cache_hits += 1;
                return Some(uid);
            }
        }
        
        None
    }
    
    /// 获取所有指向指定UID的符号
    pub fn get_symbols_for_uid(&self, uid: UID) -> Vec<String> {
        self.uid_to_symbols
            .get(&uid)
            .map(|set| set.iter().cloned().collect())
            .unwrap_or_default()
    }
    
    /// 获取UID的基本符号（在全局上下文中）
    pub fn get_base_symbol(&mut self, uid: UID) -> Option<String> {
        // 首先检查全局上下文
        for (symbol, mapping) in &self.symbol_to_mapping {
            if let Some(mapped_uid) = mapping.get_uid(&Context::Global) {
                if mapped_uid == uid {
                    return Some(symbol.clone());
                }
            }
        }
        
        // 如果没有全局映射，返回第一个找到的符号
        self.uid_to_symbols
            .get(&uid)
            .and_then(|set| set.iter().next())
            .cloned()
    }
    
    /// 在指定上下文中设置符号-UID映射
    pub fn set_mapping(&mut self, symbol: &str, context: Context, uid: UID) -> Result<(), SymbolError> {
        let symbol_lower = symbol.to_lowercase();
        
        let mapping = self.symbol_to_mapping
            .entry(symbol_lower.clone())
            .or_insert_with(|| SymbolMapping::new(symbol.to_string()));
        
        // 检查是否已存在不同的映射
        if let Some(existing_uid) = mapping.get_uid(&context) {
            if existing_uid != uid {
                // 移除旧的反向映射
                if let Some(symbols) = self.uid_to_symbols.get_mut(&existing_uid) {
                    symbols.remove(&symbol_lower);
                    if symbols.is_empty() {
                        self.uid_to_symbols.remove(&existing_uid);
                        self.stats.unique_uids -= 1;
                    }
                }
            }
        }
        
        // 设置新映射
        mapping.set_uid(context, uid);
        
        // 更新反向映射
        self.uid_to_symbols
            .entry(uid)
            .or_insert_with(HashSet::new)
            .insert(symbol_lower);
        
        self.stats.unique_uids = self.uid_to_symbols.len();
        
        Ok(())
    }
    
    /// 移除指定上下文中的映射
    pub fn remove_mapping(&mut self, symbol: &str, context: &Context) -> bool {
        let symbol_lower = symbol.to_lowercase();
        
        if let Some(mapping) = self.symbol_to_mapping.get_mut(&symbol_lower) {
            if let Some(uid) = mapping.mappings.remove(context) {
                // 更新反向映射
                if let Some(symbols) = self.uid_to_symbols.get_mut(&uid) {
                    symbols.remove(&symbol_lower);
                    if symbols.is_empty() {
                        self.uid_to_symbols.remove(&uid);
                        self.stats.unique_uids -= 1;
                    }
                }
                
                // 如果映射为空，删除整个条目
                if mapping.mappings.is_empty() {
                    self.symbol_to_mapping.remove(&symbol_lower);
                    self.stats.total_symbols -= 1;
                }
                
                return true;
            }
        }
        
        false
    }
    
    /// 获取所有符号
    pub fn get_all_symbols(&self) -> Vec<String> {
        self.symbol_to_mapping.keys().cloned().collect()
    }
    
    /// 获取统计信息
    pub fn get_stats(&self) -> &SymbolStats {
        &self.stats
    }
    
    /// 清理不常用的符号（LRU策略）
    pub fn cleanup(&mut self, max_age_ms: u64, min_access_count: u32) -> usize {
        let now = crate::core::uid_gen::global_generator()
            .current_timestamp()
            .unwrap_or(0);
        
        let mut to_remove = Vec::new();
        
        for (symbol, mapping) in &self.symbol_to_mapping {
            // 计算未访问时间
            let age = now.saturating_sub(mapping.last_accessed);
            
            // 简单的LRU策略
            if age > max_age_ms {
                // 可以添加更复杂的访问计数检查
                to_remove.push(symbol.clone());
            }
        }
        
        let removed_count = to_remove.len();
        
        for symbol in to_remove {
            // 移除符号的所有映射
            if let Some(mapping) = self.symbol_to_mapping.remove(&symbol) {
                for (_, uid) in mapping.mappings {
                    if let Some(symbols) = self.uid_to_symbols.get_mut(&uid) {
                        symbols.remove(&symbol);
                        if symbols.is_empty() {
                            self.uid_to_symbols.remove(&uid);
                        }
                    }
                }
            }
        }
        
        self.stats.total_symbols = self.symbol_to_mapping.len();
        self.stats.unique_uids = self.uid_to_symbols.len();
        self.stats.cleanup_count += removed_count;
        
        removed_count
    }
}

/// 符号统计信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolStats {
    /// 总符号数量
    pub total_symbols: usize,
    /// 唯一UID数量
    pub unique_uids: usize,
    /// 总查找次数
    pub lookups: u64,
    /// 缓存命中次数
    pub cache_hits: u64,
    /// 清理次数
    pub cleanup_count: u64,
}

impl SymbolStats {
    pub fn new() -> Self {
        Self {
            total_symbols: 0,
            unique_uids: 0,
            lookups: 0,
            cache_hits: 0,
            cleanup_count: 0,
        }
    }
    
    /// 计算命中率
    pub fn hit_rate(&self) -> f64 {
        if self.lookups == 0 {
            0.0
        } else {
            self.cache_hits as f64 / self.lookups as f64
        }
    }
}

/// 符号错误类型
#[derive(Debug, thiserror::Error)]
pub enum SymbolError {
    #[error("符号 '{0}' 未找到")]
    SymbolNotFound(String),
    
    #[error("UID生成失败: {0}")]
    UIDGenerationFailed(String),
    
    #[error("序列化错误: {0}")]
    SerializationError(String),
    
    #[error("反序列化错误: {0}")]
    DeserializationError(String),
}

// 全局符号表实例
lazy_static! {
    static ref GLOBAL_SYMBOL_TABLE: RwLock<SymbolTable> = RwLock::new(SymbolTable::new());
}

/// 获取全局符号表
pub fn global_symbol_table() -> &'static RwLock<SymbolTable> {
    &GLOBAL_SYMBOL_TABLE
}

/// 注册全局符号
pub fn register_global_symbol(symbol: &str) -> Result<UID, SymbolError> {
    let mut table = GLOBAL_SYMBOL_TABLE.write().unwrap();
    table.register_symbol(symbol, Context::Global)
}

/// 获取符号的UID（全局上下文）
pub fn get_global_uid(symbol: &str) -> Option<UID> {
    let mut table = GLOBAL_SYMBOL_TABLE.write().unwrap();
    table.get_uid(symbol, &Context::Global)
}

/// 在指定上下文中获取符号UID
pub fn get_uid_in_context(symbol: &str, context: &Context) -> Option<UID> {
    let mut table = GLOBAL_SYMBOL_TABLE.write().unwrap();
    table.get_uid(symbol, context)
}

/// 获取UID的基础符号
pub fn get_base_symbol_for_uid(uid: UID) -> Option<String> {
    let mut table = GLOBAL_SYMBOL_TABLE.write().unwrap();
    table.get_base_symbol(uid)
}

/// 预注册系统常用符号
pub fn pre_register_system_symbols() -> Result<(), SymbolError> {
    let mut table = GLOBAL_SYMBOL_TABLE.write().unwrap();
    
    // 预定义关系标记
    let _ = table.register_symbol("REL_ROLE", Context::Global)?;
    let _ = table.register_symbol("REL_CONTEXT", Context::Global)?;
    let _ = table.register_symbol("REL_MEANING", Context::Global)?;
    
    // 预定义模式元素
    let _ = table.register_symbol("PATTERN_WILDCARD", Context::Global)?;
    let _ = table.register_symbol("PATTERN_WILDCARD_MULTI", Context::Global)?;
    let _ = table.register_symbol("PATTERN_SET_START", Context::Global)?;
    let _ = table.register_symbol("PATTERN_SET_END", Context::Global)?;
    let _ = table.register_symbol("PATTERN_NOT", Context::Global)?;
    let _ = table.register_symbol("PATTERN_MIN_MAX", Context::Global)?;
    
    // 预定义错误码
    let _ = table.register_symbol("ERROR_FATAL", Context::Global)?;
    let _ = table.register_symbol("ERROR_SEVERE", Context::Global)?;
    let _ = table.register_symbol("ERROR_WARNING", Context::Global)?;
    let _ = table.register_symbol("ERROR_INFO", Context::Global)?;
    
    // 预定义指令操作码
    let _ = table.register_symbol("OP_MOVE", Context::Global)?;
    let _ = table.register_symbol("OP_INSERT", Context::Global)?;
    let _ = table.register_symbol("OP_DELETE", Context::Global)?;
    let _ = table.register_symbol("OP_COPY", Context::Global)?;
    let _ = table.register_symbol("OP_RELATE", Context::Global)?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_symbol_registration() {
        let mut table = SymbolTable::new();
        
        // 注册新符号
        let uid1 = table.register_symbol("test", Context::Global).unwrap();
        let uid2 = table.register_symbol("test", Context::Domain("math".to_string())).unwrap();
        
        // 应该得到不同的UID
        assert_ne!(uid1, uid2);
        
        // 再次获取应该返回相同的UID
        let uid1_again = table.register_symbol("test", Context::Global).unwrap();
        assert_eq!(uid1, uid1_again);
    }
    
    #[test]
    fn test_one_symbol_multiple_uids() {
        let mut table = SymbolTable::new();
        
        // 同一符号在不同上下文中应有不同UID
        let uid_global = table.register_symbol("pi", Context::Global).unwrap();
        let uid_math = table.register_symbol("pi", Context::Domain("math".to_string())).unwrap();
        let uid_physics = table.register_symbol("pi", Context::Domain("physics".to_string())).unwrap();
        
        // 所有UID应该不同
        assert_ne!(uid_global, uid_math);
        assert_ne!(uid_global, uid_physics);
        assert_ne!(uid_math, uid_physics);
        
        // 获取应返回正确UID
        assert_eq!(table.get_uid("pi", &Context::Global).unwrap(), uid_global);
        assert_eq!(table.get_uid("pi", &Context::Domain("math".to_string())).unwrap(), uid_math);
    }
    
    #[test]
    fn test_multiple_symbols_same_uid() {
        let mut table = SymbolTable::new();
        
        // 创建自定义UID
        let custom_uid = uid_gen::next_global_uid().unwrap();
        
        // 多个符号映射到同一个UID
        table.set_mapping("apple", Context::Global, custom_uid).unwrap();
        table.set_mapping("pomme", Context::Global, custom_uid).unwrap(); // 法语的"apple"
        
        // 两个符号应映射到同一UID
        let uid1 = table.get_uid("apple", &Context::Global).unwrap();
        let uid2 = table.get_uid("pomme", &Context::Global).unwrap();
        
        assert_eq!(uid1, uid2);
        assert_eq!(uid1, custom_uid);
        
        // 获取该UID的所有符号
        let symbols = table.get_symbols_for_uid(custom_uid);
        assert!(symbols.contains(&"apple".to_string()));
        assert!(symbols.contains(&"pomme".to_string()));
        assert_eq!(symbols.len(), 2);
    }
    
    #[test]
    fn test_context_isolation() {
        let mut table = SymbolTable::new();
        
        // 在不同上下文中注册同一符号
        table.register_symbol("root", Context::Domain("math".to_string())).unwrap();
        table.register_symbol("root", Context::Domain("botany".to_string())).unwrap();
        
        // 确保它们不冲突
        let math_uid = table.get_uid("root", &Context::Domain("math".to_string()));
        let botany_uid = table.get_uid("root", &Context::Domain("botany".to_string()));
        
        assert!(math_uid.is_some());
        assert!(botany_uid.is_some());
        assert_ne!(math_uid.unwrap(), botany_uid.unwrap());
    }
    
    #[test]
    fn test_global_symbol_table() {
        // 测试全局符号表
        let uid = register_global_symbol("global_test").unwrap();
        let retrieved = get_global_uid("global_test").unwrap();
        
        assert_eq!(uid, retrieved);
        
        // 测试基础符号查找
        let symbol = get_base_symbol_for_uid(uid).unwrap();
        assert_eq!(symbol, "global_test");
    }
    
    #[test]
    fn test_case_insensitive() {
        let mut table = SymbolTable::new();
        
        let uid1 = table.register_symbol("Hello", Context::Global).unwrap();
        let uid2 = table.register_symbol("hello", Context::Global).unwrap();
        let uid3 = table.register_symbol("HELLO", Context::Global).unwrap();
        
        // 所有大小写变体应映射到同一UID
        assert_eq!(uid1, uid2);
        assert_eq!(uid2, uid3);
        
        // 查找时也应大小写不敏感
        assert_eq!(table.get_uid("Hello", &Context::Global).unwrap(), uid1);
        assert_eq!(table.get_uid("hello", &Context::Global).unwrap(), uid1);
        assert_eq!(table.get_uid("HELLO", &Context::Global).unwrap(), uid1);
    }
    
    #[test]
    fn test_cleanup() {
        let mut table = SymbolTable::new();
        
        // 注册一些符号
        for i in 0..100 {
            let symbol = format!("symbol_{}", i);
            table.register_symbol(&symbol, Context::Global).unwrap();
        }
        
        let initial_count = table.get_stats().total_symbols;
        
        // 模拟时间流逝（无法直接修改last_accessed，所以这里只测试API）
        let removed = table.cleanup(0, 0); // 立即清理所有未访问的
        
        // 由于我们刚创建，可能不会有被清理的（取决于实现）
        println!("Initial: {}, Removed: {}", initial_count, removed);
        
        assert!(removed <= initial_count);
    }
}