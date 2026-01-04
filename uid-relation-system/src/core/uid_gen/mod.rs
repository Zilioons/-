//! 全局唯一ID生成器
//! 
//! 64位UID结构：
//! [时间戳42位][机器ID10位][进程ID6位][序列号6位]
//! 时间戳：从自定义纪元开始的毫秒数（约139年范围）
//! 机器ID：10位（0-1023）
//! 进程ID：6位（0-63）
//! 序列号：6位（0-63，每毫秒重置）

use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};
use std::net::{Ipv4Addr, IpAddr};
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;
use crate::core::types::UID;
use lazy_static::lazy_static;
use serde::{Deserialize, Serialize};

/// 自定义纪元：2024-01-01 00:00:00 UTC
const CUSTOM_EPOCH: u64 = 1704067200000; // 毫秒

/// 位分配常量
const TIMESTAMP_BITS: u64 = 42;
const MACHINE_ID_BITS: u64 = 10;
const PROCESS_ID_BITS: u64 = 6;
const SEQUENCE_BITS: u64 = 6;

/// 位移偏移量
const TIMESTAMP_SHIFT: u64 = MACHINE_ID_BITS + PROCESS_ID_BITS + SEQUENCE_BITS;
const MACHINE_ID_SHIFT: u64 = PROCESS_ID_BITS + SEQUENCE_BITS;
const PROCESS_ID_SHIFT: u64 = SEQUENCE_BITS;

/// 最大值（用于掩码）
const MAX_SEQUENCE: u64 = (1 << SEQUENCE_BITS) - 1;
const MAX_MACHINE_ID: u64 = (1 << MACHINE_ID_BITS) - 1;
const MAX_PROCESS_ID: u64 = (1 << PROCESS_ID_BITS) - 1;

/// UID生成器配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIDGeneratorConfig {
    /// 机器ID（0-1023），默认为IP地址的哈希
    pub machine_id: u16,
    /// 进程ID（0-63），默认为实际进程ID的哈希
    pub process_id: u8,
    /// 是否启用时间回拨保护
    pub enable_clock_drift_protection: bool,
}

impl Default for UIDGeneratorConfig {
    fn default() -> Self {
        let machine_id = calculate_default_machine_id();
        let process_id = calculate_default_process_id();
        
        Self {
            machine_id,
            process_id,
            enable_clock_drift_protection: true,
        }
    }
}

/// 主UID生成器
pub struct UIDGenerator {
    config: UIDGeneratorConfig,
    last_timestamp: AtomicU64,
    sequence: AtomicU64,
    drift_protection_enabled: bool,
}

impl UIDGenerator {
    /// 创建新的UID生成器
    pub fn new(config: UIDGeneratorConfig) -> Self {
        Self {
            config,
            last_timestamp: AtomicU64::new(0),
            sequence: AtomicU64::new(0),
            drift_protection_enabled: true,
        }
    }
    
    /// 生成下一个UID
    pub fn next(&self) -> Result<UID, UIDGeneratorError> {
        let mut timestamp = self.current_timestamp()?;
        let mut sequence = self.sequence.load(Ordering::Relaxed);
        
        loop {
            let last_timestamp = self.last_timestamp.load(Ordering::Relaxed);
            
            if timestamp < last_timestamp {
                if self.drift_protection_enabled {
                    // 时间回拨，等待直到时间追上
                    std::thread::sleep(std::time::Duration::from_millis(last_timestamp - timestamp));
                    timestamp = self.current_timestamp()?;
                    continue;
                } else {
                    return Err(UIDGeneratorError::ClockDrift(timestamp, last_timestamp));
                }
            }
            
            if timestamp == last_timestamp {
                // 同一毫秒内，递增序列号
                sequence = (sequence + 1) & MAX_SEQUENCE;
                
                if sequence == 0 {
                    // 序列号用尽，等待下一毫秒
                    timestamp = self.wait_for_next_millis(last_timestamp);
                }
            } else {
                // 新的毫秒，重置序列号
                sequence = 0;
            }
            
            // CAS更新last_timestamp和sequence
            let expected_last = last_timestamp;
            let new_last = timestamp;
            
            if self.last_timestamp.compare_exchange_weak(
                expected_last,
                new_last,
                Ordering::AcqRel,
                Ordering::Relaxed,
            ).is_ok() {
                self.sequence.store(sequence, Ordering::Relaxed);
                break;
            }
            
            // CAS失败，重试
        }
        
        // 组合各部分生成UID
        let uid = ((timestamp - CUSTOM_EPOCH) << TIMESTAMP_SHIFT)
            | ((self.config.machine_id as u64) << MACHINE_ID_SHIFT)
            | ((self.config.process_id as u64) << PROCESS_ID_SHIFT)
            | sequence;
        
        Ok(UID(uid))
    }
    
