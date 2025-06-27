from eth_hash.auto import (
    keccak,
)
from vm.utils import constant
from vm.utils.numeric import (
    ceil32,
)
from vm.AbstractClass import (
    ComputationAPI,
)


def keccak256(computation: ComputationAPI) -> None:
    start_position, size = computation.stack_pop_ints(2)

    computation.extend_memory(start_position, size)

    sha3_bytes = computation.memory_read_bytes(start_position, size)
    # word_count = ceil32(len(sha3_bytes)) // 32

    # gas_cost = constant.GAS_SHA3WORD * word_count
    # computation.consume_gas(gas_cost, reason="SHA3: word gas cost")

    result = keccak(sha3_bytes)

    computation.stack_push_bytes(result)
