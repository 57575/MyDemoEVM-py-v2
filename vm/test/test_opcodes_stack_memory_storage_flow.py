import pytest
from eth_utils import decode_hex
import vm.OpcodeValues as opcode_values
from vm.test.test_opcode import (
    run_general_computation,
    run_computation,
    build_state,
    CANONICAL_ADDRESS_A,
    CANONICAL_ADDRESS_B,
    CANONICAL_ADDRESS_C,
)
from vm.Exception import InsufficientStack
from vm.OpcodeStream import CodeStream


def test_pop():
    computation = run_general_computation()

    computation.stack_push_int(1)
    computation.stack_push_int(2)

    computation.opcodes[opcode_values.POP](computation)

    result = computation.stack_pop1_int()
    result == 1
    with pytest.raises(InsufficientStack):
        computation.opcodes[opcode_values.POP](computation)


def test_mload():
    computation = run_general_computation()
    computation.memory_write(0, 32, decode_hex("0xFF").rjust(32, b"\x00"))
    computation.stack_push_int(0)
    computation.opcodes[opcode_values.MLOAD](computation)
    computation.stack_pop1_bytes() == decode_hex("0xFF").rjust(32, b"\x00")

    computation.memory_write(33, 1, decode_hex("0xFF"))
    computation.stack_push_int(1)
    computation.opcodes[opcode_values.MLOAD](computation)
    computation.stack_pop1_bytes() == decode_hex("0xFFFF").rjust(32, b"\x00")

    computation.stack_push_int(0)
    computation.opcodes[opcode_values.MLOAD](computation)
    computation.stack_pop1_bytes() == decode_hex("0xFFFF").rjust(31, b"\x00") + b"\x00"


@pytest.mark.parametrize(
    "start_position, size, value, expected",
    [
        (0, 32, b"\x10\x10", b"\x10\x10".rjust(32, b"\x00")),
        (0, 32, b"\xff", b"\xff".rjust(32, b"\x00")),
        (1, 32, b"\xff", b"\xff".rjust(32, b"\x00")),
    ],
)
def test_mstore(start_position, size, value, expected):
    computation = run_general_computation()
    computation.stack_push_bytes(value)
    computation.stack_push_int(start_position)
    computation.opcodes[opcode_values.MSTORE](computation)
    assert computation.memory_read_bytes(start_position, size) == expected


def test_multiple_mstore():
    computation = run_general_computation()
    computation.stack_push_bytes(b"\xff")
    computation.stack_push_int(0)
    computation.opcodes[opcode_values.MSTORE](computation)
    assert computation.memory_read_bytes(0, 32) == b"\xff".rjust(32, b"\x00")
    computation.stack_push_bytes(b"\xff")
    computation.stack_push_int(1)
    computation.opcodes[opcode_values.MSTORE](computation)
    assert computation.memory_read_bytes(1, 32) == b"\xff".rjust(32, b"\x00")
    assert computation.memory_read_bytes(0, 33) == b"\xff".rjust(33, b"\x00")


@pytest.mark.parametrize(
    "start_position, size, value, expected",
    [
        (0, 1, b"\xff\xff", b"\xff".rjust(1, b"\x00")),
        (1, 1, b"\xff", b"\xff".rjust(1, b"\x00")),
    ],
)
def test_mstore8(start_position, size, value, expected):
    computation = run_general_computation()
    computation.stack_push_bytes(value)
    computation.stack_push_int(start_position)
    computation.opcodes[opcode_values.MSTORE8](computation)
    assert computation.memory_read_bytes(start_position, size) == expected


def test_multiple_mstore8():
    computation = run_general_computation()
    computation.stack_push_bytes(b"\xff\xff")
    computation.stack_push_int(0)
    computation.opcodes[opcode_values.MSTORE8](computation)
    assert computation.memory_read_bytes(0, 1) == b"\xff"
    assert computation.memory_read_bytes(0, 32) == b"\xff".ljust(32, b"\x00")
    computation.stack_push_bytes(b"\xff")
    computation.stack_push_int(1)
    computation.opcodes[opcode_values.MSTORE8](computation)
    assert computation.memory_read_bytes(1, 1) == b"\xff"
    assert computation.memory_read_bytes(0, 2) == b"\xff\xff"
    assert computation.memory_read_bytes(0, 32) == b"\xff\xff".ljust(32, b"\x00")


