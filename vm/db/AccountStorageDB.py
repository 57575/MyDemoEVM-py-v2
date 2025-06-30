from typing import (
    FrozenSet,
    List,
    NamedTuple,
    Set,
)

from eth_hash.auto import (
    keccak,
)
from eth_typing import (
    Address,
    Hash32,
)
from eth_utils import (
    ValidationError,
    encode_hex,
    get_extended_debug_logger,
    int_to_big_endian,
    to_bytes,
    to_int,
)
from sqlalchemy.engine import Engine
import rlp
from vm.utils.EVMTyping import DBCheckpoint
from vm.db.AccountBatchDB import AccountBatchDB


CLEAR_COUNT_KEY_NAME = b"clear-count"


class AccountStorageDB:
    logger = get_extended_debug_logger("eth.db.storage.AccountStorageDB")

    def __init__(self, engine: Engine, address: Address) -> None:
        """ """
        self._address = address
        self._accessed_slots: Set[int] = set()
        self._journal_storage = AccountBatchDB(engine=engine, account_address=address)

    def get(self, slot: int, from_journal: bool = True) -> int:
        self._accessed_slots.add(slot)
        key = int_to_big_endian(slot)
        lookup_db = self._journal_storage
        try:
            encoded_value = lookup_db.get_item(key)
        except KeyError:
            return 0

        if encoded_value == b"" or encoded_value is None:
            return 0
        else:
            return rlp.decode(encoded_value, sedes=rlp.sedes.big_endian_int)

    def set(self, slot: int, value: int) -> None:
        key = int_to_big_endian(slot)
        if value:
            self._journal_storage.set_item(key, rlp.encode(value))
        else:
            try:
                current_val = self._journal_storage.get_item(key)
            except KeyError:
                # deleting an empty key has no effect
                return
            else:
                if current_val != b"":
                    # only try to delete the value if it's present
                    # del self._journal_storage[key]
                    self._journal_storage.delete_item(key)

    def delete(self) -> None:
        self.logger.debug2(
            f"Deleting all storage in account 0x{self._address.hex()}",
        )
        self._journal_storage.clear()

    def record(self, checkpoint: DBCheckpoint) -> None:
        self._journal_storage.record_checkpoint(checkpoint)

    def discard(self, checkpoint: DBCheckpoint) -> None:
        self.logger.debug2(f"discard checkpoint {repr(checkpoint)}")
        if self._journal_storage.has_checkpoint(checkpoint):
            self._journal_storage.discard(checkpoint)
        else:
            # if the checkpoint comes before this account started tracking,
            #    then simply reset to the beginning
            self._journal_storage.reset()

    def commit(self, checkpoint: DBCheckpoint) -> None:
        if self._journal_storage.has_checkpoint(checkpoint):
            self._journal_storage.commit_checkpoint(checkpoint)
        else:
            raise ValidationError(
                f"account:{self._address} does not have the checkpoint:{checkpoint}"
            )

    def get_accessed_slots(self) -> FrozenSet[int]:
        return frozenset(self._accessed_slots)

    def persist(self) -> None:
        if self._journal_storage.has_clear():
            self.logger.warning(
                f"account:{self._address} try to clear all data in database"
            )
            self._journal_storage.clear_hard_disk()
        self._journal_storage.persist()
