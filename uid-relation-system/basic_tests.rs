use uid_relation_system::core::types::*;
use uid_relation_system::error::make_error_sequence;

#[test]
fn test_uid_display() {
    let uid = UID(0x1234567890ABCDEF);
    assert_eq!(format!("{}", uid), "0x1234567890abcdef");
}

#[test]
fn test_relational_position() {
    let pos = RelationalPosition::start();
    assert_eq!(pos.anchor_uid.0, 0);
    assert!(matches!(pos.direction, Direction::Right));
    assert_eq!(pos.distance, 0);
    
    let anchor = UID(0x1000);
    let pos2 = RelationalPosition::from_anchor(anchor);
    assert_eq!(pos2.anchor_uid, anchor);
}

#[test]
fn test_error_sequence() {
    let error_seq = make_error_sequence(
        ErrorLevel::Warning,
        SystemError::InvalidPosition,
        vec![UID(1), UID(2), UID(3)],
        vec![UID(4)],
    );
    
    // 基本结构检查
    assert!(error_seq.len() >= 5);
}

#[test]
fn test_logic_offset() {
    let offset = LogicOffset {
        logical_timestamp: 1000,
        physical_position: 42,
        deleted: false,
    };
    
    assert_eq!(offset.logical_timestamp, 1000);
    assert_eq!(offset.physical_position, 42);
    assert!(!offset.deleted);
}