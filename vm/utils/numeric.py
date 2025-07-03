import itertools
from typing import (
    Union,
)
from eth_typing import (
    Hash32,
)
from vm.utils.constant import UINT_256_CEILING, UINT_255_MAX, UINT_256_MAX


def int_to_bytes32(value: Union[int, bool]) -> Hash32:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"Value must be an integer: Got: {type(value)}")
    if value < 0:
        raise ValueError(f"Value cannot be negative: Got: {value}")
    if value > UINT_256_MAX:
        raise ValueError(f"Value exeeds maximum UINT256 size.  Got: {value}")
    value_bytes = value.to_bytes(32, "big")
    return Hash32(value_bytes)


# hotspot, optimized
def ceil32(x: int) -> int:
    return (x + 31) & ~31


def ceil8(x: int) -> int:
    return (x + 7) & ~7


def unsigned_to_signed(value: int) -> int:
    if value <= UINT_255_MAX:
        return value
    else:
        return value - UINT_256_CEILING


def signed_to_unsigned(value: int) -> int:
    if value < 0:
        return value + UINT_256_CEILING
    else:
        return value


def get_highest_bit_index(value: int) -> int:
    value >>= 1
    for bit_length in itertools.count():
        if not value:
            return bit_length
        value >>= 1

    raise Exception("Invariant: unreachable code path")
