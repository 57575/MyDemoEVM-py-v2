import pytest
from eth_utils import decode_hex
import vm.OpcodeValues as opcode_values
from vm.test.test_opcode_arithmetic import build_state, run_computation
from vm.Exception import InsufficientStack


@pytest.mark.parametrize("swap_index", range(1, 17))
def test_swapXX(swap_index: int):
    stack_bottom = "60ff"
    ignored_push_codes = "6000" * (swap_index - 1)
    stack_top = "6001"
    opcode = opcode_values.SWAP1 + (swap_index - 1)
    code: bytes = decode_hex(
        stack_bottom + ignored_push_codes + stack_top + f"{opcode:X}"
    )
    expected = "ff"
    state = build_state()
    computation = run_computation(state, None, code)
    stack_size = computation._stack.size()
    result = computation.stack_pop1_any()
    assert stack_size == swap_index + 1
    assert result == decode_hex(expected)


def test_out_of_bounds():
    base_push_codes = "60ff"
    opcode = opcode_values.SWAP1
    code: bytes = decode_hex(base_push_codes + f"{opcode:X}")
    state = build_state()
    computation = run_computation(state, None, code)
    assert computation.is_error == True
    assert isinstance(computation.error, InsufficientStack) == True
