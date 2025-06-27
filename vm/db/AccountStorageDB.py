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
import rlp
from vm.utils.EVMTyping import DBCheckpoint
from vm.db.AccountBatchDB import AccountBatchDB


CLEAR_COUNT_KEY_NAME = b"clear-count"


class AccountStorageDB:
    logger = get_extended_debug_logger("eth.db.storage.AccountStorageDB")

    def __init__(self, engine, address: Address) -> None:
        """ """
        self._address = address
        self._accessed_slots: Set[int] = set()
        self._journal_storage = AccountBatchDB(engine=engine, account_address=address)

    def get(self, slot: int, from_journal: bool = True) -> int:
        self._accessed_slots.add(slot)
        key = int_to_big_endian(slot)
        lookup_db = self._journal_storage
        try:
            encoded_value = lookup_db[key]
        except KeyError:
            return 0

        if encoded_value == b"":
            return 0
        else:
            return rlp.decode(encoded_value, sedes=rlp.sedes.big_endian_int)

    def set(self, slot: int, value: int) -> None:
        key = int_to_big_endian(slot)
        if value:
            self._journal_storage[key] = rlp.encode(value)
        else:
            try:
                current_val = self._journal_storage[key]
            except KeyError:
                # deleting an empty key has no effect
                return
            else:
                if current_val != b"":
                    # only try to delete the value if it's present
                    del self._journal_storage[key]

    def delete(self) -> None:
        self.logger.debug2(
            f"Deleting all storage in account 0x{self._address.hex()}",
        )
        self._journal_storage.clear()

    def record(self, checkpoint: DBCheckpoint) -> None:
        self._journal_storage.record_checkpoint(checkpoint)

    def discard(self, checkpoint: DBCheckpoint) -> None:
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
            # if the checkpoint comes before this account started tracking,
            #    then flatten all changes, without persisting
            # self._journal_storage.flatten()
            raise NotImplementedError("not implement commit")

    def lock_changes(self) -> None:
        if self._journal_storage.has_clear():
            self._locked_changes.clear()
        self._journal_storage.persist()

    def lock_changes(self) -> None:
        raise NotImplementedError("not implement lock_changes")

        # if self._journal_storage.has_clear():
        #     self._locked_changes.clear()
        # self._journal_storage.persist()

    def make_storage_root(self) -> None:
        self.lock_changes()
        self._locked_changes.persist()

    def _validate_flushed(self) -> None:
        # raise NotImplementedError("not implement validate_flushed")
        # """
        # Will raise an exception if there are some changes made since the last persist.
        # """
        journal_diff = self._journal_storage.diff()
        if len(journal_diff) > 0:
            raise ValidationError(
                "StorageDB had a dirty journal when it needed to be "
                f"clean: {journal_diff!r}"
            )

    def get_accessed_slots(self) -> FrozenSet[int]:
        return frozenset(self._accessed_slots)

    @property
    def has_changed_root(self) -> bool:
        raise NotImplementedError("not implement has_change_root")
        return self._storage_lookup.has_changed_root

    def get_changed_root(self) -> Hash32:
        raise NotImplementedError("not implement get_changed_root")
        return self._storage_lookup.get_changed_root()

    def persist(self) -> None:
        self._validate_flushed()
        if self._storage_lookup.has_changed_root:
            self._storage_lookup.commit_to(db)