    /// 批量生成UID
    pub fn batch(&self, count: usize) -> Result<Vec<UID>, UIDGeneratorError> {
        let mut result = Vec::with_capacity(count);
        for _ in 0..count {
            result.push(self.next()?);
        }
        Ok(result)
    }
    
    /// 从现有UID解析信息
    pub fn parse(uid: UID) -> UIDInfo {
        let value = uid.0;
        
        let timestamp = (value >> TIMESTAMP_SHIFT) + CUSTOM_EPOCH;
        let machine_id = ((value >> MACHINE_ID_SHIFT) & MAX_MACHINE_ID) as u16;
        let process_id = ((value >> PROCESS_ID_SHIFT) & MAX_PROCESS_ID) as u8;
        let sequence = value & MAX_SEQUENCE;
        
        UIDInfo {
            uid,
            timestamp,
            machine_id,
            process_id,
            sequence,
        }
    }
    
    /// 获取当前时间戳（毫秒）
    fn current_timestamp(&self) -> Result<u64, UIDGeneratorError> {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis() as u64)
            .map_err(|_| UIDGeneratorError::SystemTimeError)
    }
    
    /// 等待下一毫秒
    fn wait_for_next_millis(&self, last_timestamp: u64) -> u64 {
        let mut timestamp = self.current_timestamp().unwrap_or(last_timestamp);
        while timestamp <= last_timestamp {
            std::thread::sleep(std::time::Duration::from_micros(100));
            timestamp = self.current_timestamp().unwrap_or(last_timestamp + 1);
        }
        timestamp
    }
    
    /// 启用/禁用时间回拨保护
    pub fn set_drift_protection(&mut self, enabled: bool) {
        self.drift_protection_enabled = enabled;
    }
}

/// UID详细信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIDInfo {
    pub uid: UID,
    pub timestamp: u64,    // 毫秒
    pub machine_id: u16,
    pub process_id: u8,
    pub sequence: u64,
}

impl UIDInfo {
    /// 获取创建时间
    pub fn created_at(&self) -> SystemTime {
        UNIX_EPOCH + std::time::Duration::from_millis(self.timestamp)
    }
    
    /// 检查是否在同一毫秒内生成
    pub fn is_same_millisecond(&self, other: &UIDInfo) -> bool {
        self.timestamp == other.timestamp
            && self.machine_id == other.machine_id
            && self.process_id == other.process_id
    }
}

/// UID生成器错误
#[derive(Debug, thiserror::Error)]
pub enum UIDGeneratorError {
    #[error("系统时间错误")]
    SystemTimeError,
    
    #[error("时间回拨: 当前时间{0} < 上次时间{1}")]
    ClockDrift(u64, u64),
    
    #[error("机器ID超出范围: {0} (最大{MAX_MACHINE_ID})")]
    InvalidMachineId(u64),
    
    #[error("进程ID超出范围: {0} (最大{MAX_PROCESS_ID})")]
    InvalidProcessId(u64),
}

/// 计算默认机器ID（基于IP地址）
fn calculate_default_machine_id() -> u16 {
    // 尝试获取本地IP地址
    let ip_hash = if let Ok(interfaces) = get_local_ips() {
        // 使用第一个IPv4地址
        interfaces.iter()
            .filter_map(|ip| {
                if let IpAddr::V4(ipv4) = ip {
                    Some(ipv4.0)
                } else {
                    None
                }
            })
            .next()
            .unwrap_or(0)
    } else {
        0
    };
    
    (ip_hash % (MAX_MACHINE_ID + 1) as u32) as u16
}

/// 计算默认进程ID
fn calculate_default_process_id() -> u8 {
    let pid = std::process::id() as u64;
    (pid % (MAX_PROCESS_ID + 1)) as u8
}

