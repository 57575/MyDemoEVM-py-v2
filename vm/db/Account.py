from typing import (
    Dict,
    Iterable,
    Set,
    Tuple,
    cast,
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
    to_checksum_address,
    to_dict,
    to_tuple,
)
from sqlalchemy.engine import Engine
from cachetools import LRUCache

import rlp

from vm.AbstractClass import (
    AccountDatabaseAPI,
    DatabaseAPI,
)
from vm.utils.constant import (
    BLANK_ROOT_HASH,
    EMPTY_SHA3,
)
from vm.utils.EVMTyping import (
    DBCheckpoint,
)
from vm.utils.Validation import (
    validate_canonical_address,
    validate_is_bytes,
    validate_uint64,
    validate_uint256,
)
from vm.db.AccountStorageDB import AccountStorageDB
from vm.rlp.accounts import Account
from vm.db.CodeBatchDB import CodeBatchDB
from vm.db.AccountInfoBatchDB import AccountInfoBatchDB

IS_PRESENT_VALUE = b""

# We focus on simulating transaction execution.
# do not need for interaction and verification with the main chain.
# Therefore, we use fake HASH values to simplify the process.
EMPTY_STATE_ROOT = b"\x00" * 32
EMPTY_STORAGE_ROOT = b"\x00" * 32


