from vm.utils.numeric import ceil32
from vm.utils.Validation import (
    validate_uint256,
    validate_is_bytes,
    validate_length,
    validate_lte,
)
from vm.AbstractClass import MemoryAPI


class Memory(MemoryAPI):
    def __init__(self):
        self._bytes = bytearray()

    def get_memory(self):
        return self._bytes

    def extend(self, start_position: int, size: int) -> None:
        if size == 0:
            return

        new_size = ceil32(start_position + size)
        if new_size <= len(self._bytes):
            return

        size_to_extend = new_size - len(self._bytes)
        try:
            self._bytes.extend(bytearray(size_to_extend))
        except BufferError:
            # we can't extend the buffer (which might involve relocating it) if a
            # memoryview (which stores a pointer into the buffer) has been created by
            # read() and not released. Callers of read() will never try to write to the
            # buffer so we're not missing anything by making a new buffer and forgetting
            # about the old one. We're keeping too much memory around but this is still
            # a net savings over having read() return a new bytes() object every time.
            self._bytes = self._bytes + bytearray(size_to_extend)

    def read_bytes(self, start_position: int, size: int) -> bytes:
        return bytes(self._bytes[start_position : start_position + size])

    def __len__(self) -> int:
        return len(self._bytes)

    def write(self, start_position: int, size: int, value: bytes) -> None:
        if size:
            validate_uint256(start_position)
            validate_uint256(size)
            validate_is_bytes(value)
            validate_length(value, length=size)
            validate_lte(start_position + size, maximum=len(self))

            self._bytes[start_position : start_position + len(value)] = value

    def read(self, start_position: int, size: int) -> memoryview:
        return memoryview(self._bytes)[start_position : start_position + size]

    def read_bytes(self, start_position: int, size: int) -> bytes:
        return bytes(self._bytes[start_position : start_position + size])

    def copy(self, destination: int, source: int, length: int) -> None:
        if length == 0:
            return

        validate_uint256(destination)
        validate_uint256(source)
        validate_uint256(length)
        validate_lte(max(destination, source) + length, maximum=len(self))

        buf = memoryview(self._bytes)
        buf[destination : destination + length] = buf[source : source + length]

    def mstore(self, offset, value) -> None:
        mem_offset = int(offset)  # 实际 EVM 中 offset 是 256 位
        if mem_offset + 8 > len(self._bytes):
            raise RuntimeError("Memory out of bounds")
        # 将 long 拆分为 8 个字节
        for i in range(8):
            self._bytes[mem_offset + i] = (value >> (56 - i * 8)) & 0xFF

    def mload(self, offset):
        mem_offset = int(offset)
        if mem_offset + 8 > len(self._bytes):
            raise RuntimeError("Memory out of bounds")
        value = 0
        for i in range(8):
            value |= (self._bytes[mem_offset + i] & 0xFF) << (56 - i * 8)
        return value

    def is_empty(self):
        return all(b == 0 for b in self._bytes)

    def clear(self):
        self._bytes = bytearray(len(self._bytes))
