import os
import time
import threading
import tempfile
from queue import Queue, Empty
from pathlib import Path
from typing import Optional, List, Tuple, Union, Any, NamedTuple

# ---------------------------- 配置管理 ----------------------------
class Config:
    """从配置文件读取根目录、监控文件路径和轮询间隔"""
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if len(lines) < 2:
            raise ValueError("配置文件至少需要两行：根目录和监控文件路径")
        self.root = Path(lines[0]).resolve()
        self.monitor_file = (self.root / lines[1]).resolve()
        # 可选第三行：轮询间隔（毫秒），默认1000
        self.interval = int(lines[2]) if len(lines) > 2 else 1000
        # 确保监控文件所在的目录存在
        self.monitor_file.parent.mkdir(parents=True, exist_ok=True)
        # 临时文件目录（系统临时目录下创建专属子目录）
        self.temp_dir = Path(tempfile.gettempdir()) / "logos_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

# ---------------------------- 地址解析 ----------------------------
class Address(NamedTuple):
    """解析后的地址信息"""
    file_path: Path          # 绝对路径
    loc_type: str            # 'file', 'gap', 'cell'
    data: Any                # gap: int, cell: (line, cell)

def parse_address(addr_str: str, root: Path) -> Optional[Address]:
    """
    解析地址字符串，返回Address对象。
    格式：
        - 纯路径：/path/to/file  或  path/to/file (相对于根目录)
        - 间隙：  地址#数字
        - 单元：  地址#行数#单元数
    """
    parts = addr_str.split('#')
    if not parts:
        return None
    path_part = parts[0]
    if path_part.startswith('/'):
        path_part = path_part[1:]  # 去掉开头的'/'
    full_path = (root / path_part).resolve()

    if len(parts) == 1:
        return Address(full_path, 'file', None)
    elif len(parts) == 2:
        try:
            gap = int(parts[1])
            return Address(full_path, 'gap', gap)
        except ValueError:
            return None
    elif len(parts) == 3:
        try:
            line = int(parts[1])
            cell = int(parts[2])
            return Address(full_path, 'cell', (line, cell))
        except ValueError:
            return None
    else:
        return None

# ---------------------------- 文件内容操作 ----------------------------
def read_file_text(file_path: Path) -> str:
    """读取文件全部内容，返回字符串。若文件不存在返回空字符串。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def write_file_text(file_path: Path, text: str):
    """将字符串写入文件（覆盖）"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

def read_file_lines(file_path: Path) -> List[str]:
    """读取文件所有行（保留换行符）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        return []

def write_file_lines(file_path: Path, lines: List[str]):
    """将行列表写入文件（覆盖）"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def get_content_by_address(addr: Address) -> Optional[str]:
    """
    根据地址获取内容（仅用于检测指令等需要读取内容的场景）：
    - file: 返回None
    - gap: 返回None（需配合长度）
    - cell: 返回单元内容
    """
    if addr.loc_type == 'file' or addr.loc_type == 'gap':
        return None
    lines = read_file_lines(addr.file_path)
    line_num, cell_num = addr.data
    if line_num < 1 or line_num > len(lines):
        return None
    line_text = lines[line_num-1].rstrip('\n')
    cells = line_text.split('*')
    if cell_num < 1 or cell_num > len(cells):
        return None
    return cells[cell_num-1]

