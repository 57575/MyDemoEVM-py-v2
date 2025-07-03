import pytest
from eth_utils import decode_hex, encode_hex
import vm.OpcodeValues as opcode_values
from vm.test.test_opcode import (
    run_general_computation,
    run_computation,
    build_state,
    CANONICAL_ADDRESS_A,
    CANONICAL_ADDRESS_B,
    CANONICAL_ADDRESS_C,
)
from vm.Exception import InvalidInstruction


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                ]
            ),
            "0x43a61f3f4c73ea0d444c5c1c1a8544067a86219b",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "09",
                    f"{opcode_values.CREATE:2X}",
                ]
            ),
            "0x43a61f3f4c73ea0d444c5c1c1a8544067a86219b",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH13:2X}",
                    "63FFFFFFFF6000526004601CF3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "13",
                    f"{opcode_values.PUSH1:2X}",
                    "19",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                ]
            ),
            "0x43a61f3f4c73ea0d444c5c1c1a8544067a86219b",
        ),
    ],
)
def test_create(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.stack_pop1_bytes()
    assert result == decode_hex(expected)
    assert computation.state.get_nonce(address) == 1


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH17:2X}",
                    "67600035600757FE5B60005260086018F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "11",
                    f"{opcode_values.PUSH1:2X}",
                    "0F",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.DUP6:2X}",
                    f"{opcode_values.PUSH2:2X}",
                    "FFFF",
                    f"{opcode_values.CALL:2X}",
                ]
            ),
            "00",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH17:2X}",
                    "67600035600757FE5B60005260086018F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "11",
                    f"{opcode_values.PUSH1:2X}",
                    "0F",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "20",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.DUP6:2X}",
                    f"{opcode_values.PUSH2:2X}",
                    "FFFF",
                    f"{opcode_values.CALL:2X}",
                ]
            ),
            "01",
        ),
    ],
)
def test_call(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.stack_pop1_bytes()
    assert result == decode_hex(expected)


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH17:2X}",
                    "67600035600757FE5B60005260086018F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "11",
                    f"{opcode_values.PUSH1:2X}",
                    "0F",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.DUP6:2X}",
                    f"{opcode_values.PUSH2:2X}",
                    "FFFF",
                    f"{opcode_values.CALLCODE:2X}",
                ]
            ),
            "00",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH17:2X}",
                    "67600035600757FE5B60005260086018F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "11",
                    f"{opcode_values.PUSH1:2X}",
                    "0F",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "01",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.SSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "20",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.DUP6:2X}",
                    f"{opcode_values.PUSH2:2X}",
                    "FFFF",
                    f"{opcode_values.CALL:2X}",
                ]
            ),
            "01",
        ),
    ],
)
def test_callcode(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.stack_pop1_bytes()
    assert result == decode_hex(expected)


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH32:2X}",
                    "FF01000000000000000000000000000000000000000000000000000000000000",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "02",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.RETURN:2X}",
                ]
            ),
            "ff01",
        )
    ],
)
def test_return(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.output
    assert result == decode_hex(expected)


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH17:2X}",
                    "67600035600757FE5B60005260086018F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "11",
                    f"{opcode_values.PUSH1:2X}",
                    "0F",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.DUP5:2X}",
                    f"{opcode_values.PUSH2:2X}",
                    "FFFF",
                    f"{opcode_values.DELEGATECALL:2X}",
                ]
            ),
            "00",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH17:2X}",
                    "67600035600757FE5B60005260086018F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "11",
                    f"{opcode_values.PUSH1:2X}",
                    "0F",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.SSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "20",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.DUP5:2X}",
                    f"{opcode_values.PUSH2:2X}",
                    "FFFF",
                    f"{opcode_values.DELEGATECALL:2X}",
                ]
            ),
            "01",
        ),
    ],
)
def test_delegatecall(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.stack_pop1_bytes()
    assert result == decode_hex(expected)


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE2:2X}",
                ]
            ),
            "0687a12da0ffa0a64a28c9512512b8ae8870b7ea",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE2:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE2:2X}",
                ]
            ),
            "00",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH1:2X}",
                    "01",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "09",
                    f"{opcode_values.CREATE2:2X}",
                ]
            ),
            "dbd0b036a125995a83d0ab020656a8355abac612",
        ),
        (
            "".join(
                [
                    f"{opcode_values.PUSH13:2X}",
                    "63FFFFFFFF60005260046000F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "02",
                    f"{opcode_values.PUSH1:2X}",
                    "0D",
                    f"{opcode_values.PUSH1:2X}",
                    "13",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE2:2X}",
                ]
            ),
            "748c9d8abe0bbfbb78ab6eb20948af7f460a11b7",
        ),
    ],
)
def test_create2(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.stack_pop1_bytes()
    assert result == decode_hex(expected)
    assert computation.state.get_nonce(address) > 0


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH14:2X}",
                    "6460016000556000526005601BF3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "0E",
                    f"{opcode_values.PUSH1:2X}",
                    "12",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.DUP5:2X}",
                    f"{opcode_values.PUSH2:2X}",
                    "FFFF",
                    f"{opcode_values.CREATE:2X}",
                    f"{opcode_values.STATICCALL:2X}",
                ]
            ),
            "00",
        )
    ],
)
def test_staticcall(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.stack_pop1_bytes()
    assert result == decode_hex(expected)


@pytest.mark.parametrize(
    "code_str, expected",
    [
        (
            "".join(
                [
                    f"{opcode_values.PUSH32:2X}",
                    "FF01000000000000000000000000000000000000000000000000000000000000",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "02",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.REVERT:2X}",
                ]
            ),
            "ff01",
        )
    ],
)
def test_revert(code_str, expected):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.output
    assert result == decode_hex(expected)


@pytest.mark.parametrize(
    "code_str",
    [("FE"), ("FB"), ("FC")],
)
def test_invalid(code_str: str):
    address = decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8")
    state = build_state()
    state.set_balance(address, 10)
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=address,
    )
    result = computation.error
    assert type(result) == InvalidInstruction
    assert f"Invalid opcode 0x{code_str.lower()}" in result.args[0]


@pytest.mark.parametrize(
    "code_str, original_address, new_smart_contract_address",
    [
        (
            "".join(
                [
                    # self destruct contract, address 748c9d8abe0bbfbb78ab6eb20948af7f460a11b7
                    f"{opcode_values.PUSH13:2X}",
                    "63FFFFFFFF60005260046000F3",
                    f"{opcode_values.PUSH1:2X}",
                    "00",
                    f"{opcode_values.MSTORE:2X}",
                    f"{opcode_values.PUSH1:2X}",
                    "02",
                    f"{opcode_values.PUSH1:2X}",
                    "0D",
                    f"{opcode_values.PUSH1:2X}",
                    "13",
                    f"{opcode_values.PUSH1:2X}",
                    "63",
                    f"{opcode_values.CREATE2:2X}",
                    f"{opcode_values.SELFDESTRUCT:2X}",
                ]
            ),
            decode_hex("9bbfed6889322e016e0a02ee459d306fc19545d8"),
            decode_hex("748c9d8abe0bbfbb78ab6eb20948af7f460a11b7"),
        )
    ],
)
def test_selfdestruct(code_str, original_address, new_smart_contract_address):
    state = build_state()
    state.set_balance(original_address, 1000)
    assert state.get_balance(original_address) == 1000
    computation = run_computation(
        state,
        None,
        decode_hex(code_str),
        to=original_address,
    )
    assert state.get_balance(original_address) == 0
    assert state.get_balance(new_smart_contract_address) == 1000
