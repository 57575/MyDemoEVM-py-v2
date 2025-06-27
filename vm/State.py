import contextlib
from typing import (
    Iterator,
    Sequence,
    Tuple,
    Type,
)

from eth_typing import (
    Address,
    BlockNumber,
    Hash32,
)
from eth_utils import ExtendedDebugLogger, get_extended_debug_logger, encode_hex
from eth_utils.toolz import (
    nth,
)


from vm.AbstractClass import (
    AccountDatabaseAPI,
    ComputationAPI,
    ExecutionContextAPI,
    MessageAPI,
    SignedTransactionAPI,
    StateAPI,
    TransactionContextAPI,
    TransactionExecutorAPI,
)
from vm.Exception import ContractCreationCollision
from vm.utils.EVMTyping import (
    DBCheckpoint,
)

from vm.utils.constant import (
    MAX_PREV_HEADER_DEPTH,
    BLOB_BASE_FEE_UPDATE_FRACTION,
    MIN_BLOB_BASE_FEE,
)
from vm.Computation import Computation
from vm.TransactionContext import BaseTransactionContext
from vm.db.Account import AccountDB
from vm.EthereumAPI import EthereumAPI
from vm.transient_storage import TransientStorage


def fake_exponential(
    factor: int, numerator: int, denominator: int, max_iterations: int = 10000
) -> int:
    i = 1
    output = 0
    numerator_accum = factor * denominator
    while numerator_accum > 0 and i < max_iterations:
        output += numerator_accum
        numerator_accum = (numerator_accum * numerator) // (denominator * i)
        i += 1
    return output // denominator


