import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from vm.test.test_opcode import run_general_computation
import vm.OpcodeValues as opcode_values
from eth_utils import decode_hex, encode_hex


@pytest.mark.parametrize(
    "val1, val2, expected", [(2, 3, 1), (3, 2, 0), (9, 10, 1), (10, 10, 0)]
)
def test_lt(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.LT](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, expected", [(3, 2, 1), (2, 3, 0), (10, 9, 1), (10, 10, 0)]
)
def test_gt(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.GT](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, expected",
    [
        (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 0, 1),
        (10, 10, 0),
    ],
)
def test_slt(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.SLT](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, expected",
    [
        (0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 1),
        (10, 10, 0),
    ],
)
def test_sgt(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.SGT](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("val1, val2, expected", [(10, 10, 1), (10, 5, 0)])
def test_eq(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.EQ](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("val, expected", [(0, 1), (10, 0)])
def test_iszero(val, expected):
    computation = run_general_computation()
    computation.stack_push_int(val)
    computation.opcodes[opcode_values.ISZERO](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("val1, val2, expected", [(0xF, 0xF, 0xF), (0xFF, 0, 0)])
def test_and(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.AND](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, expected", [(0xF0, 0xF, 0xFF), (0xFF, 0xFF, 0xFF)]
)
def test_or(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.OR](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("val1, val2, expected", [(0xF0, 0xF, 0xFF), (0xFF, 0xFF, 0)])
def test_xor(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.XOR](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val, expected",
    [(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)],
)
def test_not(val, expected):
    computation = run_general_computation()
    computation.stack_push_int(val)
    computation.opcodes[opcode_values.NOT](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "index, value, expected",
    [
        (31, 0xFF, 0xFF),
        (30, 0xFF00, 0xFF),
        (29, 0x123456, 0x12),
        (30, 0x123456, 0x34),
        (31, 0x123456, 0x56),
        (28, 0x123456, 0),
    ],
)
def test_byte(index, value, expected):
    computation = run_general_computation()
    computation.stack_push_int(value)
    computation.stack_push_int(index)
    computation.opcodes[opcode_values.BYTE](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "value, shift, expected",
    [
        ("0x01", "0x01", "0x02"),
        (
            "0xFF00000000000000000000000000000000000000000000000000000000000000",
            "0x04",
            "0xF000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x00",
            "0x0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x01",
            "0x0000000000000000000000000000000000000000000000000000000000000002",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0xff",
            "0x8000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x0100",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x0101",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x00",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x01",
            "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0xff",
            "0x8000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x0100",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            "0x01",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x01",
            "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe",
        ),
    ],
)
def test_shl(value, shift, expected):
    computation = run_general_computation()
    computation.stack_push_bytes(decode_hex(value))
    computation.stack_push_bytes(decode_hex(shift))
    computation.opcodes[opcode_values.SHL](computation)

    result = computation.stack_pop1_int()

    assert result == int(expected, 16)


@pytest.mark.parametrize(
    "value, shift, expected",
    (
        ("0x02", "0x01", "0x01"),
        ("0xFF", "0x04", "0x0f"),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x00",
            "0x0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x01",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0x01",
            "0x4000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0xff",
            "0x0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0x0100",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0x0101",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x00",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x01",
            "0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0xff",
            "0x0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x0100",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            "0x01",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
    ),
)
def test_shr(value, shift, expected):
    computation = run_general_computation()
    computation.stack_push_bytes(decode_hex(value))
    computation.stack_push_bytes(decode_hex(shift))
    computation.opcodes[opcode_values.SHR](computation)

    result = computation.stack_pop1_int()
    assert result == int(expected, 16)


@pytest.mark.parametrize(
    # EIP: https://github.com/ethereum/EIPs/blob/master/EIPS/eip-145.md#sar-arithmetic-shift-right  # noqa: E501
    "value, shift, expected",
    (
        ("0x02", "0x01", "0x01"),
        (
            "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0",
            "0x04",
            "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x00",
            "0x0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x01",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0x01",
            "0xc000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0xff",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0x0100",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0x8000000000000000000000000000000000000000000000000000000000000000",
            "0x0101",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x00",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x01",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0xff",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x0100",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        ),
        (
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            "0x01",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x4000000000000000000000000000000000000000000000000000000000000000",
            "0xfe",
            "0x0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0xf8",
            "0x000000000000000000000000000000000000000000000000000000000000007f",
        ),
        (
            "0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0xfe",
            "0x0000000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0xff",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            "0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "0x0100",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
    ),
)
def test_sar(value, shift, expected):
    computation = run_general_computation()
    computation.stack_push_bytes(decode_hex(value))
    computation.stack_push_bytes(decode_hex(shift))
    computation.opcodes[opcode_values.SAR](computation)

    result = computation.stack_pop1_int()
    assert result == int(expected, 16)
