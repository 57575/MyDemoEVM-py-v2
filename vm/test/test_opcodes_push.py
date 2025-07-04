import pytest
from hypothesis import given, strategies as st
from hypothesis.strategies import binary, integers
from eth_utils import decode_hex, encode_hex
import vm.OpcodeValues as opcode_values
from vm.test.test_opcode_arithmetic import ADDRESS_WITH_CODE, build_state, run_computation


@pytest.mark.parametrize("push_size", range(1, 33))
def test_pushXX(push_size: int):
    data_code = str("ff" * push_size)
    opcode = 0x5F + push_size
    code: bytes = decode_hex(f"0x{opcode:X}" + data_code)
    expected = "ff" * push_size
    expected_pc = push_size + 1
    state = build_state()
    computation = run_computation(state, None, code)
    result = computation.stack_pop1_any()
    assert result == decode_hex(expected)
    assert computation.code.program_counter == expected_pc


def test_push0():
    data_code = str("")
    opcode = 0x5F
    code: bytes = decode_hex(f"0x{opcode:X}" + data_code)
    expected = "0x00"
    expected_pc = 1
    state = build_state()
    computation = run_computation(state, None, code)
    result = computation.stack_pop1_any()
    assert result == decode_hex(expected)
    assert computation.code.program_counter == expected_pc


# def test_push_out_of_bounds():
#     data_code = b"0xff" * 0
#     state = build_state()
#     computation = run_computation(state, None, data_code)

#     with pytest.raises(IndexError):
#         computation.opcodes[opcode_values.PUSH1](computation)


# %%
