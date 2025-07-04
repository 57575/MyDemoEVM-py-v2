import pytest
from hypothesis import given, strategies as st
from typing import List, Tuple, Optional

from vm.test.test_opcode_arithmetic import run_general_computation
import vm.OpcodeValues as opcode_values


def test_log0(offset=0, size=13):
    computation = run_general_computation()
    computation.extend_memory(0, 13)
    computation.memory_write(0, 13, (b"Hello, World!"))
    computation.stack_push_int(size)
    computation.stack_push_int(offset)

    computation.opcodes[opcode_values.LOG0](computation)

    all_logs = computation.get_raw_log_entries()
    assert len(all_logs) == 1
    assert all_logs[0][3] == b"Hello, World!"
    assert all_logs[0][2] == ()


# 测试LOG1-LOG4操作码（带主题）
@pytest.mark.parametrize(
    "opcode, num_topics",
    [
        (opcode_values.LOG1, 1),  # LOG1
        (opcode_values.LOG2, 2),  # LOG2
        (opcode_values.LOG3, 3),  # LOG3
        (opcode_values.LOG4, 4),  # LOG4
    ],
)
def test_log_with_topics(opcode: int, num_topics: int):
    computation = run_general_computation()
    # 设置内存
    computation.extend_memory(0, 13)
    computation.memory_write(0, 13, (b"Hello, World!"))

    # 添加主题（每个主题是32bit的整数）
    topics_list = []
    for i in range(num_topics):
        topic = 0x10000000 + (num_topics - i)
        topics_list.append(topic)
        computation.stack_push_int(topic)

    # 设置栈中，memory size和offset
    computation.stack_push_int(13)
    computation.stack_push_int(0)
    # 执行LOG操作
    computation.opcodes[opcode](computation)

    # 验证日志
    all_logs = computation.get_raw_log_entries()
    assert len(all_logs) == 1
    assert all_logs[0][3] == b"Hello, World!"
    assert len(all_logs[0][2]) == num_topics
    assert all_logs[0][2] == tuple(reversed(topics_list))
