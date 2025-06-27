import collections
from itertools import (
    count,
)
from typing import (
    Callable,
    Dict,
    List,
    Set,
    Union,
    cast,
)

from eth_utils import (
    ValidationError,
)
from eth_utils.toolz import (
    first,
)

from vm.AbstractClass import (
    DatabaseAPI,
)
from vm.utils.EVMTyping import DBCheckpoint

from vm.db.backends.base_db import BaseDB


class DeletedEntry:
    pass


# Track two different kinds of deletion:

# 1. key in wrapped
# 2. key modified in journal
# 3. key deleted
DELETE_WRAPPED = DeletedEntry()

# 1. key not in wrapped
# 2. key created in journal
# 3. key deleted
REVERT_TO_WRAPPED = DeletedEntry()

ChangesetValue = Union[bytes, DeletedEntry]
ChangesetDict = Dict[bytes, ChangesetValue]

get_next_checkpoint = cast(Callable[[], DBCheckpoint], count().__next__)


class TransientBase(BaseDB):
    __slots__ = [
        "_journal_data",
        "_clears_at",
        "_current_values",
        "_ignore_wrapped_db",
        "_checkpoint_stack",
    ]

    def __init__(self) -> None:
        self._current_values: ChangesetDict = {}

        self._journal_data: collections.OrderedDict[DBCheckpoint, ChangesetDict] = (
            collections.OrderedDict()
        )

        self._clears_at: Set[DBCheckpoint] = set()

        self._ignore_wrapped_db = False

        self._checkpoint_stack: List[DBCheckpoint] = []

    @property
    def root_checkpoint(self) -> DBCheckpoint:
        """
        Returns the starting checkpoint
        """
        return first(self._journal_data.keys())

    @property
    def last_checkpoint(self) -> DBCheckpoint:
        """
        Returns the latest checkpoint
        """
        return first(reversed(self._journal_data.keys()))

    def has_checkpoint(self, checkpoint: DBCheckpoint) -> bool:
        return checkpoint in self._checkpoint_stack

    def record_checkpoint(self, custom_checkpoint: DBCheckpoint = None) -> DBCheckpoint:
        """
        Creates a new checkpoint. Checkpoints are a sequential int chosen by Journal
        to prevent collisions.
        """
        if custom_checkpoint is not None:
            if custom_checkpoint in self._journal_data:
                raise ValidationError(
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
        while self._checkpoint_stack:
            checkpoint_id = self._checkpoint_stack.pop()
            if checkpoint_id == through_checkpoint_id:
                break
        else:
            # checkpoint not found!
            raise ValidationError(f"No checkpoint {through_checkpoint_id} was found")

        # This might be optimized further by iterating the other direction and
        # ignoring any follow-up rollbacks on the same variable.
        for _ in range(len(self._journal_data)):
            checkpoint_id, rollback_data = self._journal_data.popitem()

            for old_key, old_value in rollback_data.items():
                if old_value is REVERT_TO_WRAPPED:
                    # The current value may not exist, if it was a delete followed by a
                    # clear, so pop it off, or ignore if it is already missing
                    self._current_values.pop(old_key, None)
                elif old_value is DELETE_WRAPPED:
                    self._current_values[old_key] = old_value
                elif type(old_value) is bytes:
                    self._current_values[old_key] = old_value
                else:
                    raise ValidationError(
                        f"Unexpected value, must be bytes: {old_value!r}"
                    )

            if checkpoint_id in self._clears_at:
                self._clears_at.remove(checkpoint_id)
                self._ignore_wrapped_db = False

            if checkpoint_id == through_checkpoint_id:
                break

        if self._clears_at:
            # if there is still a clear in older locations,
            # then reinitiate the clear flag
            self._ignore_wrapped_db = True

    def clear(self) -> None:
        """
        Treat as if the *underlying* database will also be cleared by some other
        mechanism. We build a special empty reversion changeset just for marking that
        all previous data should be ignored.
        """
        checkpoint = get_next_checkpoint()
        self._journal_data[checkpoint] = self._current_values
        self._current_values = {}
        self._ignore_wrapped_db = True
        self._clears_at.add(checkpoint)

    def has_clear(self, at_checkpoint: DBCheckpoint) -> bool:
        for reversion_changeset_id in reversed(self._journal_data.keys()):
            if reversion_changeset_id in self._clears_at:
                return True
            elif at_checkpoint == reversion_changeset_id:
                return False
        raise ValidationError(f"Checkpoint {at_checkpoint} is not in the journal")

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
            raise ValidationError(f"No checkpoint {commit_to} was found")

        if checkpoint_idx == -1 * len(self._checkpoint_stack):
            raise ValidationError(
                "Should not commit root changeset with commit_changeset, "
                "use pop_all() instead"
            )

        # delete committed checkpoints from the stack
        # (but keep rollbacks for future discards)
        del self._checkpoint_stack[checkpoint_idx:]

        return self._current_values

    def pop_all(self) -> ChangesetDict:
        final_changes = self._current_values
        self._journal_data.clear()
        self._clears_at.clear()
        self._current_values = {}
        self._checkpoint_stack.clear()
        self.record_checkpoint()
        self._ignore_wrapped_db = False
        return final_changes

    #
    # Database API
    #
    def __getitem__(self, key: bytes) -> ChangesetValue:  # type: ignore # Breaks LSP
        """
        For key lookups we need to iterate through the changesets in reverse
        order, returning from the first one in which the key is present.
        """
        # the default result (the value if not in the local values) depends on whether
        # there was a clear
        if self._ignore_wrapped_db:
            default_result = REVERT_TO_WRAPPED
        else:
            default_result = None  # indicate that caller should check wrapped database
        return self._current_values.get(key, default_result)

    def __setitem__(self, key: bytes, value: bytes) -> None:
        # if the value has not been changed since wrapping,
        # then simply revert to original value
        revert_changeset = self._journal_data[self.last_checkpoint]
        if key not in revert_changeset:
            revert_changeset[key] = self._current_values.get(key, REVERT_TO_WRAPPED)
        self._current_values[key] = value

    def _exists(self, key: bytes) -> bool:
        val = self.get(key)
        return val is not None and val not in (REVERT_TO_WRAPPED, DELETE_WRAPPED)

    def __delitem__(self, key: bytes) -> None:
        raise NotImplementedError(
            "You must delete with one of delete_local or delete_wrapped"
        )

    def delete_wrapped(self, key: bytes) -> None:
        revert_changeset = self._journal_data[self.last_checkpoint]
        if key not in revert_changeset:
            revert_changeset[key] = self._current_values.get(key, REVERT_TO_WRAPPED)
        self._current_values[key] = DELETE_WRAPPED

    def delete_local(self, key: bytes) -> None:
        revert_changeset = self._journal_data[self.last_checkpoint]
        if key not in revert_changeset:
            revert_changeset[key] = self._current_values.get(key, REVERT_TO_WRAPPED)
        self._current_values[key] = REVERT_TO_WRAPPED


class TransientBatchDB(BaseDB):
    __slots__ = ["_wrapped_db", "_journal", "record", "commit"]

    def __init__(self, wrapped_db: DatabaseAPI) -> None:
        self._wrapped_db = wrapped_db
        self._journal = TransientBase()
        self.record = self._journal.record_checkpoint
        self.commit = self._journal.commit_checkpoint
        self.reset()

    def __getitem__(self, key: bytes) -> bytes:
        val = self._journal[key]
        if val is DELETE_WRAPPED:
            raise KeyError(
                key,
                "item is deleted in JournalDB, and will be deleted from the wrapped DB",
            )
        elif val is REVERT_TO_WRAPPED:
            raise KeyError(
                key,
                "item is deleted in JournalDB, "
                "and is presumed gone from the wrapped DB",
            )
        elif val is None:
            return self._wrapped_db[key]
        else:
            # mypy doesn't allow custom type guards yet so we need to cast here
            # even though we know it can only be `bytes` at this point.
            return cast(bytes, val)

    def __setitem__(self, key: bytes, value: bytes) -> None:
        """
        - replacing an existing value
        - setting a value that does not exist
        """
        self._journal[key] = value

    def _exists(self, key: bytes) -> bool:
        val = self._journal[key]
        if val in (REVERT_TO_WRAPPED, DELETE_WRAPPED):
            return False
        elif val is None:
            return key in self._wrapped_db
        else:
            return True

    def clear(self) -> None:
        self._journal.clear()

    def has_clear(self) -> bool:
        return self._journal.has_clear(self._journal.root_checkpoint)

    def __delitem__(self, key: bytes) -> None:
        if key in self._wrapped_db:
            self._journal.delete_wrapped(key)
        else:
            if key in self._journal:
                self._journal.delete_local(key)
            else:
                raise KeyError(
                    key, "key could not be deleted in JournalDB, because it was missing"
                )

    #
    # Snapshot API
    #
    def has_checkpoint(self, checkpoint: DBCheckpoint) -> bool:
        return self._journal.has_checkpoint(checkpoint)

    def discard(self, checkpoint: DBCheckpoint) -> None:
        """
        Throws away all journaled data starting at the given checkpoint
        """
        self._journal.discard(checkpoint)

    def reset(self) -> None:
        """
        Reset the entire journal.
        """
        self._journal.pop_all()
