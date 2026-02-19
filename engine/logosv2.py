import os
import time
from pathlib import Path
from typing import Optional, List, Tuple, NamedTuple, Any

# ---------------------------- 配置管理 ----------------------------
class Config:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if len(lines) < 2:
            raise ValueError("配置文件至少需要两行：根目录和监控文件路径")
        self.root = Path(lines[0]).resolve()
        self.monitor_file = (self.root / lines[1]).resolve()
        self.interval = int(lines[2]) if len(lines) > 2 else 1000
        self.monitor_file.parent.mkdir(parents=True, exist_ok=True)
        self.temp_file = self.root / "temp_line.txt"

# ---------------------------- 地址解析 ----------------------------
class Address(NamedTuple):
    file_id: int
    line: Optional[int]
    cell: Optional[int]

def parse_address(addr_str: str) -> Optional[Address]:
    parts = addr_str.split('-')
    if not parts:
        return None
    try:
        file_id = int(parts[0])
    except ValueError:
        return None
    if len(parts) == 1:
        return Address(file_id, None, None)
    elif len(parts) == 2:
        try:
            line = int(parts[1])
            return Address(file_id, line, None)
        except ValueError:
            return None
    elif len(parts) == 3:
        try:
            line = int(parts[1])
            cell = int(parts[2])
            return Address(file_id, line, cell)
        except ValueError:
            return None
    else:
        return None

def format_address(addr: Address) -> str:
    if addr.cell is not None:
        return f"{addr.file_id}-{addr.line}-{addr.cell}"
    elif addr.line is not None:
        return f"{addr.file_id}-{addr.line}"
    else:
        return str(addr.file_id)

# ---------------------------- 文件操作 ----------------------------
def file_path_from_id(file_id: int, root: Path) -> Path:
    return root / f"{file_id}.txt"

def read_file_lines(file_path: Path) -> List[List[str]]:
    if not file_path.exists():
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    result = []
    for line in lines:
        line = line.rstrip('\n')
        parts = line.split('*')
        while len(parts) < 3:
            parts.append('null')
        result.append(parts[:3])
    return result

def write_file_lines(file_path: Path, lines: List[List[str]]):
    with open(file_path, 'w', encoding='utf-8') as f:
        for cells in lines:
            f.write('*'.join(cells) + '\n')

def ensure_file_exists(file_id: int, root: Path) -> Path:
    file_path = file_path_from_id(file_id, root)
    if not file_path.exists():
        write_file_lines(file_path, [['null', 'null', 'null']])
    return file_path

def get_cell(addr: Address, root: Path) -> Optional[str]:
    file_path = file_path_from_id(addr.file_id, root)
    if not file_path.exists():
        return None
    lines = read_file_lines(file_path)
    if addr.line is None or addr.line < 1 or addr.line > len(lines):
        return None
    if addr.cell is None or addr.cell < 1 or addr.cell > 3:
        return None
    return lines[addr.line-1][addr.cell-1]

def set_cell(addr: Address, value: str, root: Path) -> bool:
    file_path = file_path_from_id(addr.file_id, root)
    if not file_path.exists():
        return False
    lines = read_file_lines(file_path)
    if addr.line is None or addr.line < 1 or addr.line > len(lines):
        return False
    if addr.cell is None or addr.cell < 1 or addr.cell > 3:
        return False
    lines[addr.line-1][addr.cell-1] = value
    write_file_lines(file_path, lines)
    return True

def delete_line(addr: Address, root: Path) -> bool:
    if addr.line is None:
        return False
    file_path = file_path_from_id(addr.file_id, root)
    if not file_path.exists():
        return False
    lines = read_file_lines(file_path)
    if addr.line < 1 or addr.line > len(lines):
        return False
    del lines[addr.line-1]
    write_file_lines(file_path, lines)
    return True

def delete_file(addr: Address, root: Path) -> bool:
    file_path = file_path_from_id(addr.file_id, root)
    if not file_path.exists():
        return False
    file_path.unlink()
    return True

def insert_lines_at(lines: List[List[str]], at_line: int, new_lines: List[List[str]]) -> List[List[str]]:
    if at_line < 0 or at_line > len(lines):
        return lines
    return lines[:at_line] + new_lines + lines[at_line:]

# ---------------------------- 指令解析 ----------------------------
class Instruction(NamedTuple):
    name: str
    params: List[str]
    has_continuation: bool
    source_file: Path
    source_line: int