class AccountDB(AccountDatabaseAPI):
    logger = get_extended_debug_logger("eth.db.account.AccountDB")

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._account_cache: LRUCache[Address, Account] = LRUCache(maxsize=2048)
        self._account_stores: Dict[Address, AccountStorageDB] = {}  # key-map storage
        self._journaldb = CodeBatchDB(
            engine=self.engine
        )  # account (smart contract) code storage
        self._journaltrie = AccountInfoBatchDB(engine=self.engine)  # account storage
        self._dirty_accounts: Set[Address] = set()
        self._accessed_accounts: Set[Address] = set()
        self._accessed_bytecodes: Set[Address] = set()
        self._root_hash: Hash32 = EMPTY_STATE_ROOT

    @property
    def state_root(self) -> Hash32:
        return self._root_hash

    @state_root.setter
    def state_root(self, value: Hash32) -> None:
        if self._root_hash != value:
            self._root_hash = value

    #
    # Storage
    #
    def get_storage(
        self, address: Address, slot: int, from_journal: bool = True
    ) -> int:
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(slot, title="Storage Slot")

        account_store = self._get_address_store(address)
        return account_store.get(slot, from_journal)

    def set_storage(self, address: Address, slot: int, value: int) -> None:
        validate_uint256(value, title="Storage Value")
        validate_uint256(slot, title="Storage Slot")
        validate_canonical_address(address, title="Storage Address")

        account_store = self._get_address_store(address)
        if address not in self._dirty_accounts:
            cp = self._journaldb.last_checkpoint
            account_store.record(cp)
        self._dirty_accounts.add(address)
        account_store.set(slot, value)

    def _get_address_store(self, address: Address) -> AccountStorageDB:
        if address in self._account_stores:
            store = self._account_stores[address]
        else:
            storage_root = self._get_storage_root(address)
            store = AccountStorageDB(engine=self.engine, address=address)
            self._account_stores[address] = store
        return store

    def delete_storage(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")

        self._set_storage_root(address, BLANK_ROOT_HASH)
        self._wipe_storage(address)

    def is_storage_warm(self, address: Address, slot: int) -> bool:
        key = self._get_storage_tracker_key(address, slot)
        return NotImplementedError("not implement the is storage warm")
        return key in self._journal_accessed_state

    def mark_storage_warm(self, address: Address, slot: int) -> None:
        key = self._get_storage_tracker_key(address, slot)
        return NotImplementedError("not implement the mark storage warm")
        if key not in self._journal_accessed_state:
            self._journal_accessed_state[key] = IS_PRESENT_VALUE

    def _get_storage_tracker_key(self, address: Address, slot: int) -> bytes:
        """
        Get the key used to track whether a storage slot has been accessed
        during this transaction.
        """
        return address + int_to_big_endian(slot)

    def _wipe_storage(self, address: Address) -> None:
        """
        Wipe out the storage, without explicitly handling the storage root update
        """
        account_store = self._get_address_store(address)
        self._dirty_accounts.add(address)
        account_store.delete()

    def _dirty_account_stores(
        self,
    ) -> Iterable[Tuple[Address, AccountStorageDB]]:
        for address in self._dirty_accounts:
            store = self._account_stores[address]
            yield address, store

    def _get_storage_root(self, address: Address) -> Hash32:
        account = self._get_account(address)
        return account.storage_root

    def _set_storage_root(self, address: Address, new_storage_root: Hash32) -> None:
        account = self._get_account(address)
        self._set_account(address, account.copy(storage_root=new_storage_root))

    #
    # Balance
    #
    def get_balance(self, address: Address) -> int:
        validate_canonical_address(address, title="Storage Address")

        account = self._get_account(address)
        return account.balance

    def set_balance(self, address: Address, balance: int) -> None:
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(balance, title="Account Balance")

        account = self._get_account(address)
        self._set_account(address, account.copy(balance=balance))

    #
    # Nonce
    #
    def get_nonce(self, address: Address) -> int:
        validate_canonical_address(address, title="Storage Address")

        account = self._get_account(address)
        return account.nonce

    def set_nonce(self, address: Address, nonce: int) -> None:
        validate_canonical_address(address, title="Storage Address")
        validate_uint64(nonce, title="Nonce")

        account = self._get_account(address)
        self._set_account(address, account.copy(nonce=nonce))

    def increment_nonce(self, address: Address) -> None:
        current_nonce = self.get_nonce(address)
        self.set_nonce(address, current_nonce + 1)

    #
    # Code
    #
    def get_code(self, address: Address) -> bytes:
        validate_canonical_address(address, title="Storage Address")

        code_hash = self.get_code_hash(address)
        if code_hash == EMPTY_SHA3:
            return b""
        else:
            try:
                return self._journaldb.get_item(code_hash)
                return self._journaldb[code_hash]
            except KeyError:
                raise Exception(f"can not get the code from address: {address}")
            finally:
                if code_hash in self._journaldb.accessed:
                    self._accessed_bytecodes.add(address)
                # if code_hash in self._get_accessed_node_hashes():
                #     self._accessed_bytecodes.add(address)

    def set_code(self, address: Address, code: bytes) -> None:
        validate_canonical_address(address, title="Storage Address")
        validate_is_bytes(code, title="Code")

        account = self._get_account(address)

        code_hash = keccak(code)
        self._journaldb.set_item(code_hash, code)
        # self._journaldb[code_hash] = code
        self._set_account(address, account.copy(code_hash=code_hash))

    def get_code_hash(self, address: Address) -> Hash32:
        validate_canonical_address(address, title="Storage Address")

        account = self._get_account(address)
        return account.code_hash

    def delete_code(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")

        account = self._get_account(address)
        self._set_account(address, account.copy(code_hash=EMPTY_SHA3))

    #
    # Account Methods
    #
    def account_has_code_or_nonce(self, address: Address) -> bool:
        return self.get_nonce(address) != 0 or self.get_code_hash(address) != EMPTY_SHA3

    def delete_account(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")

        # We must wipe the storage first, because if it's the first time we load it,
        #   then we want to load it with the original storage root hash, not the
        #   empty one. (in case of a later revert, we don't want to poison the
        #   storage cache)
        self._wipe_storage(address)

        if address in self._account_cache:
            del self._account_cache[address]
        # del self._journaltrie[address]
        self._journaltrie.delete_item(address)

    def account_exists(self, address: Address) -> bool:
        validate_canonical_address(address, title="Storage Address")
        account_rlp = self._get_encoded_account(address, from_journal=True)
        return account_rlp is not None

    def touch_account(self, address: Address) -> None:
        validate_canonical_address(address, title="Storage Address")

        account = self._get_account(address)
        self._set_account(address, account)

    def account_is_empty(self, address: Address) -> bool:
        return (
            not self.account_has_code_or_nonce(address)
            and self.get_balance(address) == 0
        )

    #
    # Internal
    #
    def _get_encoded_account(
        self, address: Address, from_journal: bool = True
    ) -> bytes:
        self._accessed_accounts.add(address)
        lookup_trie = self._journaltrie

        try:
            return lookup_trie.get_item(address)
            return lookup_trie[address]
        # except trie_exceptions.MissingTrieNode as exc:
        # raise MissingAccountTrieNode(*exc.args) from exc
        except KeyError:
            # In case the account is deleted in the JournalDB
            return b""

    def _get_account(self, address: Address, from_journal: bool = True) -> Account:
        if from_journal and address in self._account_cache:
            return self._account_cache[address]

        rlp_account = self._get_encoded_account(address, from_journal)

        if rlp_account:
            account = rlp.decode(rlp_account, sedes=Account)
        else:
            account = Account()
        if from_journal:
            self._account_cache[address] = account
        return account

    def _set_account(self, address: Address, account: Account) -> None:
        self._account_cache[address] = account
        rlp_account = rlp.encode(account, sedes=Account)
        self._journaltrie.set_item(address, rlp_account)
        # self._journaltrie[address] = rlp_account

    #
    # Record and discard API
    #
    def record(self) -> DBCheckpoint:
        checkpoint = self._journaldb.record_checkpoint()
        self._journaltrie.record_checkpoint(checkpoint)
        # self._journal_accessed_state.record(checkpoint)

        for _, store in self._dirty_account_stores():
            store.record(checkpoint)
        return checkpoint

    def discard(self, checkpoint: DBCheckpoint) -> None:
        self._journaldb.discard(checkpoint)
        self._journaltrie.discard(checkpoint)
        # self._journal_accessed_state.discard(checkpoint)
        self._account_cache.clear()
        for _, store in self._dirty_account_stores():
            store.discard(checkpoint)

    def commit(self, checkpoint: DBCheckpoint) -> None:
        self._journaldb.commit_checkpoint(checkpoint)
        self._journaltrie.commit_checkpoint(checkpoint)
        # self._journal_accessed_state.commit(checkpoint)
        for _, store in self._dirty_account_stores():
            store.commit(checkpoint)

    def make_state_root(self) -> Hash32:
        return self.state_root

    def persist(self) -> None:
        # persist storage
        for address, store in self._dirty_account_stores():
            store.persist()

        # reset local storage trackers
        self._account_stores = {}
        self._dirty_accounts = set()
        self._accessed_accounts = set()
        self._accessed_bytecodes = set()
        # We have to clear the account cache here so that future account accesses
        #   will get added to _accessed_accounts correctly. Account accesses that
        #   are cached do not add the address to the list of accessed accounts.
        self._account_cache.clear()

        # persist accounts
        new_root_hash = self.state_root
        self.logger.debug2(f"Persisting new state root: 0x{new_root_hash.hex()}")
        self._journaldb.persist()
        self._journaltrie.persist()
        self._root_hash_at_last_persist = new_root_hash