def test_sload():
    pass


def test_sstore(code, original):

    state = build_state()

    state.set_balance(CANONICAL_ADDRESS_B, 100000000000)
    state.set_storage(CANONICAL_ADDRESS_B, 0, original)
    assert state.get_storage(CANONICAL_ADDRESS_B, 0) == original
    state.persist()
    assert state.get_storage(CANONICAL_ADDRESS_B, 0, from_journal=True) == original
    assert state.get_storage(CANONICAL_ADDRESS_B, 0, from_journal=False) == original

    comp = run_computation(state, CANONICAL_ADDRESS_B, decode_hex(code))


def test_jump():
    code_str = (
        f"{opcode_values.PUSH1:X}"
        + "07"
        + f"{opcode_values.JUMP:X}"
        + f"{opcode_values.PUSH1:x}"
        + "FF"
        + f"{opcode_values.PUSH1:X}"
        + "FF"
        + f"{opcode_values.JUMPDEST:X}"
    )
    state = build_state()
    computation = run_computation(state, None, decode_hex(code_str))
    computation.opcodes[opcode_values.PC](computation)
    assert computation.stack_pop1_int() == 0x07


def test_jumpi():
    code_str = (
        f"{opcode_values.JUMPDEST:X}"
        + f"{opcode_values.PUSH1:X}"
        + "00"
        + f"{opcode_values.PUSH1:X}"
        + "00"
        + f"{opcode_values.JUMPI:X}"
        f"{opcode_values.PUSH1:X}"
        + "01"
        + f"{opcode_values.PUSH1:X}"
        + "0F"
        + f"{opcode_values.JUMPI:X}"
        + f"{opcode_values.PUSH1:x}"
        + "FF"
        + f"{opcode_values.PUSH1:X}"
        + "FF"
        + f"{opcode_values.JUMPDEST:X}"
    )
    state = build_state()
    computation = run_computation(state, None, decode_hex(code_str))
    computation.opcodes[opcode_values.PC](computation)
    assert computation.stack_pop1_int() == 0x0F


def test_program_counter():
    code_str = f"{opcode_values.PC:X}"
    state = build_state()
    computation = run_computation(state, None, decode_hex(code_str))
    assert computation.stack_pop1_int() == 0


def test_msize():
    code_str = (
        f"{opcode_values.MSIZE:X}"
        + f"{opcode_values.PUSH1:X}"
        + "00"
        + f"{opcode_values.MLOAD:X}"
        + f"{opcode_values.POP:X}"
        + f"{opcode_values.MSIZE:X}"
        + f"{opcode_values.PUSH1:X}"
        + "39"
        + f"{opcode_values.MLOAD:X}"
        + f"{opcode_values.POP:X}"
        + f"{opcode_values.MSIZE:X}"
    )
    state = build_state()
    computation = run_computation(state, None, decode_hex(code_str))
    assert computation.stack_pop1_int() == 0x60
    assert computation.stack_pop1_int() == 0x20
    assert computation.stack_pop1_int() == 0x00


def test_gas(gas=10000):
    state = build_state()
    computation = run_computation(state, None, b"", gas=gas)
    computation.opcodes[opcode_values.GAS](computation)
    result = computation.stack_pop1_int()
    assert result == gas


