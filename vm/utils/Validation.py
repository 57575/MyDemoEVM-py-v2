from typing import (
    Any,
    Sequence,
    Union,
)
from eth_typing import Address
from eth_utils import ValidationError
from vm.utils.EVMTyping import (
    BytesOrView,
)

from vm.utils.constant import UINT_256_MAX, UINT_64_MAX


def validate_uint64(value: int, title: str = "Value") -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{title} must be an integer: Got: {type(value)}")
    if value < 0:
        raise ValidationError(f"{title} cannot be negative: Got: {value}")
    if value > UINT_64_MAX:
        raise ValidationError(f"{title} exceeds maximum uint64 size.  Got: {value}")


def validate_uint256(value: int, title: str = "Value") -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{title} must be an integer: Got: {type(value)}")
    if value < 0:
        raise ValidationError(f"{title} cannot be negative: Got: {value}")
    if value > UINT_256_MAX:
        raise ValidationError(f"{title} exceeds maximum uint256 size.  Got: {value}")


def validate_is_bytes(value: bytes, title: str = "Value", size: int = None) -> None:
    # TODO: include the value itself in the error string
    if not isinstance(value, bytes):
        raise ValidationError(f"{title} must be a byte string.  Got: {type(value)}")
    if size is not None and len(value) != size:
        raise ValidationError(f"{title} must be size `{size}`. Got size `{len(value)}`")


def validate_canonical_address(value: Address, title: str = "Value") -> None:
    if not isinstance(value, bytes) or not len(value) == 20:
        raise ValidationError(f"{title} {value!r} is not a valid canonical address")


def validate_length(value: Sequence[Any], length: int, title: str = "Value") -> None:
    if not len(value) == length:
        raise ValidationError(
            f"{title} must be of length {length}.  Got {value} of length {len(value)}"
        )


def validate_lte(value: int, maximum: int, title: str = "Value") -> None:
    if value > maximum:
        raise ValidationError(f"{title} {value} is not less than or equal to {maximum}")
    validate_is_integer(value, title=title)


def validate_is_integer(value: Union[int, bool], title: str = "Value") -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{title} must be a an integer.  Got: {type(value)}")


def validate_stack_int(value: int) -> None:
    if 0 <= value <= UINT_256_MAX:
        return
    raise ValidationError(
        "Invalid Stack Item: Must be a 256 bit integer. Got {value!r}"
    )


def validate_stack_bytes(value: bytes) -> None:
    if len(value) <= 32:
        return
    raise ValidationError(
        "Invalid Stack Item: Must be either a length 32 byte string. Got {value!r}"
    )


def validate_gte(value: int, minimum: int, title: str = "Value") -> None:
    if value < minimum:
        raise ValidationError(
            f"{title} {value} is not greater than or equal to {minimum}"
        )
    validate_is_integer(value)


def validate_is_boolean(value: bool, title: str = "Value") -> None:
    if not isinstance(value, bool):
        raise ValidationError(f"{title} must be an boolean.  Got type: {type(value)}")


def validate_is_bytes_or_view(value: BytesOrView, title: str = "Value") -> None:
    if isinstance(value, (bytes, memoryview)):
        return
    raise ValidationError(f"{title} must be bytes or memoryview. Got {type(value)}")
