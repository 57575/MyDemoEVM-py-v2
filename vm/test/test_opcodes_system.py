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
