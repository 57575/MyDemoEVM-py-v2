from typing import (
    Any,
)

import rlp
from rlp.sedes import big_endian_int, Binary

from vm.AbstractClass import (
    AccountAPI,
)
from vm.utils.constant import (
    BLANK_ROOT_HASH,
    EMPTY_SHA3,
)

trie_root = Binary.fixed_length(32, allow_empty=True)
hash32 = Binary.fixed_length(32)


class Account(rlp.Serializable, AccountAPI):
    """
    RLP object for accounts.
    """

    fields = [
        ("nonce", big_endian_int),
        ("balance", big_endian_int),
        ("storage_root", trie_root),
        ("code_hash", hash32),
    ]

    def __init__(
        self,
        nonce: int = 0,
        balance: int = 0,
        storage_root: bytes = BLANK_ROOT_HASH,
        code_hash: bytes = EMPTY_SHA3,
        **kwargs: Any,
    ) -> None:
        super().__init__(nonce, balance, storage_root, code_hash, **kwargs)

    def __repr__(self) -> str:
        return (
            f"Account(nonce={self.nonce}, balance={self.balance}, "
            f"storage_root=0x{self.storage_root.hex()}, "
            f"code_hash=0x{self.code_hash.hex()})"
        )