/// 获取本地IP地址列表
fn get_local_ips() -> Result<Vec<IpAddr>, std::io::Error> {
    use std::net::UdpSocket;
    
    // 创建一个UDP socket来获取本地地址
    let socket = UdpSocket::bind("0.0.0.0:0")?;
    socket.connect("8.8.8.8:80")?;
    let local_addr = socket.local_addr()?;
    
    Ok(vec![local_addr.ip()])
}

/// 简单UID生成器（单线程，用于测试）
pub struct SimpleUIDGenerator {
    counter: AtomicU64,
    base: u64,
}

impl SimpleUIDGenerator {
    pub fn new() -> Self {
        Self {
            counter: AtomicU64::new(0),
            base: CUSTOM_EPOCH << TIMESTAMP_SHIFT,
        }
    }
    
    pub fn next(&self) -> UID {
        let seq = self.counter.fetch_add(1, Ordering::Relaxed);
        UID(self.base | (seq & MAX_SEQUENCE))
    }
}

// 全局UID生成器实例
lazy_static! {
    static ref GLOBAL_GENERATOR: UIDGenerator = UIDGenerator::new(UIDGeneratorConfig::default());
}

/// 获取全局UID生成器引用
pub fn global_generator() -> &'static UIDGenerator {
    &GLOBAL_GENERATOR
}

/// 生成下一个全局UID
pub fn next_global_uid() -> Result<UID, UIDGeneratorError> {
    GLOBAL_GENERATOR.next()
}

/// 批量生成全局UID
pub fn batch_global_uids(count: usize) -> Result<Vec<UID>, UIDGeneratorError> {
    GLOBAL_GENERATOR.batch(count)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_uid_structure() {
        let config = UIDGeneratorConfig {
            machine_id: 0x1FF,  // 511
            process_id: 0x3F,   // 63
            enable_clock_drift_protection: false,
        };
        
        let generator = UIDGenerator::new(config);
        let uid = generator.next().unwrap();
        let info = UIDGenerator::parse(uid);
        
        println!("UID: {}", uid);
        println!("Timestamp: {}", info.timestamp);
        println!("Machine ID: {}", info.machine_id);
        println!("Process ID: {}", info.process_id);
        println!("Sequence: {}", info.sequence);
        
        assert_eq!(info.machine_id, 0x1FF);
        assert_eq!(info.process_id, 0x3F);
        assert!(info.timestamp >= CUSTOM_EPOCH);
    }
    
    #[test]
    fn test_uid_uniqueness() {
        let generator = UIDGenerator::new(UIDGeneratorConfig::default());
        let mut uids = std::collections::HashSet::new();
        
        for _ in 0..1000 {
            let uid = generator.next().unwrap();
            assert!(!uids.contains(&uid));
            uids.insert(uid);
        }
        
        assert_eq!(uids.len(), 1000);
    }
    
    #[test]
    fn test_batch_generation() {
        let generator = UIDGenerator::new(UIDGeneratorConfig::default());
        let batch = generator.batch(10).unwrap();
        
        assert_eq!(batch.len(), 10);
        
        // 验证所有UID都是唯一的
        let mut set = std::collections::HashSet::new();
        for uid in &batch {
            assert!(!set.contains(uid));
            set.insert(*uid);
        }
    }
    
    #[test]
    fn test_simple_generator() {
        let generator = SimpleUIDGenerator::new();
        let uid1 = generator.next();
        let uid2 = generator.next();
        
        assert_ne!(uid1, uid2);
        
        let info1 = UIDGenerator::parse(uid1);
        let info2 = UIDGenerator::parse(uid2);
        
        // 简单生成器使用相同的基地址，只有序列号不同
        assert_eq!(info1.timestamp, info2.timestamp);
        assert_eq!(info1.machine_id, info2.machine_id);
        assert_eq!(info1.process_id, info2.process_id);
        assert_eq!(info2.sequence, info1.sequence + 1);
    }
    
    #[test]
    fn test_global_generator() {
        let uid1 = next_global_uid().unwrap();
        let uid2 = next_global_uid().unwrap();
        
        assert_ne!(uid1, uid2);
        
        let batch = batch_global_uids(5).unwrap();
        assert_eq!(batch.len(), 5);
        
        // 验证批量和单个生成不冲突
        let uid3 = next_global_uid().unwrap();
        assert_ne!(uid3, batch[4]);
    }
}