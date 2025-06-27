import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from eth_utils import decode_hex
from eth_typing import Address

from vm.test.test_opcode import (
    run_general_computation,
    NORMALIZED_ADDRESS_A,
    NORMALIZED_ADDRESS_B,
    EMPTY_ADDRESS_IN_STATE,
    ADDRESS_NOT_IN_STATE,
    ADDRESS_WITH_JUST_BALANCE,
    ADDRESS_WITH_CODE,
)
import vm.OpcodeValues as opcode_values


@pytest.mark.parametrize("expected", [decode_hex(NORMALIZED_ADDRESS_A)])
def test_address(expected):
    computation = run_general_computation()
    computation.opcodes[opcode_values.ADDRESS](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected


@pytest.mark.parametrize(
    "account_address, expected", [(decode_hex(ADDRESS_WITH_JUST_BALANCE), 1)]
)
def test_balance(account_address: bytes, expected: int):
    computation = run_general_computation()
    computation.stack_push_bytes(account_address)
    computation.opcodes[opcode_values.BALANCE](computation)
    result = computation.stack_pop1_int()
    assert result == expected
    computation.state.set_balance(account_address, 999)
    computation.stack_push_bytes(account_address)
    computation.opcodes[opcode_values.BALANCE](computation)
    result = computation.stack_pop1_int()
    assert result == 999


@pytest.mark.parametrize("expected", [b"\x11" * 20])
def test_origin(expected):
    computation = run_general_computation()
    computation.opcodes[opcode_values.ORIGIN](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected


@pytest.mark.parametrize("expected", [decode_hex(NORMALIZED_ADDRESS_B)])
def test_caller(expected):
    computation = run_general_computation()
    computation.opcodes[opcode_values.CALLER](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected


@pytest.mark.parametrize("expected", [0])
def test_callvalue(expected):
    computation = run_general_computation()
    computation.opcodes[opcode_values.CALLVALUE](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "calldata_index, expected",
    [
        (
            0,
            decode_hex(
                "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            ),
        ),
        (
            31,
            decode_hex(
                "0xFF00000000000000000000000000000000000000000000000000000000000000"
            ),
        ),
    ],
)
def test_calldataload(calldata_index: int, expected):
    computation = run_general_computation(
        data=decode_hex(
            "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
        )
    )
    computation.stack_push_int(calldata_index)
    computation.opcodes[opcode_values.CALLDATALOAD](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            decode_hex(
                "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            ),
            32,
        ),
        (decode_hex("0xFF"), 1),
    ],
)
def test_calldatasize(data, expected):
    computation = run_general_computation(data=data)
    computation.opcodes[opcode_values.CALLDATASIZE](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "data, mem_start_position, calldata_start_position, size, expected",
    [
        (
            decode_hex(
                "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            ),
            0,
            0,
            32,
            decode_hex(
                "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            ),
        ),
        (
            decode_hex(
                "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            ),
            0,
            31,
            8,
            decode_hex(
                "0xFF00000000000000000000000000000000000000000000000000000000000000"
            ),
        ),
    ],
)
def test_calldatacopy(
    data, mem_start_position, calldata_start_position, size, expected
):
    computation = run_general_computation(data=data)
    computation.stack_push_int(size)
    computation.stack_push_int(calldata_start_position)
    computation.stack_push_int(mem_start_position)
    computation.opcodes[opcode_values.CALLDATACOPY](computation)
    result = computation.memory_read_bytes(0, 32)
    assert result == expected


@pytest.mark.parametrize("gasprice, expected", [(10, 10), (123, 123)])
def test_gasprice(gasprice, expected):
    computation = run_general_computation(gas_price=gasprice)
    computation.opcodes[opcode_values.GASPRICE](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "address, expected", [(decode_hex(ADDRESS_WITH_CODE[0]), len(ADDRESS_WITH_CODE[1]))]
)
def test_extcodesize(address: Address, expected):
    computation = run_general_computation()
    computation.stack_push_bytes(address)
    computation.opcodes[opcode_values.EXTCODESIZE](computation)
    result = computation.stack_pop1_int()
    assert result == expected


TEST_ADDRESS_WITH_PSEUDOCODE = (
    "0xddd722f3947def4cf144679da39c4c32bdc35681",
    "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
)


@pytest.mark.parametrize(
    "address, code, mem_start_position, code_start_position, size, expected",
    [
        (
            decode_hex(TEST_ADDRESS_WITH_PSEUDOCODE[0]),
            decode_hex(TEST_ADDRESS_WITH_PSEUDOCODE[1]),
            0,
            0,
            32,
            decode_hex(
                "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            ),
        ),
        (
            decode_hex(TEST_ADDRESS_WITH_PSEUDOCODE[0]),
            decode_hex(TEST_ADDRESS_WITH_PSEUDOCODE[1]),
            0,
            31,
            8,
            decode_hex(
                "0xFF00000000000000000000000000000000000000000000000000000000000000"
            ),
        ),
    ],
)
def test_extcodecopy(
    address, code, mem_start_position, code_start_position, size, expected
):
    computation = run_general_computation()
    computation.state.set_code(address, code)
    computation.stack_push_int(size)
    computation.stack_push_int(code_start_position)
    computation.stack_push_int(mem_start_position)
    computation.stack_push_bytes(address)
    computation.opcodes[opcode_values.EXTCODECOPY](computation)
    result = computation.memory_read_bytes(0, 32)
    assert result == expected


# def test_returndatasize(expected):
#     pass


# def test_returndatacopy(expected):
#     pass


@pytest.mark.parametrize(
    "address, expected",
    (
        (
            ADDRESS_NOT_IN_STATE,
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            EMPTY_ADDRESS_IN_STATE,
            "0x0000000000000000000000000000000000000000000000000000000000000000",
        ),
        (
            ADDRESS_WITH_JUST_BALANCE,
            # account without code, return the empty hash
            "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        ),
        (
            ADDRESS_WITH_CODE[0],
            # equivalent to encode_hex(keccak(ADDRESS_WITH_CODE[1])),
            "0xb6f5188e2984211a0de167a56a92d85bee084d7a469d97a59e1e2b573dbb4301",
        ),
    ),
)
def test_extcodehash(address, expected):
    computation = run_general_computation()

    computation.stack_push_bytes(decode_hex(address))
    computation.opcodes[opcode_values.EXTCODEHASH](computation)

    result = computation.stack_pop1_bytes()
    assert result == decode_hex(expected)
