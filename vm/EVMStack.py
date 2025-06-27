from typing import List, Union, Tuple, Any
from eth_utils import (
    ValidationError,
    big_endian_to_int,
    int_to_big_endian,
)
from vm.utils.Validation import validate_stack_bytes, validate_stack_int
from vm.AbstractClass import StackAPI
from vm.Exception import InsufficientStack, FullStack


class EVMStack(StackAPI):
    stack: List[Union[int, bytes]] = []

    def __init__(self):
        self.stack = []
        self._append = self.stack.append

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if self.is_empty():
            raise Exception("Stack is empty")
        return self.stack.pop()

    def push_int(self, value: int) -> None:
        if len(self.stack) > 1023:
            raise FullStack("Stack limit reached")

        validate_stack_int(value)

        self.stack.append(value)

    def push_bytes(self, value: bytes) -> None:
        if len(self.stack) > 1023:
            raise FullStack("Stack limit reached")

        validate_stack_bytes(value)

        self.stack.append(value)

    def pop_any(self, num_items: int) -> Tuple[Union[int, bytes], ...]:
        #
        # Note: This function is optimized for speed over readability.
        #
        if num_items > len(self.stack):
            raise InsufficientStack(
                f"Wanted {num_items} stack items, only had {len(self.stack)}"
            )

        # Quickest way to pop off multiple values from the end, in place
        ret = reversed(self.stack[-num_items:])
        del self.stack[-num_items:]

        return tuple(ret)

    def pop_ints(self, num_items: int) -> Tuple[int, ...]:
        return tuple(to_int(x) for x in self.pop_any(num_items))

    def pop_bytes(self, num_items: int) -> Tuple[bytes, ...]:
        return tuple(to_bytes(x) for x in self.pop_any(num_items))

    def pop1_any(self) -> Union[int, bytes]:
        try:
            return self.stack.pop()
        except IndexError:
            raise InsufficientStack("Wanted 1 stack item, had none")

    def pop1_bytes(self) -> bytes:
        return to_bytes(self.pop1_any())

    def pop1_int(self) -> int:
        return to_int(self.pop1_any())

    def size(self) -> int:
        return len(self.stack)

    def peek(self):
        if self.is_empty():
            raise Exception("Stack is empty")
        return self.stack[-1]

    def is_empty(self):
        return len(self.stack) == 0

    def clear(self):
        self.stack.clear()

    def swap(self, position: int) -> None:
        idx = -1 * position - 1
        try:
            self.stack[-1], self.stack[idx] = self.stack[idx], self.stack[-1]
        except IndexError:
            raise InsufficientStack(f"Insufficient stack items for SWAP{position}")

    def dup(self, position: int) -> None:
        if len(self.stack) > 1023:
            raise FullStack("Stack limit reached")

        try:
            self._append(self.stack[-position])
        except IndexError:
            raise InsufficientStack(f"Insufficient stack items for DUP{position}")


def _busted_type(value: Union[int, bytes]) -> ValidationError:
    item_type = type(value)
    return ValidationError(
        f"Stack must always be bytes or int, got {item_type!r} type, val {value!r}"
    )


def to_int(x: Any) -> int:
    if isinstance(x, int):
        return x
    if isinstance(x, bytes):
        return big_endian_to_int(x)
    raise _busted_type(x)


def to_bytes(x: Any) -> bytes:
    if isinstance(x, bytes):
        return x
    if isinstance(x, int):
        return int_to_big_endian(x)
    raise _busted_type(x)