def set_content_by_address(addr: Address, new_content: str, mode: str = 'replace') -> bool:
    """
    将内容写入指定位置。
    mode: 'insert' (仅对间隙有效) 或 'replace' (对单元有效)
    """
    if addr.loc_type == 'file':
        return False
    lines = read_file_lines(addr.file_path)
    if addr.loc_type == 'gap':
        gap = addr.data
        full_text = ''.join(lines)
        if gap < 1 or gap > len(full_text) + 1:
            return False
        new_text = full_text[:gap-1] + new_content + full_text[gap-1:]
        with open(addr.file_path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        return True
    elif addr.loc_type == 'cell':
        line_num, cell_num = addr.data
        if line_num < 1 or line_num > len(lines):
            return False
        line_text = lines[line_num-1].rstrip('\n')
        cells = line_text.split('*')
        if cell_num < 1 or cell_num > len(cells):
            return False
        cells[cell_num-1] = new_content
        new_line = '*'.join(cells) + '\n'
        lines[line_num-1] = new_line
        write_file_lines(addr.file_path, lines)
        return True
    return False

def delete_by_address(addr: Address, length: Optional[int] = None) -> bool:
    """
    删除操作：
    - addr为file：删除整个文件/文件夹
    - addr为gap：删除从该间隙向右length个字符
    - addr为cell：删除整个单元（忽略length）
    """
    if addr.loc_type == 'file':
        try:
            if addr.file_path.is_file():
                addr.file_path.unlink()
            elif addr.file_path.is_dir():
                addr.file_path.rmdir()  # 只删除空目录
            else:
                return False
            return True
        except OSError:
            return False
    elif addr.loc_type == 'gap':
        if length is None:
            return False
        gap = addr.data
        lines = read_file_lines(addr.file_path)
        full_text = ''.join(lines)
        if gap < 1 or gap > len(full_text) + 1:
            return False
        end = gap - 1 + length
        if end > len(full_text):
            return False
        new_text = full_text[:gap-1] + full_text[end:]
        with open(addr.file_path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        return True
    elif addr.loc_type == 'cell':
        line_num, cell_num = addr.data
        lines = read_file_lines(addr.file_path)
        if line_num < 1 or line_num > len(lines):
            return False
        line_text = lines[line_num-1].rstrip('\n')
        cells = line_text.split('*')
        if cell_num < 1 or cell_num > len(cells):
            return False
        del cells[cell_num-1]
        new_line = '*'.join(cells)
        if new_line:
            new_line += '\n'
        else:
            new_line = '\n'
        lines[line_num-1] = new_line
        write_file_lines(addr.file_path, lines)
        return True
    return False

# ---------------------------- 搜索功能 ----------------------------
def search_in_file(file_path: Path, search_str: str) -> List[Tuple[int, int]]:
    """在文件内容中搜索所有不重叠匹配，返回 [(起始间隙, 匹配长度)]"""
    content = read_file_text(file_path)
    results = []
    pos = 0
    search_len = len(search_str)
    while pos < len(content):
        idx = content.find(search_str, pos)
        if idx == -1:
            break
        start_gap = idx + 1
        results.append((start_gap, search_len))
        pos = idx + search_len
    return results

def search_files(root_dir: Path, search_str: str, timeout_ms: int) -> List[Tuple[Path, int, int]]:
    """
    在root_dir下递归搜索所有文件，返回 (文件路径, 起始间隙, 长度)
    超时后返回已找到的结果，结果按文件路径字典序排序。
    """
    start_time = time.time()
    deadline = start_time + timeout_ms / 1000.0 if timeout_ms > 0 else float('inf')
    results = []
    for root, dirs, files in os.walk(root_dir):
        if time.time() > deadline:
            break
        for file in files:
            if time.time() > deadline:
                break
            file_path = Path(root) / file
            matches = search_in_file(file_path, search_str)
            for start_gap, length in matches:
                results.append((file_path, start_gap, length))
    results.sort(key=lambda x: (str(x[0]), x[1]))
    return results

def format_search_result(file_path: Path, start_gap: int, length: int, mode: str, root: Path) -> Optional[str]:
    """
    格式化搜索结果：
    - mode 'a': 输出 "相对路径#起始间隙"
    - mode 'b': 输出 "相对路径#行数#单元数"，若起始位置在分隔符上则返回None
    """
    rel_path = file_path.relative_to(root)
    if mode == 'a':
        return f"{rel_path}#{start_gap}"
    elif mode == 'b':
        content = read_file_text(file_path)
        if not content:
            return None
        lines = content.splitlines(keepends=True)
        char_idx = 0
        for line_num, line in enumerate(lines, start=1):
            line_len = len(line)
            if char_idx <= start_gap-1 < char_idx + line_len:
                in_line_pos = start_gap-1 - char_idx
                if line[in_line_pos] == '*':
                    return None
                line_content = line.rstrip('\n')
                cells = line_content.split('*')
                cell_starts = []
                pos = 0
                for cell in cells:
                    cell_starts.append(pos)
                    pos += len(cell) + 1
                for i, start in enumerate(cell_starts):
                    end = start + len(cells[i])
                    if start <= in_line_pos < end:
                        return f"{rel_path}#{line_num}#{i+1}"
                return None
            char_idx += line_len
        return None
    else:
        return None

# ---------------------------- 指令解析 ----------------------------
class ParsedInstruction(NamedTuple):
    cmd_type: str
    params: List[str]
    has_amp: bool
    after_amp_gap: Optional[int]  # & 之后的间隙（基于当前文本）

def parse_instruction_at(text: str, start_gap: int) -> Optional[ParsedInstruction]:
    """
    从文本的指定间隙开始解析一个指令。
    返回 (类型, 参数列表, 是否有&, &之后的间隙) 或 None。
    """
    if start_gap < 1 or start_gap > len(text) + 1:
        return None
    pos = start_gap - 1
    first_hash = text.find('#', pos)
    if first_hash == -1:
        return None
    cmd_type = text[pos:first_hash]

    # 动态确定参数个数
    if cmd_type == '删除':
        second_hash = text.find('#', first_hash+1)
        if second_hash == -1:
            param_count = 1
        else:
            if second_hash + 1 < len(text) and text[second_hash+1] != '&':
                param_count = 2
            else:
                param_count = 1
    elif cmd_type == '检测':
        param_count = 3  # 三个 #，最后一个参数为空
    else:
        known = {
            '复制': 3,
            '文件夹': 2,
            '文件': 2,
            '搜索': 5,
            '点击': 1
        }
        param_count = known.get(cmd_type)
        if param_count is None:
            return None

    params = []
    current = first_hash
    for i in range(param_count):
        if i == param_count - 1:
            # 最后一个参数：取到行尾或 & 之前
            amp_pos = text.find('&', current+1)
            if amp_pos == -1:
                param = text[current+1:]
                next_pos = len(text)
            else:
                param = text[current+1:amp_pos]
                next_pos = amp_pos
            params.append(param)
            current = next_pos - 1  # 使 current 指向最后一个字符
        else:
            next_hash = text.find('#', current+1)
            if next_hash == -1:
                return None
            param = text[current+1:next_hash]
            params.append(param)
            current = next_hash

    # 检查是否有延续标记 &
    after_pos = current + 1
    has_amp = False
    after_amp_gap = None
    if after_pos < len(text) and text[after_pos] == '&':
        has_amp = True
        if after_pos + 2 <= len(text) + 1:
            after_amp_gap = after_pos + 2
        else:
            after_amp_gap = len(text) + 1

    return ParsedInstruction(cmd_type, params, has_amp, after_amp_gap)

# ---------------------------- 指令对象 ----------------------------
class Instruction(NamedTuple):
    type: str
    params: List[str]
    next_click: Optional[Tuple[Path, int]]  # (文件绝对路径, 间隙编号)

# ---------------------------- 点击函数 ----------------------------
def click(file_path: Path, gap: int, root: Path, queue: Queue):
    """
    在指定文件的指定间隙执行点击：解析一个指令，若成功则构造指令对象并放入队列。
    指令对象包含：类型、参数、以及如果解析时发现 & 则记录 next_click 位置。
    """
    text = read_file_text(file_path)
    if gap < 1 or gap > len(text) + 1:
        print(f"[点击] 无效间隙 {gap} 在文件 {file_path}")
        return
    parsed = parse_instruction_at(text, gap)
    if not parsed:
        print(f"[点击] 解析失败 at {file_path}:{gap}")
        return
    cmd_type, params, has_amp, after_amp_gap = parsed
    next_click = None
    if has_amp and after_amp_gap is not None:
        next_click = (file_path, after_amp_gap)
        print(f"[点击] 指令 {cmd_type} {params} 有延续标记，next_click={next_click}")
    else:
        print(f"[点击] 指令 {cmd_type} {params} 无延续")
    instr = Instruction(cmd_type, params, next_click)
    queue.put(instr)
    print(f"[点击] 指令已入队")

# ---------------------------- 指令执行 ----------------------------
def execute_instruction(inst: Instruction, root: Path, queue: Queue) -> bool:
    """
    执行单个指令。执行成功后若 next_click 存在，则调用 click 将新指令入队。
    返回成功与否。
    """
    cmd = inst.type
    params = inst.params
    print(f"[执行] 开始执行 {cmd} {params}")

    def parse_addr(s):
        return parse_address(s, root)

    try:
        if cmd == '复制':
            if len(params) < 3:
                print("[执行] 复制参数不足")
                return False
            src_addr = parse_addr(params[0])
            dst_addr = parse_addr(params[2])
            if not src_addr or not dst_addr:
                print("[执行] 复制地址解析失败")
                return False
            # 获取源内容
            if src_addr.loc_type == 'gap':
                try:
                    length = int(params[1])
                except ValueError:
                    print("[执行] 复制长度无效")
                    return False
                lines = read_file_lines(src_addr.file_path)
                full_text = ''.join(lines)
                gap = src_addr.data
                if gap < 1 or gap > len(full_text) + 1:
                    return False
                if gap + length - 1 > len(full_text):
                    return False
                content = full_text[gap-1:gap-1+length]
            elif src_addr.loc_type == 'cell':
                content = get_content_by_address(src_addr)
                if content is None:
                    return False
            else:
                print("[执行] 复制源地址类型不支持")
                return False
            # 写入目的地
            if dst_addr.loc_type == 'gap':
                if not set_content_by_address(dst_addr, content, mode='insert'):
                    return False
            elif dst_addr.loc_type == 'cell':
                if not set_content_by_address(dst_addr, content, mode='replace'):
                    return False
            else:
                return False
            print("[执行] 复制成功")

        elif cmd == '文件夹':
            if len(params) < 2:
                return False
            parent_addr = parse_addr(params[0])
            if not parent_addr or parent_addr.loc_type != 'file' or not parent_addr.file_path.is_dir():
                print("[执行] 父目录无效")
                return False
            new_folder = parent_addr.file_path / params[1]
            if new_folder.exists():
                print("[执行] 文件夹已存在")
                return False
            new_folder.mkdir()
            print(f"[执行] 文件夹已创建: {new_folder}")

        elif cmd == '文件':
            if len(params) < 2:
                return False
            parent_addr = parse_addr(params[0])
            if not parent_addr or parent_addr.loc_type != 'file' or not parent_addr.file_path.is_dir():
                print("[执行] 父目录无效")
                return False
            new_file = parent_addr.file_path / params[1]
            if new_file.exists():
                print("[执行] 文件已存在")
                return False
            new_file.touch()
            print(f"[执行] 文件已创建: {new_file}")

        elif cmd == '删除':
            if len(params) == 1:
                addr = parse_addr(params[0])
                if not addr or addr.loc_type != 'file':
                    return False
                if not delete_by_address(addr, None):
                    return False
            elif len(params) == 2:
                addr = parse_addr(params[0])
                if not addr:
                    return False
                if addr.loc_type == 'gap':
                    try:
                        length = int(params[1])
                    except ValueError:
                        return False
                    if not delete_by_address(addr, length):
                        return False
                elif addr.loc_type == 'cell':
                    if not delete_by_address(addr, None):
                        return False
                else:
                    return False
            else:
                return False
            print("[执行] 删除成功")

        elif cmd == '检测':
            if len(params) < 2:
                return False
            addr_str, match_str = params[0], params[1]
            addr = parse_addr(addr_str)
            if not addr:
                return False
            content = get_content_by_address(addr)
            if content is None:
                return False
            if content != match_str:
                print("[执行] 检测不匹配")
                return False
            print("[执行] 检测匹配成功")

        elif cmd == '搜索':
            if len(params) < 5:
                return False
            search_str, timeout_str, folder_str, out_str, mode = params
            folder_addr = parse_addr(folder_str)
            out_addr = parse_addr(out_str)
            if not folder_addr or folder_addr.loc_type != 'file' or not folder_addr.file_path.is_dir():
                return False
            if not out_addr or out_addr.loc_type not in ('gap', 'cell'):
                return False
            try:
                timeout = int(timeout_str)
            except ValueError:
                return False
            matches = search_files(folder_addr.file_path, search_str, timeout)
            result_lines = []
            for file_path, start_gap, length in matches:
                line = format_search_result(file_path, start_gap, length, mode, root)
                if line is not None:
                    result_lines.append(line + '\n')
            result_text = ''.join(result_lines)
            if out_addr.loc_type == 'gap':
                if not set_content_by_address(out_addr, result_text, mode='insert'):
                    return False
            else:
                if not set_content_by_address(out_addr, result_text, mode='replace'):
                    return False
            print("[执行] 搜索完成")

        elif cmd == '点击':
            if len(params) < 1:
                return False
            addr = parse_addr(params[0])
            if not addr or addr.loc_type != 'gap':
                return False
            click(addr.file_path, addr.data, root, queue)
            print("[执行] 点击指令执行成功")

        else:
            print(f"[执行] 未知指令类型: {cmd}")
            return False

        # 指令执行成功，触发 next_click
        if inst.next_click:
            file_path, gap = inst.next_click
            print(f"[执行] 触发后续点击: {file_path}:{gap}")
            click(file_path, gap, root, queue)
        return True

    except Exception as e:
        print(f"[执行] 异常: {e}")
        return False

# ---------------------------- 监控线程 ----------------------------
def monitor_worker(config: Config, queue: Queue, stop_event: threading.Event):
    """监控线程：每次读取监控文件第一行，写入临时文件，点击临时文件间隙1，然后删除监控文件该行"""
    monitor_file = config.monitor_file
    interval = config.interval / 1000.0
    # 临时文件路径
    temp_line_file = config.temp_dir / "current_line.txt"

    while not stop_event.is_set():
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
            print(f"[监控] 读取行: {first_line}")

            # 将第一行写入临时文件（覆盖）
            with open(temp_line_file, 'w', encoding='utf-8') as f:
                f.write(first_line)

            # 删除监控文件第一行
            with open(monitor_file, 'w', encoding='utf-8') as f:
                f.writelines(lines[1:])
            print("[监控] 已删除监控文件第一行")

            # 点击临时文件的间隙1
            click(temp_line_file, 1, config.root, queue)

        except Exception as e:
            print(f"[监控] 错误: {e}")
            time.sleep(interval)

# ---------------------------- 执行线程 ----------------------------
def executor_worker(config: Config, queue: Queue, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            instr = queue.get(timeout=1)
            success = execute_instruction(instr, config.root, queue)
            if success:
                print(f"[执行] 指令执行成功: {instr.type}")
            else:
                print(f"[执行] 指令执行失败: {instr.type}")
        except Empty:
            continue
        except Exception as e:
            print(f"[执行] 错误: {e}")

# ---------------------------- 主程序 ----------------------------
def main():
    import sys
    if len(sys.argv) != 2:
        print("用法: python logos_fixed.py <配置文件路径>")
        sys.exit(1)
    config_path = sys.argv[1]
    try:
        config = Config(config_path)
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        sys.exit(1)

    print(f"根目录: {config.root}")
    print(f"监控文件: {config.monitor_file}")
    print(f"轮询间隔: {config.interval}ms")
    print(f"临时目录: {config.temp_dir}")

    queue = Queue()
    stop_event = threading.Event()

    monitor_thread = threading.Thread(target=monitor_worker, args=(config, queue, stop_event), daemon=True)
    executor_thread = threading.Thread(target=executor_worker, args=(config, queue, stop_event), daemon=True)

    monitor_thread.start()
    executor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止...")
        stop_event.set()
        monitor_thread.join(timeout=2)
        executor_thread.join(timeout=2)
    print("程序退出")

if __name__ == "__main__":
    main()