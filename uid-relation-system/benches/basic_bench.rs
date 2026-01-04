use criterion::{black_box, criterion_group, criterion_main, Criterion};
use uid_relation_system::core::types::{UID, RelationalPosition, Direction};

fn bench_uid_creation(c: &mut Criterion) {
    c.bench_function("uid_creation", |b| {
        b.iter(|| {
            for i in 0..1000 {
                let _uid = UID::from(black_box(i));
            }
        })
    });
}

fn bench_position_creation(c: &mut Criterion) {
    c.bench_function("position_creation", |b| {
        b.iter(|| {
            for i in 0..100 {
                let anchor = UID::from(black_box(i));
                let _pos = RelationalPosition {
                    anchor_uid: anchor,
                    direction: Direction::Right,
                    distance: black_box(i as i64),
                };
            }
        })
    });
}

criterion_group!(benches, bench_uid_creation, bench_position_creation);
criterion_main!(benches);