# %%
import collections
from itertools import (
    count,
)
from typing import Callable, Dict, List, Union, cast, FrozenSet
from eth_utils.toolz import (
    first,
)
from sqlalchemy.orm import sessionmaker
from vm.db.StateDBModel import CodeStorageModel
from vm.utils.EVMTyping import DBCheckpoint
from vm.db.backends.checkpoint import get_next_checkpoint


class DeletedEntry:
    pass


# 1. key modified in journal
# 2. key deleted
DELETE_WRAPPED = DeletedEntry()

ChangesetValue = Union[bytes, DeletedEntry]
ChangesetDict = Dict[bytes, ChangesetValue]


class CodeBatchDB:
    def __init__(self, engine):
        self.engine = engine
        self._checkpoint_stack: List[DBCheckpoint] = []
        self._current_values: ChangesetDict = {}
        self._accessed = set()
        self._journal_data: collections.OrderedDict[DBCheckpoint, ChangesetDict] = (
            collections.OrderedDict()
        )
        self.reset()

    @property
    def last_checkpoint(self) -> DBCheckpoint:
        """
        Returns the latest checkpoint
        """
        # last() was iterating through all values, so first(reversed()) gives a 12.5x
        # speedup Interestingly, an attempt to cache this value caused a slowdown.
        return first(reversed(self._journal_data.keys()))

    @property
    def accessed(self) -> FrozenSet[bytes]:
        # Make a defensive copy so callers can't modify the list externally
        return frozenset(self._accessed)

    def get_item(self, key: bytes):
        ## in py-evm, consider warpped db, but we did not consider
        default_result = None  # indicate that caller should check wrapped database
        if key not in self._accessed:
            self._accessed.add(key)
        return self._current_values.get(key, default_result)

    def set_item(self, key: bytes, value: bytes):
        # if the value has not been changed since wrapping,
        # then simply revert to original value
        revert_changeset = self._journal_data[self.last_checkpoint]
        if key not in revert_changeset:
            revert_changeset[key] = self._current_values.get(key, DELETE_WRAPPED)
        if key not in self._accessed:
            self._accessed.add(key)
        self._current_values[key] = value

    def has_checkpoint(self, checkpoint: DBCheckpoint) -> bool:
        return checkpoint in self._checkpoint_stack

    def record_checkpoint(self, custom_checkpoint: DBCheckpoint = None) -> DBCheckpoint:
        """
        Creates a new checkpoint. Checkpoints are a sequential int chosen by Journal
        to prevent collisions.
        """
        if custom_checkpoint is not None:
            if custom_checkpoint in self._journal_data:
                raise Exception(
                    "Tried to record with an existing checkpoint: "
                    f"{custom_checkpoint!r}"
                )
            else:
                checkpoint = custom_checkpoint
        else:
            checkpoint = get_next_checkpoint()

        self._journal_data[checkpoint] = {}
        self._checkpoint_stack.append(checkpoint)
        return checkpoint

    def discard(self, through_checkpoint_id: DBCheckpoint) -> None:
        """
        remove checkpoint from __checkpoint_stack and data from __journal_data
        """
        while self._checkpoint_stack:
            checkpoint_id = self._checkpoint_stack.pop()
            if checkpoint_id == through_checkpoint_id:
                break
        else:
            # checkpoint not found!
            raise Exception(f"No checkpoint {through_checkpoint_id} was found")

        # This might be optimized further by iterating the other direction and
        # ignoring any follow-up rollbacks on the same variable.
        for _ in range(len(self._journal_data)):
            checkpoint_id, rollback_data = self._journal_data.popitem()

            for old_key, old_value in rollback_data.items():
                if old_value is DELETE_WRAPPED:
                    self._current_values.pop(old_key, None)
                elif type(old_value) is bytes:
                    self._current_values[old_key] = old_value
                else:
                    raise Exception(f"Unexpected value, must be bytes: {old_value!r}")

            if checkpoint_id == through_checkpoint_id:
                break

    def commit_checkpoint(self, commit_to: DBCheckpoint) -> ChangesetDict:
        """
        Collapses all changes since the given checkpoint. Can no longer discard to any
        of the checkpoints that followed the given checkpoint.
        """
        # Another option would be to enforce monotonically-increasing changeset ids,
        # so we can do:
        # checkpoint_idx = bisect_left(self._checkpoint_stack, commit_to)
        # (then validate against length and value at index)
        for positions_before_last, checkpoint in enumerate(
            reversed(self._checkpoint_stack)
        ):
            if checkpoint == commit_to:
                checkpoint_idx = -1 - positions_before_last
                break
        else:
            raise Exception(f"No checkpoint {commit_to} was found")

        if checkpoint_idx == -1 * len(self._checkpoint_stack):
            raise Exception(
                "Should not commit root changeset with commit_changeset, "
                "use pop_all() instead"
            )

        # delete committed checkpoints from the stack
        # (but keep rollbacks for future discards)
        del self._checkpoint_stack[checkpoint_idx:]

        return self._current_values

    def clear(self) -> None:
        """
        Treat as if the *underlying* database will also be cleared by some other
        mechanism. We build a special empty reversion changeset just for marking that
        all previous data should be ignored.
        """
        checkpoint = get_next_checkpoint()
        self._journal_data[checkpoint] = self._current_values
        self._current_values = {}
        self._accessed.clear()

    def __initial_from_raw_db(self) -> None:
        self._accessed.clear()

    def __pop_all(self) -> ChangesetDict:
        final_changes = self._current_values
        self._journal_data.clear()
        self._current_values = {}
        self._checkpoint_stack.clear()
        self.record_checkpoint()
        return final_changes

    def __reapply_checkpoint_to_journal(self, journal_data: ChangesetDict) -> None:
        self.reset()
        for key, value in journal_data.items():
            self.set_item(key=key, value=value)

    def reset(self) -> None:
        """
        Reset the entire storage.
        """
        self.__pop_all()
        self.__initial_from_raw_db()

    def persist(self) -> None:
        """
        Persist all changes in underlying db. After all changes have been written the
        JournalDB starts a new recording.
        """
        current_data = self.__pop_all()

        try:
            Session = sessionmaker(bind=self.engine)
            with Session() as session:
                existing_data = (
                    session.query(CodeStorageModel)
                    .filter(CodeStorageModel.code_hash.in_(self._accessed))
                    .all()
                )
                existing_slot_map = {item.code_hash: item for item in existing_data}
                # 1. 新增或更新
                for code_hash, code in current_data.items():
                    if code_hash in existing_slot_map:
                        # 更新
                        existing_slot_map[code_hash].code = code
                    else:
                        # 新增
                        new_item = CodeStorageModel(code_hash, code)
                        session.add(new_item)

                # 2. 删除
                for code_hash, item in existing_slot_map.items():
                    if code_hash not in current_data:
                        session.delete(item)
                session.commit()
            self.__initial_from_raw_db()
        except Exception:
            self.__reapply_checkpoint_to_journal(current_data)
            raise