def parse_instruction_from_line(line_cells: List[str], file_path: Path, line_num: int) -> Optional[Instruction]:
    if len(line_cells) != 3:
        return None
    first = line_cells[0]
    if first.endswith('&'):
        name = first[:-1]
        has_cont = True
    else:
        name = first
        has_cont = False
    if name == '检测指令':
        has_cont = False  # 检测指令的延续由内部逻辑触发，不额外触发
    params = line_cells[1:3]
    return Instruction(name, params, has_cont, file_path, line_num)

def line_from_instruction(inst: Instruction) -> List[str]:
    first = inst.name + ('&' if inst.has_continuation else '')
    return [first, inst.params[0], inst.params[1]]

# ---------------------------- 点击与执行 ----------------------------
# 注意：click 函数将立即执行指令，不再使用队列
def click(file_path: Path, line_num: int, root: Path):
    """在指定文件的指定行执行点击：读取该行，解析指令，立即执行。"""
    print(f"[点击] 点击 {file_path.name}:{line_num}")
    if not file_path.exists():
        print(f"[点击] 文件不存在: {file_path}")
        return False
    lines = read_file_lines(file_path)
    if line_num < 1 or line_num > len(lines):
        print(f"[点击] 行号 {line_num} 无效")
        return False
    cells = lines[line_num-1]
    inst = parse_instruction_from_line(cells, file_path, line_num)
    if not inst:
        print(f"[点击] 该行不是有效指令: {cells}")
        return False
    print(f"[点击] 解析到指令: {inst.name} {inst.params}")
    # 立即执行指令
    success = execute_instruction(inst, root)
    if success:
        print(f"[点击] 指令 {inst.name} 执行成功")
    else:
        print(f"[点击] 指令 {inst.name} 执行失败")
    return success

