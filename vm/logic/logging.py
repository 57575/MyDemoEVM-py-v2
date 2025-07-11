import functools
from typing import (
    Tuple,
)
from vm.AbstractClass import (
    ComputationAPI,
)


def log_XX(computation: ComputationAPI, topic_count: int) -> None:
    if topic_count < 0 or topic_count > 4:
        raise TypeError("Invalid log topic size.  Must be 0, 1, 2, 3, or 4")

    mem_start_position, size = computation.stack_pop_ints(2)

    if not topic_count:
        topics: Tuple[int, ...] = ()
    elif topic_count > 1:
        topics = computation.stack_pop_ints(topic_count)
    else:
        topics = (computation.stack_pop1_int(),)

    computation.extend_memory(mem_start_position, size)
    log_data = computation.memory_read_bytes(mem_start_position, size)

    computation.add_log_entry(
        account=computation.msg.storage_address,
        topics=topics,
        data=log_data,
    )


log0 = functools.partial(log_XX, topic_count=0)
log1 = functools.partial(log_XX, topic_count=1)
log2 = functools.partial(log_XX, topic_count=2)
log3 = functools.partial(log_XX, topic_count=3)
log4 = functools.partial(log_XX, topic_count=4)