@pytest.mark.parametrize(
    "load_key, store_key, store_value, expected",
    [
        ("00", "00", "46", decode_hex("46")),
        ("01", "00", "46", decode_hex("00")),
        ("01", "01", "46", decode_hex("46")),
        (
            "0100000000000000000000000000000000",
            "0100000000000000000000000000000000",
            "46",
            decode_hex("46"),
        ),
        (
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "46",
            decode_hex("46"),
        ),
    ],
)
def test_tload_tstore(load_key, store_key, store_value, expected):
    key_push_opcode = hex(opcode_values.PUSH0 + len(load_key) // 2)[2:]
    code_str = (
        f"{opcode_values.PUSH1:X}"
        + f"{store_value}"
        + key_push_opcode
        + f"{store_key}"
        + f"{opcode_values.TSTORE:X}"
        + key_push_opcode
        + f"{load_key}"
        + f"{opcode_values.TLOAD:X}"
    )
    state = build_state()
    computation = run_computation(state, None, decode_hex(code_str))
    result = computation.stack_pop1_bytes()
    assert result == expected


def test_mcopy():
    code_str = (
        f"{opcode_values.PUSH32:X}"
        + "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        + f"{opcode_values.PUSH1:X}"
        + "32"
        + f"{opcode_values.MSTORE:X}"
        + f"{opcode_values.PUSH1:X}"
        + "32"
        + f"{opcode_values.PUSH1:X}"
        + "32"
        + f"{opcode_values.PUSH1:X}"
        + "00"
        + f"{opcode_values.MCOPY:X}"
    )
    state = build_state()
    computation = run_computation(state, None, decode_hex(code_str))
    result = computation.memory_read_bytes(0, 64)
    result == decode_hex(
        "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
    )


def test_simple_loop():
    code_str = (
        f"{opcode_values.PUSH1:X}"
        + "03"  # PUSH 0x03 (计数器初始值)
        + f"{opcode_values.PUSH1:X}"
        + "00"  # PUSH 0x00 (计数器存储位置)
        + f"{opcode_values.MSTORE:X}"  # MSTORE (将计数器存储到 memory[0])
        # 循环开始
        + f"{opcode_values.JUMPDEST:X}"  # JUMPDEST (循环目标)
        # 将 "hello" 字符串存储到内存中
        + f"{opcode_values.PUSH5:X}"
        + b"hello".hex()  # PUSH "hello" 的打包值 (0x68 'h', 0x65 'e', 0x6C 'l', 0x6C 'l', 0x6F 'o')
        + f"{opcode_values.PUSH1:X}"
        + "20"  # PUSH 0x20 (存储位置)
        + f"{opcode_values.MSTORE:X}"  # MSTORE (将 "hello" 存储到 memory[0x20])
        # 打印 "hello"
        + f"{opcode_values.PUSH1:X}"
        + "20"  # PUSH 0x20 (字符串长度),MSTORE会将存储内容转换为256位，即32字节，即0x20字节
        + f"{opcode_values.PUSH1:X}"
        + "20"  # PUSH 0x20 (字符串起始位置)
        + f"{opcode_values.LOG0:X}"  # LOG0 (打印 "hello")
        # 计数器减 1
        + f"{opcode_values.PUSH1:X}"
        + "01"
        + f"{opcode_values.PUSH1:X}"
        + "00"  # PUSH 0x00 (计数器存储位置)
        + f"{opcode_values.MLOAD:X}"  # MLOAD (加载计数器值)
        + f"{opcode_values.SUB:02X}"  # SUB (计数器减 1)
        + f"{opcode_values.PUSH1:X}"
        + "00"  # PUSH 0x00 (计数器存储位置)
        + f"{opcode_values.MSTORE:X}"  # MSTORE (将更新后的计数器存储到 memory[0])
        # 检查计数器是否为 0
        + f"{opcode_values.PUSH1:X}"
        + "00"
        + f"{opcode_values.MLOAD:X}"  # MLOAD (加载计数器值)
        + f"{opcode_values.PUSH1:X}"
        + "00"
        + f"{opcode_values.EQ:X}"
        + f"{opcode_values.PUSH1:X}"
        + "29"  # PUSH 0x25 (跳出循环的目标地址)
        + f"{opcode_values.JUMPI:X}"
        # 跳回循环开始
        + f"{opcode_values.PUSH1:X}"
        + "05"  # PUSH 0x05 (循环开始的目标地址)
        + f"{opcode_values.JUMP:X}"  # JUMP (跳回循环开始)
        # 跳出循环
        + f"{opcode_values.JUMPDEST:X}"
        + f"{opcode_values.STOP:02X}"
    )
    state = build_state()
    computation = run_computation(state, None, decode_hex(code_str))
    all_logs = computation.get_raw_log_entries()
    assert all_logs[0][3] == b"hello".rjust(32, b"\x00")
    assert all_logs[1][3] == b"hello".rjust(32, b"\x00")
    assert all_logs[2][3] == b"hello".rjust(32, b"\x00")
