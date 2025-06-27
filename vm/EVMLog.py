from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from eth_typing import Address
from vm.utils.Validation import (
    validate_canonical_address,
    validate_is_bytes,
    validate_uint256,
)
import itertools


class EVMlog:
    _log_entries: List[Tuple[int, Address, Tuple[int, ...], bytes]] = None

    def __init__(self):
        self._log_counter = itertools.count()
        self._log_entries = []

    def add_log_entry(
        self,
        account: Address,
        topics: Tuple[int, ...],
        data: bytes,
    ) -> None:
        validate_canonical_address(account, title="Log entry address")
        for topic in topics:
            validate_uint256(topic, title="Log entry topic")
        validate_is_bytes(data, title="Log entry data")
        self._log_entries.append((next(self._log_counter), account, topics, data))

    def add_log_without_account(self, topics: Tuple[int, ...], data: bytes) -> None:
        for topic in topics:
            validate_uint256(topic, title="Log entry topic")
        validate_is_bytes(data, title="Log entry data")
        anonymous_address_bytes = b"\xff" * 20
        anonymous_account = Address(anonymous_address_bytes)
        self._log_entries.append(
            (next(self._log_counter), anonymous_account, topics, data)
        )
