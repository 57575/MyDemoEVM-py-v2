import pytest
from eth_utils import decode_hex
import vm.OpcodeValues as opcode_values
from vm.test.test_opcode import build_state, run_computation
from vm.Exception import InsufficientStack


@pytest.mark.parametrize("dup_index", range(1, 17))
def test_dupXX(dup_index: int):
    base_push_codes = "60ff"
    ignored_push_codes = "6000" * (dup_index - 1)
    opcode = 0x7F + dup_index
    code: bytes = decode_hex(base_push_codes + ignored_push_codes + f"{opcode:X}")
    expected = "ff"
    state = build_state()
    computation = run_computation(state, None, code)
    stack_size = computation._stack.size()
    result = computation.stack_pop1_any()
    assert stack_size == dup_index + 1
    assert result == decode_hex(expected)


def test_out_of_bounds():
    base_push_codes = "60ff"
    ignored_push_codes = "6000"
    opcode = opcode_values.DUP16
    code: bytes = decode_hex(base_push_codes + ignored_push_codes + f"{opcode:X}")
    state = build_state()
    computation = run_computation(state, None, code)
    assert computation.is_error == True
    assert isinstance(computation.error, InsufficientStack) == True