class BaseState(StateAPI):
    #
    # Set from __init__
    #
    __slots__ = ["_db", "execution_context", "_account_db"]

    computation_class: Type[ComputationAPI] = Computation
    transaction_context_class: Type[TransactionContextAPI] = BaseTransactionContext
    account_db_class: Type[AccountDatabaseAPI] = AccountDB
    transaction_executor_class: Type[TransactionExecutorAPI] = None

    _transient_storage: TransientStorage = None

    # def __init__(
    #     self,
    #     db: AtomicDatabaseAPI,
    #     execution_context: ExecutionContextAPI,
    #     state_root: Hash32,
    # ) -> None:
    #     self._db = db
    #     self.execution_context = execution_context
    #     self._account_db = self.get_account_db_class()(db, state_root)

    def __init__(self, engine, execution_context: ExecutionContextAPI) -> None:
        self._engine = engine
        self.execution_context = execution_context
        self._account_db = AccountDB(engine=engine)

    # -- cancun hard fork, transient storage -- #
    @property
    def transient_storage(self) -> TransientStorage:
        if self._transient_storage is None:
            self._transient_storage = TransientStorage()

        return self._transient_storage

    def clear_transient_storage(self) -> None:
        self.transient_storage.clear()

    def get_transient_storage(self, address: Address, slot: int) -> bytes:
        return self.transient_storage.get_transient_storage(address, slot)

    def set_transient_storage(self, address: Address, slot: int, value: bytes) -> None:
        return self.transient_storage.set_transient_storage(address, slot, value)
    
    #
    # Logging
    #
    @property
    def logger(self) -> ExtendedDebugLogger:
        return get_extended_debug_logger(f"eth.vm.state.{self.__class__.__name__}")

    #
    # Access to account db
    #
    @classmethod
    def get_account_db_class(cls) -> Type[AccountDatabaseAPI]:
        if cls.account_db_class is None:
            raise AttributeError(f"No account_db_class set for {cls.__name__}")
        return cls.account_db_class

    @property
    def state_root(self) -> Hash32:
        return self._account_db.state_root

    def make_state_root(self) -> Hash32:
        return self._account_db.make_state_root()

    def get_storage(
        self, address: Address, slot: int, from_journal: bool = True
    ) -> int:
        return self._account_db.get_storage(address, slot, from_journal)

    def set_storage(self, address: Address, slot: int, value: int) -> None:
        return self._account_db.set_storage(address, slot, value)

    def delete_storage(self, address: Address) -> None:
        self._account_db.delete_storage(address)

    def delete_account(self, address: Address) -> None:
        self._account_db.delete_account(address)

    def get_balance(self, address: Address) -> int:
        return self._account_db.get_balance(address)

    def set_balance(self, address: Address, balance: int) -> None:
        self._account_db.set_balance(address, balance)

    def delta_balance(self, address: Address, delta: int) -> None:
        self.set_balance(address, self.get_balance(address) + delta)

    def get_nonce(self, address: Address) -> int:
        return self._account_db.get_nonce(address)

    def set_nonce(self, address: Address, nonce: int) -> None:
        self._account_db.set_nonce(address, nonce)

    def increment_nonce(self, address: Address) -> None:
        self._account_db.increment_nonce(address)

    def get_code(self, address: Address) -> bytes:
        return self._account_db.get_code(address)

    def set_code(self, address: Address, code: bytes) -> None:
        self._account_db.set_code(address, code)

    def get_code_hash(self, address: Address) -> Hash32:
        return self._account_db.get_code_hash(address)

    def delete_code(self, address: Address) -> None:
        self._account_db.delete_code(address)

    def has_code_or_nonce(self, address: Address) -> bool:
        return self._account_db.account_has_code_or_nonce(address)

    def account_exists(self, address: Address) -> bool:
        return self._account_db.account_exists(address)

    def touch_account(self, address: Address) -> None:
        self._account_db.touch_account(address)

    def account_is_empty(self, address: Address) -> bool:
        return self._account_db.account_is_empty(address)

    def is_storage_warm(self, address: Address, slot: int) -> bool:
        return self._account_db.is_storage_warm(address, slot)

    def mark_storage_warm(self, address: Address, slot: int) -> None:
        return self._account_db.mark_storage_warm(address, slot)

    def is_address_warm(self, address: Address) -> bool:
        """
        Was the account accessed during this transaction?

        See EIP-2929
        """
        return (
            self._account_db.is_address_warm(address)
            or address in self.computation_class.get_precompiles()
        )

    def mark_address_warm(self, address: Address) -> None:
        self._account_db.mark_address_warm(address)

    #
    # Access self._chaindb
    #
    def snapshot(self) -> Tuple[Hash32, DBCheckpoint]:
        check_point = self._account_db.record()
        self.transient_storage.record(check_point)
        return (self.state_root, check_point)

    def revert(self, snapshot: Tuple[Hash32, DBCheckpoint]) -> None:
        state_root, account_snapshot = snapshot

        # first revert the database state root.
        self._account_db.state_root = state_root
        # now roll the underlying database back
        self._account_db.discard(account_snapshot)

    def commit(self, snapshot: Tuple[Hash32, DBCheckpoint]) -> None:
        _, checkpoint = snapshot
        self._account_db.commit(checkpoint)
        self.transient_storage.commit(checkpoint)

    def lock_changes(self) -> None:
        self._account_db.lock_changes()

    def persist(self) -> None:
        return self._account_db.persist()

    #
    # Access self.prev_hashes (Read-only)
    # 为了减少header相关API的开发，此处使用公共API代替
    #
    def get_ancestor_hash(self, block_number: int) -> Hash32:
        # raise NotImplementedError("not implement get_ancestor_hash ")
        ancestor_depth = self.block_number - block_number - 1
        is_ancestor_depth_out_of_range = (
            ancestor_depth >= MAX_PREV_HEADER_DEPTH
            or ancestor_depth < 0
            or block_number < 0
        )
        if is_ancestor_depth_out_of_range:
            return Hash32(b"")

        try:
            block = EthereumAPI.get_block_by_number(block_number_hex=hex(block_number))
            return Hash32(bytes.fromhex(block.get("hash")[2:]))
        except StopIteration:
            # Ancestor with specified depth not present
            return Hash32(b"")

    #
    # Computation
    #
    def get_computation(
        self, message: MessageAPI, transaction_context: TransactionContextAPI
    ) -> ComputationAPI:
        if self.computation_class is None:
            raise AttributeError("No `computation_class` has been set for this State")
        else:
            computation = self.computation_class(self, message, transaction_context)
        return computation

    #
    # Transaction context
    #
    @classmethod
    def get_transaction_context_class(cls) -> Type[TransactionContextAPI]:
        if cls.transaction_context_class is None:
            raise AttributeError(
                "No `transaction_context_class` has been set for this State"
            )
        return cls.transaction_context_class

    #
    # Execution
    #
    def apply_transaction(self, transaction: SignedTransactionAPI) -> ComputationAPI:
        raise NotImplementedError(
            "not implement apply_transaction, the simplified EVM does not need to use transaction executor as the entry point for executing transactions "
        )
        executor = self.get_transaction_executor()
        return executor(transaction)

    def validate_transaction(self, transaction: SignedTransactionAPI) -> None:
        raise NotImplementedError(
            "not implement validate_transaction, the simplified EVM does not need to use transaction executor as the entry point for executing transactions "
        )
        validate_frontier_transaction(self, transaction)

    def get_transaction_executor(self) -> TransactionExecutorAPI:
        return self.transaction_executor_class(self)

    def costless_execute_transaction(
        self, transaction: SignedTransactionAPI
    ) -> ComputationAPI:
        with self.override_transaction_context(gas_price=transaction.gas_price):
            free_transaction = transaction.copy(gas_price=0)
            return self.apply_transaction(free_transaction)

    @contextlib.contextmanager
    def override_transaction_context(self, gas_price: int) -> Iterator[None]:
        original_context = self.get_transaction_context

        def get_custom_transaction_context(
            transaction: SignedTransactionAPI,
        ) -> TransactionContextAPI:
            custom_transaction = transaction.copy(gas_price=gas_price)
            return original_context(custom_transaction)

        # mypy doesn't like assigning to an existing method
        self.get_transaction_context = get_custom_transaction_context  # type: ignore
        try:
            yield
        finally:
            self.get_transaction_context = original_context  # type: ignore # Remove ignore if https://github.com/python/mypy/issues/708 is fixed. # noqa: E501

    def get_transaction_context(
        self, transaction: SignedTransactionAPI
    ) -> TransactionContextAPI:
        return self.get_transaction_context_class()(
            gas_price=transaction.gas_price,
            origin=transaction.sender,
        )

    #
    # Block Object Properties (in opcodes)
    #

    @property
    def coinbase(self) -> Address:
        return self.execution_context.coinbase

    @property
    def timestamp(self) -> int:
        return self.execution_context.timestamp

    @property
    def block_number(self) -> BlockNumber:
        return self.execution_context.block_number

    @property
    def difficulty(self) -> int:
        return self.execution_context.difficulty

    @property
    def mix_hash(self) -> Hash32:
        return self.execution_context.mix_hash

    @property
    def gas_limit(self) -> int:
        return self.execution_context.gas_limit

    @property
    def base_fee(self) -> int:
        return self.execution_context.base_fee_per_gas

    def get_tip(self, transaction: SignedTransactionAPI) -> int:
        return transaction.gas_price

    def get_gas_price(self, transaction: SignedTransactionAPI) -> int:
        return transaction.gas_price

    @property
    def blob_base_fee(self) -> int:
        excess_blob_gas = self.execution_context.excess_blob_gas
        return fake_exponential(
            MIN_BLOB_BASE_FEE, excess_blob_gas, BLOB_BASE_FEE_UPDATE_FRACTION
        )

    #
    # Withdrawals
    #

    def apply_withdrawal(self, withdrawal) -> None:
        # withdrawals not implemented until the Shanghai hard fork
        raise NotImplementedError("not implement apply_withdrawal ")
        pass

    def apply_all_withdrawals(self, withdrawals) -> None:
        # withdrawals not implemented until the Shanghai hard fork
        raise NotImplementedError("not implement apply_all_withdrawals ")
        pass

    #
    #
    #
    def build_computation(
        self, message: MessageAPI, transaction_context: TransactionContextAPI
    ) -> ComputationAPI:
        if message.is_create:
            is_collision = self.has_code_or_nonce(message.storage_address)

            if is_collision:
                # The address of the newly created contract has *somehow* collided
                # with an existing contract address.
                computation = self.get_computation(message, transaction_context)
                computation.error = ContractCreationCollision(
                    f"Address collision while creating contract: "
                    f"{encode_hex(message.storage_address)}"
                )
            else:
                computation = self.computation_class.apply_create_message(
                    self,
                    message,
                    transaction_context,
                )
        else:
            computation = self.computation_class.apply_message(
                self,
                message,
                transaction_context,
            )

        return computation


class BaseTransactionExecutor(TransactionExecutorAPI):
    def __init__(self, vm_state: StateAPI) -> None:
        self.vm_state = vm_state

    def __call__(self, transaction: SignedTransactionAPI) -> ComputationAPI:
        self.validate_transaction(transaction)
        message = self.build_evm_message(transaction)
        computation = self.build_computation(message, transaction)
        finalized_computation = self.finalize_computation(transaction, computation)
        return finalized_computation
