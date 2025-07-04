import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from vm.test.test_opcode_arithmetic import run_general_computation
import vm.OpcodeValues as opcode_values


@pytest.mark.parametrize(
    "start_position, size, memory_value, expected",
    [
        (
            0,
            4,
            bytes.fromhex("0xFFFFFFFF"[2:]),
            bytes.fromhex(
                "0x29045A592007D0C246EF02C2223570DA9522D0CF0F73282C79A1BC8F0BB2C238"[2:]
            ),
        )
    ],
)
def test_keccak256(start_position, size, memory_value, expected):
    computation = run_general_computation()
    computation.extend_memory(start_position, size)
    computation.memory_write(start_position, size, memory_value)
    computation.stack_push_int(size)
    computation.stack_push_int(start_position)
    computation.opcodes[opcode_values.KECCAK256](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected
