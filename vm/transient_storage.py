from eth_utils import (
    int_to_big_endian,
)
from eth_typing import Address
from vm.AbstractClass import (
    TransientStorageAPI,
)
from vm.db.transient_batch_db import TransientBatchDB
from vm.db.backends.memory_db import MemoryDB
from vm.utils.EVMTyping import (
    DBCheckpoint,
)
from vm.utils.Validation import (
    validate_canonical_address,
    validate_is_bytes,
    validate_uint256,
)

# EMPTY_VALUE = b""  # note: stack.to_int(b"") == 0
EMPTY_VALUE = b"\x00"


class TransientStorage(TransientStorageAPI):
    def __init__(self) -> None:
        self._db = TransientBatchDB(MemoryDB())

    @staticmethod
    def _get_key(address: Address, slot: int) -> bytes:
        return address + int_to_big_endian(slot)

    def get_transient_storage(self, address: Address, slot: int) -> bytes:
        validate_canonical_address(address)
        validate_uint256(slot)

        key = self._get_key(address, slot)
        return self._db.get(key, EMPTY_VALUE)

    def set_transient_storage(self, address: Address, slot: int, value: bytes) -> None:
        validate_canonical_address(address)
        validate_uint256(slot)
        validate_is_bytes(value)  # JournalDB requires `bytes` values

        key = self._get_key(address, slot)
        self._db[key] = value

    def record(self, checkpoint: DBCheckpoint) -> None:
        self._db.record(checkpoint)

    def commit(self, checkpoint: DBCheckpoint) -> None:
        self._db.commit(checkpoint)

    def discard(self, checkpoint: DBCheckpoint) -> None:
        self._db.discard(checkpoint)

    def clear(self) -> None:
        self._db.clear()