def execute_instruction(inst: Instruction, root: Path) -> bool:
    """执行指令，成功返回True。若成功且带延续，则递归点击下一行。"""
    print(f"[执行] 开始执行 {inst.name} {inst.params} 来自 {inst.source_file.name}:{inst.source_line}")
    try:
        # 以下是原有的指令执行逻辑，保持不变
        if inst.name == '文件生成':
            name_str = inst.params[0]
            try:
                file_id = int(name_str)
            except ValueError:
                print("[执行] 文件名必须为数字")
                return False
            file_path = file_path_from_id(file_id, root)
            if file_path.exists():
                print("[执行] 文件已存在")
                return False
            write_file_lines(file_path, [['null', 'null', 'null']])
            print(f"[执行] 文件 {file_id}.txt 已创建")

        elif inst.name == '删除指令':
            addr_str = inst.params[0]
            addr = parse_address(addr_str)
            if not addr:
                print("[执行] 地址无效")
                return False
            if addr.cell is not None:
                if not set_cell(addr, 'null', root):
                    return False
                print(f"[执行] 单元 {addr_str} 已置 null")
            elif addr.line is not None:
                if not delete_line(addr, root):
                    return False
                print(f"[执行] 行 {addr_str} 已删除")
            else:
                if not delete_file(addr, root):
                    return False
                print(f"[执行] 文件 {addr.file_id}.txt 已删除")

        elif inst.name == '复制指令':
            src_str, dst_str = inst.params[0], inst.params[1]
            src = parse_address(src_str)
            dst = parse_address(dst_str)
            if not src or not dst or src.cell is None or dst.cell is None:
                print("[执行] 地址必须为三级")
                return False
            content = get_cell(src, root)
            if content is None:
                return False
            if not set_cell(dst, content, root):
                return False
            print(f"[执行] 从 {src_str} 复制到 {dst_str}")

        elif inst.name == '合并':
            addr1_str, addr2_str = inst.params[0], inst.params[1]
            addr1 = parse_address(addr1_str)
            addr2 = parse_address(addr2_str)
            if not addr1 or not addr2 or addr1.cell is None or addr2.cell is None:
                print("[执行] 地址必须为三级")
                return False
            content1 = get_cell(addr1, root)
            content2 = get_cell(addr2, root)
            if content1 is None or content2 is None:
                return False
            result = content1 + content2
            if not set_cell(addr1, 'null', root) or not set_cell(addr2, 'null', root):
                return False
            file_path = inst.source_file
            lines = read_file_lines(file_path)
            line_num = inst.source_line
            if line_num < 1 or line_num > len(lines):
                return False
            new_line = line_from_instruction(Instruction(inst.name, [result, 'null'], inst.has_continuation, file_path, line_num))
            lines[line_num-1] = new_line
            write_file_lines(file_path, lines)
            print(f"[执行] 合并结果: {result}")

        elif inst.name == '拆分':
            src_str, out_str = inst.params[0], inst.params[1]
            src = parse_address(src_str)
            out = parse_address(out_str)
            if not src or src.cell is None:
                print("[执行] 源地址必须为三级")
                return False
            if not out or out.line is None:
                print("[执行] 输出地址必须为二级")
                return False
            content = get_cell(src, root)
            if content is None:
                return False
            if not set_cell(src, 'null', root):
                return False
            new_lines = []
            for i, ch in enumerate(content, start=1):
                new_lines.append(['分解', ch, str(i)])
            out_file = file_path_from_id(out.file_id, root)
            if not out_file.exists():
                print("[执行] 输出文件不存在")
                return False
            lines = read_file_lines(out_file)
            if out.line < 1 or out.line > len(lines):
                return False
            new_lines_list = insert_lines_at(lines, out.line, new_lines)
            write_file_lines(out_file, new_lines_list)
            print(f"[执行] 拆分 {src_str} 为 {len(content)} 行")

        elif inst.name == '地址计算':
            src_str, mod_str = inst.params[0], inst.params[1]
            src = parse_address(src_str)
            if not src or src.cell is None:
                print("[执行] 原地址必须为三级")
                return False
            mod_parts = mod_str.split('-')
            if len(mod_parts) != 3:
                print("[执行] 修改参数格式错误")
                return False
            file_mod, line_mod, cell_mod = mod_parts
            def apply_mod(original: int, mod: str) -> int:
                if mod.startswith('#'):
                    return int(mod[1:])
                elif mod.startswith('_'):
                    return original + int(mod)  # _5 表示 -5
                else:
                    return original + int(mod)
            try:
                new_file = apply_mod(src.file_id, file_mod)
                new_line = apply_mod(src.line, line_mod)
                new_cell = apply_mod(src.cell, cell_mod)
            except ValueError:
                return False
            new_addr = Address(new_file, new_line, new_cell)
            file_path = inst.source_file
            lines = read_file_lines(file_path)
            line_num = inst.source_line
            if line_num < 1 or line_num > len(lines):
                return False
            new_line_cells = line_from_instruction(Instruction(inst.name, [format_address(new_addr), mod_str], inst.has_continuation, file_path, line_num))
            lines[line_num-1] = new_line_cells
            write_file_lines(file_path, lines)
            print(f"[执行] 地址计算: {src_str} -> {format_address(new_addr)}")

        elif inst.name == '检测指令':
            addr_str, match = inst.params[0], inst.params[1]
            addr = parse_address(addr_str)
            if not addr or addr.cell is None:
                print("[执行] 地址必须为三级")
                return False
            content = get_cell(addr, root)
            if content is None:
                content = 'null'
            if content == match:
                print("[执行] 检测成功，将点击下一行")
                # 检测成功，递归点击下一行
                next_line = inst.source_line + 1
                click(inst.source_file, next_line, root)
                return True
            else:
                print("[执行] 检测失败")
                return False

        elif inst.name == '搜索指令':
            search_str = inst.params[0]
            combined = inst.params[1]
            if '#' not in combined:
                print("[执行] 搜索参数格式错误")
                return False
            range_part, out_part = combined.split('#', 1)
            if '-' not in range_part:
                print("[执行] 区间格式错误")
                return False
            start_str, end_str = range_part.split('-')
            try:
                start = int(start_str)
                end = int(end_str)
            except ValueError:
                return False
            out_addr = parse_address(out_part)
            if not out_addr or out_addr.line is None:
                print("[执行] 输出地址必须为二级")
                return False
            results = []
            for fid in range(start, end+1):
                file_path = file_path_from_id(fid, root)
                if not file_path.exists():
                    continue
                lines = read_file_lines(file_path)
                for line_num, cells in enumerate(lines, start=1):
                    for cell_num, cell in enumerate(cells, start=1):
                        if cell == search_str:
                            addr_str = f"{fid}-{line_num}-{cell_num}"
                            results.append([search_str, '搜索结果', addr_str])
            out_file = file_path_from_id(out_addr.file_id, root)
            if not out_file.exists():
                print("[执行] 输出文件不存在")
                return False
            lines = read_file_lines(out_file)
            if out_addr.line < 1 or out_addr.line > len(lines):
                return False
            new_lines_list = insert_lines_at(lines, out_addr.line, results)
            write_file_lines(out_file, new_lines_list)
            print(f"[执行] 搜索完成，找到 {len(results)} 个匹配")

        elif inst.name == '换行':
            line_addr_str, num_str = inst.params[0], inst.params[1]
            line_addr = parse_address(line_addr_str)
            if not line_addr or line_addr.line is None:
                print("[执行] 行地址必须为二级")
                return False
            try:
                num = int(num_str)
            except ValueError:
                return False
            if num <= 0:
                return False
            file_path = file_path_from_id(line_addr.file_id, root)
            if not file_path.exists():
                return False
            lines = read_file_lines(file_path)
            if line_addr.line < 1 or line_addr.line > len(lines):
                return False
            new_lines = [['null', 'null', 'null'] for _ in range(num)]
            new_lines_list = insert_lines_at(lines, line_addr.line, new_lines)
            write_file_lines(file_path, new_lines_list)
            print(f"[执行] 在 {line_addr_str} 后插入 {num} 行")

        elif inst.name == '点击指令':
            addr_str = inst.params[0]
            addr = parse_address(addr_str)
            if not addr or addr.line is None:
                print("[执行] 点击地址必须为二级")
                return False
            file_path = file_path_from_id(addr.file_id, root)
            if not file_path.exists():
                return False
            lines = read_file_lines(file_path)
            if addr.line < 1 or addr.line > len(lines):
                return False
            cells = lines[addr.line-1]
            sub_inst = parse_instruction_from_line(cells, file_path, addr.line)
            if sub_inst:
                print(f"[执行] 点击指令触发新指令，将立即执行")
                # 立即执行子指令，而不是递归点击？注意：点击指令本身是立即执行的，这里我们直接递归调用 execute_instruction
                # 但为了避免混淆，我们调用 click 来执行子指令（因为 click 会解析并执行）
                # 注意：这里如果直接调用 execute_instruction，需要传递正确的 source_file 和 source_line
                # 简单起见，我们调用 click 函数
                click(file_path, addr.line, root)
            else:
                print("[执行] 点击行无效指令")
                return False

        else:
            print(f"[执行] 未知指令: {inst.name}")
            return False

        # 指令执行成功，检查是否需要延续（递归点击下一行）
        if inst.has_continuation:
            next_line = inst.source_line + 1
            print(f"[执行] 触发延续: 点击 {inst.source_file.name}:{next_line}")
            click(inst.source_file, next_line, root)
        return True

    except Exception as e:
        print(f"[执行] 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

# ---------------------------- 主循环 ----------------------------
def main_loop(config: Config):
    monitor_file = config.monitor_file
    temp_file = config.temp_file
    interval = config.interval / 1000.0

    print(f"程序启动，根目录: {config.root}")
    print(f"监控文件: {monitor_file}")
    print(f"临时文件: {temp_file}")
    print(f"轮询间隔: {interval}秒")

    while True:
        try:
            if not monitor_file.exists():
                time.sleep(interval)
                continue
            with open(monitor_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if not lines:
                time.sleep(interval)
                continue

            first_line = lines[0].rstrip('\n')
            print(f"\n[主循环] 读取监控文件第一行: {first_line}")

            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(first_line + '\n')

            # 删除监控文件第一行
            with open(monitor_file, 'w', encoding='utf-8') as f:
                f.writelines(lines[1:])
            print("[主循环] 已删除该行")

            # 点击临时文件第1行
            click(temp_file, 1, config.root)

        except KeyboardInterrupt:
            print("\n用户中断，退出")
            break
        except Exception as e:
            print(f"[主循环] 错误: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(interval)

# ---------------------------- 主程序 ----------------------------
def main():
    import sys
    if len(sys.argv) != 2:
        print("用法: python program_b_single.py <配置文件路径>")
        sys.exit(1)
    config_path = sys.argv[1]
    try:
        config = Config(config_path)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        sys.exit(1)

    main_loop(config)

if __name__ == "__main__":
    main()