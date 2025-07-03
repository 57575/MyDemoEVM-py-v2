from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Callable,
    ContextManager,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    Hashable,
    Iterable,
    MutableMapping,
)
from eth_typing import (
    Address,
    BlockNumber,
    Hash32,
)
from eth_utils import ExtendedDebugLogger

from vm.Exception import (
    VMError,
)

from vm.utils.EVMTyping import BytesOrView, DBCheckpoint
from vm.utils.constant import BLANK_ROOT_HASH

T = TypeVar("T")


class ConfigurableAPI(ABC):
    """
    A class providing inline subclassing.
    """

    @classmethod
    @abstractmethod
    def configure(cls: Type[T], __name__: str = None, **overrides: Any) -> Type[T]: ...


class AccountAPI(ABC):
    """
    A class representing an Ethereum account.
    """

    nonce: int
    balance: int
    storage_root: Hash32
    code_hash: Hash32


class ExecutionContextAPI(ABC):
    """
    A class representing context information that remains constant over the
    execution of a block.
    """

    @property
    @abstractmethod
    def coinbase(self) -> Address:
        """
        Return the coinbase address of the block.
        """
        ...

    @property
    @abstractmethod
    def timestamp(self) -> int:
        """
        Return the timestamp of the block.
        """
        ...

    @property
    @abstractmethod
    def block_number(self) -> BlockNumber:
        """
        Return the number of the block.
        """
        ...

    @property
    @abstractmethod
    def difficulty(self) -> int:
        """
        Return the difficulty of the block.
        """
        ...

    @property
    @abstractmethod
    def mix_hash(self) -> Hash32:
        """
        Return the mix hash of the block
        """
        ...

    @property
    @abstractmethod
    def gas_limit(self) -> int:
        """
        Return the gas limit of the block.
        """
        ...

    # @property
    # @abstractmethod
    # def prev_hashes(self) -> Iterable[Hash32]:
    #     """
    #     Return an iterable of block hashes that precede the block.
    #     """
    #     ...

    @property
    @abstractmethod
    def chain_id(self) -> int:
        """
        Return the id of the chain.
        """
        ...

    @property
    @abstractmethod
    def base_fee_per_gas(self) -> Optional[int]:
        """
        Return the base fee per gas of the block
        """
        ...

    @property
    @abstractmethod
    def excess_blob_gas(self) -> Optional[int]:
        """
        Return the excess blob gas of the block
        """
        ...


class StackManipulationAPI(ABC):
    @abstractmethod
    def stack_pop_ints(self, num_items: int) -> Tuple[int, ...]:
        """
        Pop the last ``num_items`` from the stack,
        returning a tuple of their ordinal values.
        """
        ...

    @abstractmethod
    def stack_pop_bytes(self, num_items: int) -> Tuple[bytes, ...]:
        """
        Pop the last ``num_items`` from the stack, returning a tuple of bytes.
        """
        ...

    @abstractmethod
    def stack_pop_any(self, num_items: int) -> Tuple[Union[int, bytes], ...]:
        """
        Pop the last ``num_items`` from the stack, returning a tuple with potentially
        mixed values of bytes or ordinal values of bytes.
        """
        ...

    @abstractmethod
    def stack_pop1_int(self) -> int:
        """
        Pop one item from the stack and return the ordinal value
        of the represented bytes.
        """
        ...

    @abstractmethod
    def stack_pop1_bytes(self) -> bytes:
        """
        Pop one item from the stack and return the value as ``bytes``.
        """
        ...

    @abstractmethod
    def stack_pop1_any(self) -> Union[int, bytes]:
        """
        Pop one item from the stack and return the value either as byte or the ordinal
        value of a byte.
        """
        ...

    @abstractmethod
    def stack_push_int(self, value: int) -> None:
        """
        Push ``value`` on the stack which must be a 256 bit integer.
        """
        ...

    @abstractmethod
    def stack_push_bytes(self, value: bytes) -> None:
        """
        Push ``value`` on the stack which must be a 32 byte string.
        """
        ...


class OpcodeAPI(ABC):
    """
    A class representing an opcode.
    """

    mnemonic: str

    @abstractmethod
    def __call__(self, computation: "ComputationAPI") -> None:
        """
        Execute the logic of the opcode.
        """
        ...

    @classmethod
    @abstractmethod
    def as_opcode(
        cls: Type[T],
        logic_fn: Callable[["ComputationAPI"], None],
        mnemonic: str,
        gas_cost: int,
    ) -> "OpcodeAPI":
        """
        Class factory method for turning vanilla functions into Opcodes.
        """
        ...


class MemoryAPI(ABC):
    """
    A class representing the memory of the :class:`~eth.abc.VirtualMachineAPI`.
    """

    @abstractmethod
    def extend(self, start_position: int, size: int) -> None:
        """
        Extend the memory from the given ``start_position`` to the provided ``size``.
        """
        ...

    @abstractmethod
    def __len__(self) -> int:
        """
        Return the length of the memory.
        """
        ...

    @abstractmethod
    def write(self, start_position: int, size: int, value: bytes) -> None:
        """
        Write `value` into memory.
        """
        ...

    @abstractmethod
    def read(self, start_position: int, size: int) -> memoryview:
        """
        Return a view into the memory
        """
        ...

    @abstractmethod
    def read_bytes(self, start_position: int, size: int) -> bytes:
        """
        Read a value from memory and return a fresh bytes instance
        """
        ...

    @abstractmethod
    def copy(self, destination: int, source: int, length: int) -> bytes:
        """
        Copy bytes of memory with size ``length`` from ``source`` to ``destination``
        """
        ...


class StackAPI(ABC):
    """
    A class representing the stack of the :class:`~eth.abc.VirtualMachineAPI`.
    """

    @abstractmethod
    def push_int(self, value: int) -> None:
        """
        Push an integer item onto the stack.
        """
        ...

    @abstractmethod
    def push_bytes(self, value: bytes) -> None:
        """
        Push a bytes item onto the stack.
        """
        ...

    @abstractmethod
    def pop1_bytes(self) -> bytes:
        """
        Pop and return a bytes element from the stack.

        Raise `eth.exceptions.InsufficientStack` if the stack was empty.
        """
        ...

    @abstractmethod
    def pop1_int(self) -> int:
        """
        Pop and return an integer from the stack.

        Raise `eth.exceptions.InsufficientStack` if the stack was empty.
        """
        ...

    @abstractmethod
    def pop1_any(self) -> Union[int, bytes]:
        """
        Pop and return an element from the stack.
        The type of each element will be int or bytes, depending on whether it was
        pushed with push_bytes or push_int.

        Raise `eth.exceptions.InsufficientStack` if the stack was empty.
        """
        ...

    @abstractmethod
    def pop_any(self, num_items: int) -> Tuple[Union[int, bytes], ...]:
        """
        Pop and return a tuple of items of length ``num_items`` from the stack.
        The type of each element will be int or bytes, depending on whether it was
        pushed with stack_push_bytes or stack_push_int.

        Raise `eth.exceptions.InsufficientStack` if there are not enough items on
        the stack.

        Items are ordered with the top of the stack as the first item in the tuple.
        """
        ...

    @abstractmethod
    def pop_ints(self, num_items: int) -> Tuple[int, ...]:
        """
        Pop and return a tuple of integers of length ``num_items`` from the stack.

        Raise `eth.exceptions.InsufficientStack` if there are not enough items on
        the stack.

        Items are ordered with the top of the stack as the first item in the tuple.
        """
        ...

    @abstractmethod
    def pop_bytes(self, num_items: int) -> Tuple[bytes, ...]:
        """
        Pop and return a tuple of bytes of length ``num_items`` from the stack.

        Raise `eth.exceptions.InsufficientStack` if there are not enough items on
        the stack.

        Items are ordered with the top of the stack as the first item in the tuple.
        """
        ...

    @abstractmethod
    def swap(self, position: int) -> None:
        """
        Perform a SWAP operation on the stack.
        """
        ...

    @abstractmethod
    def dup(self, position: int) -> None:
        """
        Perform a DUP operation on the stack.
        """
        ...

    @abstractmethod
    def size(self) -> None: ...


class GasMeterAPI(ABC):
    """
    A class to define a gas meter.
    """

    start_gas: int
    gas_refunded: int
    gas_remaining: int

    #
    # Write API
    #
    @abstractmethod
    def consume_gas(self, amount: int, reason: str) -> None:
        """
        Consume ``amount`` of gas for a defined ``reason``.
        """
        ...

    @abstractmethod
    def return_gas(self, amount: int) -> None:
        """
        Return ``amount`` of gas.
        """
        ...

    @abstractmethod
    def refund_gas(self, amount: int) -> None:
        """
        Refund ``amount`` of gas.
        """
        ...


class CodeStreamAPI(ABC):
    """
    A class representing a stream of EVM code.
    """

    program_counter: int

    @abstractmethod
    def read(self, size: int) -> bytes:
        """
        Read and return the code from the current position of the cursor up to ``size``.
        """
        ...

    @abstractmethod
    def __len__(self) -> int:
        """
        Return the length of the code stream.
        """
        ...

    @abstractmethod
    def __getitem__(self, index: int) -> int:
        """
        Return the ordinal value of the byte at the given ``index``.
        """
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[int]:
        """
        Iterate over all ordinal values of the bytes of the code stream.
        """
        ...

    @abstractmethod
    def peek(self) -> int:
        """
        Return the ordinal value of the byte at the current program counter.
        """
        ...

    @abstractmethod
    def seek(self, program_counter: int) -> ContextManager["CodeStreamAPI"]:
        """
        Return a :class:`~typing.ContextManager` with the program counter
        set to ``program_counter``.
        """
        ...

    @abstractmethod
    def is_valid_opcode(self, position: int) -> bool:
        """
        Return ``True`` if a valid opcode exists at ``position``.
        """
        ...


class MessageAPI(ABC):
    """
    A message for VM computation.
    """

    code: bytes
    _code_address: Address
    create_address: Address
    data: BytesOrView
    depth: int
    gas: int
    is_static: bool
    sender: Address
    should_transfer_value: bool
    _storage_address: Address
    to: Address
    value: int

    __slots__ = [
        "code",
        "_code_address",
        "create_address",
        "data",
        "depth",
        "gas",
        "is_static",
        "sender",
        "should_transfer_value",
        "_storage_address" "to",
        "value",
    ]

    @property
    @abstractmethod
    def code_address(self) -> Address: ...

    @property
    @abstractmethod
    def storage_address(self) -> Address: ...

    @property
    @abstractmethod
    def is_create(self) -> bool: ...

    @property
    @abstractmethod
    def data_as_bytes(self) -> bytes: ...


class BaseTransactionAPI(ABC):
    """
    A class to define all common methods of a transaction.
    """

    @abstractmethod
    def validate(self) -> None:
        """
        Hook called during instantiation to ensure that all transaction
        parameters pass validation rules.
        """
        ...

    @property
    @abstractmethod
    def intrinsic_gas(self) -> int:
        """
        Convenience property for the return value of `get_intrinsic_gas`
        """
        ...

    @abstractmethod
    def get_intrinsic_gas(self) -> int:
        """
        Return the intrinsic gas for the transaction which is defined as the amount of
        gas that is needed before any code runs.
        """
        ...

    @abstractmethod
    def gas_used_by(self, computation: "ComputationAPI") -> int:
        """
        Return the gas used by the given computation. In Frontier,
        for example, this is sum of the intrinsic cost and the gas used
        during computation.
        """
        ...

    # We can remove this API and inherit from rlp.Serializable when it becomes typesafe
    @abstractmethod
    def copy(self: T, **overrides: Any) -> T:
        """
        Return a copy of the transaction.
        """
        ...

    @property
    @abstractmethod
    def access_list(self) -> Sequence[Tuple[Address, Sequence[int]]]:
        """
        Get addresses to be accessed by a transaction, and their storage slots.
        """
        ...


class TransactionFieldsAPI(ABC):
    """
    A class to define all common transaction fields.
    """

    @property
    @abstractmethod
    def nonce(self) -> int: ...

    @property
    @abstractmethod
    def gas_price(self) -> int:
        """
        Will raise :class:`AttributeError` if get or set on a 1559 transaction.
        """
        ...

    @property
    @abstractmethod
    def max_fee_per_gas(self) -> int:
        """
        Will default to gas_price if this is a pre-1559 transaction.
        """
        ...

    @property
    @abstractmethod
    def max_priority_fee_per_gas(self) -> int:
        """
        Will default to gas_price if this is a pre-1559 transaction.
        """
        ...

    @property
    @abstractmethod
    def gas(self) -> int: ...

    @property
    @abstractmethod
    def to(self) -> Address: ...

    @property
    @abstractmethod
    def value(self) -> int: ...

    @property
    @abstractmethod
    def data(self) -> bytes: ...

    @property
    @abstractmethod
    def r(self) -> int: ...

    @property
    @abstractmethod
    def s(self) -> int: ...

    @property
    @abstractmethod
    def hash(self) -> Hash32:
        """
        Return the hash of the transaction.
        """
        ...

    @property
    @abstractmethod
    def chain_id(self) -> Optional[int]: ...

    @property
    @abstractmethod
    def max_fee_per_blob_gas(self) -> int: ...

    @property
    @abstractmethod
    def blob_versioned_hashes(self) -> Sequence[Hash32]: ...


class SignedTransactionAPI(BaseTransactionAPI, TransactionFieldsAPI):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    """
    A class representing a transaction that was signed with a private key.
    """

    @property
    @abstractmethod
    def sender(self) -> Address:
        """
        Convenience and performance property for the return value of `get_sender`
        """
        ...

    @property
    @abstractmethod
    def y_parity(self) -> int:
        """
        The bit used to disambiguate elliptic curve signatures.

        The only values this method will return are 0 or 1.
        """
        ...

    type_id: Optional[int]
    """
    The type of EIP-2718 transaction

    Each EIP-2718 transaction includes a type id (which is the leading
    byte, as encoded).

    If this transaction is a legacy transaction, that it has no type. Then,
    type_id will be None.
    """

    # +-------------------------------------------------------------+
    # | API that must be implemented by all Transaction subclasses. |
    # +-------------------------------------------------------------+

    #
    # Validation
    #
    @abstractmethod
    def validate(self) -> None:
        """
        Hook called during instantiation to ensure that all transaction
        parameters pass validation rules.
        """
        ...

    #
    # Signature and Sender
    #
    @property
    @abstractmethod
    def is_signature_valid(self) -> bool:
        """
        Return ``True`` if the signature is valid, otherwise ``False``.
        """
        ...

    @abstractmethod
    def check_signature_validity(self) -> None:
        """
        Check if the signature is valid. Raise a ``ValidationError`` if the signature
        is invalid.
        """
        ...

    @abstractmethod
    def get_sender(self) -> Address:
        """
        Get the 20-byte address which sent this transaction.

        This can be a slow operation. ``transaction.sender`` is always preferred.
        """
        ...

    #
    # Conversion to and creation of unsigned transactions.
    #
    @abstractmethod
    def get_message_for_signing(self) -> bytes:
        """
        Return the bytestring that should be signed in order to create a signed
        transaction.
        """
        ...

    # We can remove this API and inherit from rlp.Serializable when it becomes typesafe
    def as_dict(self) -> Dict[Hashable, Any]:
        """
        Return a dictionary representation of the transaction.
        """
        ...

    # @abstractmethod
    # def make_receipt(
    #     self,
    #     status: bytes,
    #     gas_used: int,
    #     log_entries: Tuple[Tuple[bytes, Tuple[int, ...], bytes], ...],
    # ) -> ReceiptAPI:
    #     """
    #     Build a receipt for this transaction.

    #     Transactions have this responsibility because there are different types
    #     of transactions, which have different types of receipts. (See
    #     access-list transactions, which change the receipt encoding)

    #     :param status: success or failure (used to be the state root after execution)
    #     :param gas_used: cumulative usage of this transaction and the previous
    #         ones in the header
    #     :param log_entries: logs generated during execution
    #     """
    #     ...

    @abstractmethod
    def encode(self) -> bytes:
        """
        This encodes a transaction, no matter if it's: a legacy transaction, a
        typed transaction, or the payload of a typed transaction. See more
        context in decode.
        """
        ...


class TransactionContextAPI(ABC):
    """
    Immutable transaction context information that remains constant over the
    VM execution.
    """

    @abstractmethod
    def __init__(self, gas_price: int, origin: Address) -> None:
        """
        Initialize the transaction context from the given ``gas_price`` and
        ``origin`` address.
        """
        ...

    @abstractmethod
    def get_next_log_counter(self) -> int:
        """
        Increment and return the log counter.
        """
        ...

    @property
    @abstractmethod
    def gas_price(self) -> int:
        """
        Return the gas price of the transaction context.
        """
        ...

    @property
    @abstractmethod
    def origin(self) -> Address:
        """
        Return the origin of the transaction context.
        """
        ...

    @property
    @abstractmethod
    def blob_versioned_hashes(self) -> Sequence[Hash32]:
        """
        Return the blob versioned hashes of the transaction context.
        """
        ...


class TransactionExecutorAPI(ABC):
    """
    A class providing APIs to execute transactions on VM state.
    """

    @abstractmethod
    def __init__(self, vm_state: "StateAPI") -> None:
        """
        Initialize the executor from the given ``vm_state``.
        """
        ...

    @abstractmethod
    def __call__(self, transaction: SignedTransactionAPI) -> "ComputationAPI":
        """
        Execute the ``transaction`` and return a :class:`eth.abc.ComputationAPI`.
        """
        ...

    @abstractmethod
    def validate_transaction(self, transaction: SignedTransactionAPI) -> None:
        """
        Validate the given ``transaction``.
        Raise a ``ValidationError`` if the transaction is invalid.
        """
        ...

    @abstractmethod
    def build_evm_message(self, transaction: SignedTransactionAPI) -> MessageAPI:
        """
        Build and return a :class:`~eth.abc.MessageAPI` from the given ``transaction``.
        """
        ...

    @abstractmethod
    def build_computation(
        self, message: MessageAPI, transaction: SignedTransactionAPI
    ) -> "ComputationAPI":
        """
        Apply the ``message`` to the VM and use the given ``transaction`` to
        retrieve the context from.
        """
        ...

    @abstractmethod
    def finalize_computation(
        self, transaction: SignedTransactionAPI, computation: "ComputationAPI"
    ) -> "ComputationAPI":
        """
        Finalize the ``transaction``.
        """
        ...


class TransientStorageAPI(ABC):
    @abstractmethod
    def record(self, checkpoint: DBCheckpoint) -> None:
        """
        Record changes into the given ``checkpoint``.
        """
        ...

    @abstractmethod
    def commit(self, snapshot: DBCheckpoint) -> None:
        """
        Commit the given ``checkpoint``.
        """
        ...

    @abstractmethod
    def discard(self, snapshot: DBCheckpoint) -> None:
        """
        Discard the given ``checkpoint``.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """
        Clear the transient storage.
        """
        ...

    @abstractmethod
    def get_transient_storage(self, address: Address, slot: int) -> bytes:
        """
        Return the transient storage for ``address`` at slot ``slot``.
        """
        ...

    @abstractmethod
    def set_transient_storage(self, address: Address, slot: int, value: bytes) -> None:
        """
        Return the transient storage for ``address`` at slot ``slot``.
        """
        ...


class DatabaseAPI(MutableMapping[bytes, bytes], ABC):
    """
    A class representing a database.
    """

    @abstractmethod
    def set(self, key: bytes, value: bytes) -> None:
        """
        Assign the ``value`` to the ``key``.
        """
        ...

    @abstractmethod
    def exists(self, key: bytes) -> bool:
        """
        Return ``True`` if the ``key`` exists in the database, otherwise ``False``.
        """
        ...

    @abstractmethod
    def delete(self, key: bytes) -> None:
        """
        Delete the given ``key`` from the database.
        """
        ...


class AtomicDatabaseAPI(DatabaseAPI):
    """
    Like ``BatchDB``, but immediately write out changes if they are
    not in an ``atomic_batch()`` context.
    """

    # @abstractmethod
    # def atomic_batch(self) -> ContextManager[AtomicWriteBatchAPI]:
    #     """
    #     Return a :class:`~typing.ContextManager` to write an atomic batch to the
    #     database.
    #     """
    #     ...


class AccountDatabaseAPI(ABC):
    """
    A class representing a database for accounts.
    """

    @abstractmethod
    def __init__(
        self, db: AtomicDatabaseAPI, state_root: Hash32 = BLANK_ROOT_HASH
    ) -> None:
        """
        Initialize the account database.
        """
        ...

    @property
    @abstractmethod
    def state_root(self) -> Hash32:
        """
        Return the state root hash.
        """
        ...

    @state_root.setter
    def state_root(self, value: Hash32) -> None:
        """
        Force-set the state root hash.
        """
        # See: https://github.com/python/mypy/issues/4165
        # Since we can't also decorate this with abstract method we want to be
        # sure that the setter doesn't actually get used as a noop.
        raise NotImplementedError

    #
    # Storage
    #
    @abstractmethod
    def get_storage(
        self, address: Address, slot: int, from_journal: bool = True
    ) -> int:
        """
        Return the value stored at ``slot`` for the given ``address``. Take the journal
        into consideration unless ``from_journal`` is set to ``False``.
        """
        ...

    @abstractmethod
    def set_storage(self, address: Address, slot: int, value: int) -> None:
        """
        Write ``value`` into ``slot`` for the given ``address``.
        """
        ...

    @abstractmethod
    def delete_storage(self, address: Address) -> None:
        """
        Delete the storage at ``address``.
        """
        ...

    @abstractmethod
    def is_storage_warm(self, address: Address, slot: int) -> bool:
        """
        Was the storage slot accessed during this transaction?

        See EIP-2929
        """
        ...

    @abstractmethod
    def mark_storage_warm(self, address: Address, slot: int) -> None:
        """
        Mark the storage slot as accessed during this transaction.

        See EIP-2929
        """
        ...

    #
    # Balance
    #
    @abstractmethod
    def get_balance(self, address: Address) -> int:
        """
        Return the balance at ``address``.
        """
        ...

    @abstractmethod
    def set_balance(self, address: Address, balance: int) -> None:
        """
        Set ``balance`` as the new balance for ``address``.
        """
        ...

    #
    # Nonce
    #
    @abstractmethod
    def get_nonce(self, address: Address) -> int:
        """
        Return the nonce for ``address``.
        """
        ...

    @abstractmethod
    def set_nonce(self, address: Address, nonce: int) -> None:
        """
        Set ``nonce`` as the new nonce for ``address``.
        """
        ...

    @abstractmethod
    def increment_nonce(self, address: Address) -> None:
        """
        Increment the nonce for ``address``.
        """
        ...

    #
    # Code
    #
    @abstractmethod
    def set_code(self, address: Address, code: bytes) -> None:
        """
        Set ``code`` as the new code at ``address``.
        """
        ...

    @abstractmethod
    def get_code(self, address: Address) -> bytes:
        """
        Return the code at the given ``address``.
        """
        ...

    @abstractmethod
    def get_code_hash(self, address: Address) -> Hash32:
        """
        Return the hash of the code at ``address``.
        """
        ...

    @abstractmethod
    def delete_code(self, address: Address) -> None:
        """
        Delete the code at ``address``.
        """
        ...

    #
    # Account Methods
    #
    @abstractmethod
    def account_has_code_or_nonce(self, address: Address) -> bool:
        """
        Return ``True`` if either code or a nonce exists at ``address``.
        """
        ...

    @abstractmethod
    def delete_account(self, address: Address) -> None:
        """
        Delete the account at ``address``.
        """
        ...

    @abstractmethod
    def account_exists(self, address: Address) -> bool:
        """
        Return ``True`` if an account exists at ``address``, otherwise ``False``.
        """
        ...

    @abstractmethod
    def touch_account(self, address: Address) -> None:
        """
        Touch the account at ``address``.
        """
        ...

    @abstractmethod
    def account_is_empty(self, address: Address) -> bool:
        """
        Return ``True`` if an account exists at ``address``.
        """
        ...

    #
    # Record and discard API
    #
    @abstractmethod
    def record(self) -> DBCheckpoint:
        """
        Create and return a new checkpoint.
        """
        ...

    @abstractmethod
    def discard(self, checkpoint: DBCheckpoint) -> None:
        """
        Discard the given ``checkpoint``.
        """
        ...

    @abstractmethod
    def commit(self, checkpoint: DBCheckpoint) -> None:
        """
        Collapse changes into ``checkpoint``.
        """
        ...

    @abstractmethod
    def make_state_root(self) -> Hash32:
        """
        Generate the state root with all the current changes in AccountDB

        Current changes include every pending change to storage, as well as all account
        changes. After generating all the required tries, the final account state root
        is returned.

        This is an expensive operation, so should be called as little as possible.
        For example, pre-Byzantium, this is called after every transaction, because we
        need the state root in each receipt. Byzantium+, we only need state roots at
        the end of the block, so we *only* call it right before persistence.

        :return: the new state root
        """
        ...

    @abstractmethod
    def persist(self) -> None:
        """
        Send changes to underlying database, including the trie state
        so that it will forever be possible to read the trie from this checkpoint.

        :meth:`make_state_root` must be explicitly called before this method.
        Otherwise persist will raise a ValidationError.
        """
        ...


class ComputationAPI(
    ContextManager["ComputationAPI"],
    StackManipulationAPI,
):
    """
    The base abstract class for all execution computations.
    """

    logger: ExtendedDebugLogger

    state: "StateAPI"
    msg: MessageAPI
    transaction_context: TransactionContextAPI
    code: CodeStreamAPI
    children: List["ComputationAPI"]
    return_data: bytes = b""
    accounts_to_delete: List[Address]
    beneficiaries: List[Address]
    contracts_created: List[Address] = []

    _memory: MemoryAPI
    _stack: StackAPI
    _error: VMError
    _output: bytes = b""
    _log_entries: List[Tuple[int, Address, Tuple[int, ...], bytes]]

    # VM configuration
    opcodes: Dict[int, OpcodeAPI]
    _precompiles: Dict[Address, Callable[["ComputationAPI"], "ComputationAPI"]]

    @abstractmethod
    def __init__(
        self,
        state: "StateAPI",
        message: MessageAPI,
        transaction_context: TransactionContextAPI,
    ) -> None:
        """
        Instantiate the computation.
        """
        ...

    @abstractmethod
    def get_debug_logger(self) -> ExtendedDebugLogger:
        """
        get the logger in the instance
        """
        ...

    # -- convenience -- #
    @property
    @abstractmethod
    def is_origin_computation(self) -> bool:
        """
        Return ``True`` if this computation is the outermost computation at
        ``depth == 0``.
        """
        ...

    # -- error handling -- #
    @property
    @abstractmethod
    def is_success(self) -> bool:
        """
        Return ``True`` if the computation did not result in an error.
        """
        ...

    @property
    @abstractmethod
    def is_error(self) -> bool:
        """
        Return ``True`` if the computation resulted in an error.
        """
        ...

    @property
    @abstractmethod
    def error(self) -> VMError:
        """
        Return the :class:`~eth.exceptions.VMError` of the computation.
        Raise ``AttributeError`` if no error exists.
        """
        ...

    @error.setter
    def error(self, value: VMError) -> None:
        """
        Set an :class:`~eth.exceptions.VMError` for the computation.
        """
        # See: https://github.com/python/mypy/issues/4165
        # Since we can't also decorate this with abstract method we want to be
        # sure that the setter doesn't actually get used as a noop.
        raise NotImplementedError

    @abstractmethod
    def raise_if_error(self) -> None:
        """
        If there was an error during computation, raise it as an exception immediately.

        :raise VMError:
        """
        ...

    # -- memory management -- #
    @abstractmethod
    def extend_memory(self, start_position: int, size: int) -> None:
        """
        Extend the size of the memory to be at minimum ``start_position + size``
        bytes in length.  Raise `eth.exceptions.OutOfGas` if there is not enough
        gas to pay for extending the memory.
        """
        ...

    @abstractmethod
    def memory_write(self, start_position: int, size: int, value: bytes) -> None:
        """
        Write ``value`` to memory at ``start_position``. Require that
        ``len(value) == size``.
        """
        ...

    @abstractmethod
    def memory_read_bytes(self, start_position: int, size: int) -> bytes:
        """
        Read and return ``size`` bytes from memory starting at ``start_position``.
        """
        ...

    @abstractmethod
    def memory_copy(self, destination: int, source: int, length: int) -> bytes:
        """
        Copy bytes of memory with size ``length`` from ``source`` to ``destination``
        """
        ...

    # -- gas consumption -- #
    @abstractmethod
    def get_gas_meter(self) -> GasMeterAPI:
        """
        Return the gas meter for the computation.
        """
        ...

    @abstractmethod
    def consume_gas(self, amount: int, reason: str) -> None:
        """
        Consume ``amount`` of gas from the remaining gas.
        Raise `eth.exceptions.OutOfGas` if there is not enough gas remaining.
        """
        ...

    @abstractmethod
    def return_gas(self, amount: int) -> None:
        """
        Return ``amount`` of gas to the available gas pool.
        """
        ...

    @abstractmethod
    def refund_gas(self, amount: int) -> None:
        """
        Add ``amount`` of gas to the pool of gas marked to be refunded.
        """
        ...

    @abstractmethod
    def get_gas_used(self) -> int:
        """
        Return the number of used gas.
        """
        ...

    @abstractmethod
    def get_gas_remaining(self) -> int:
        """
        Return the number of remaining gas.
        """
        ...

    # -- stack management -- #
    @abstractmethod
    def stack_swap(self, position: int) -> None:
        """
        Swap the item on the top of the stack with the item at ``position``.
        """
        ...

    @abstractmethod
    def stack_dup(self, position: int) -> None:
        """
        Duplicate the stack item at ``position`` and pushes it onto the stack.
        """
        ...

    # -- computation result -- #
    @property
    @abstractmethod
    def output(self) -> bytes:
        """
        Get the return value of the computation.
        """
        ...

    @output.setter
    def output(self, value: bytes) -> None:
        """
        Set the return value of the computation.
        """
        # See: https://github.com/python/mypy/issues/4165
        # Since we can't also decorate this with abstract method we want to be
        # sure that the setter doesn't actually get used as a noop.
        raise NotImplementedError

    # -- opcode API -- #
    @property
    @abstractmethod
    def precompiles(self) -> Dict[Address, Callable[["ComputationAPI"], None]]:
        """
        Return a dictionary where the keys are the addresses of precompiles and the
        values are the precompile functions.
        """
        ...

    @classmethod
    @abstractmethod
    def get_precompiles(cls) -> Dict[Address, Callable[["ComputationAPI"], None]]:
        """
        Return a dictionary where the keys are the addresses of precompiles and the
        values are the precompile functions.
        """
        ...

    @abstractmethod
    def get_opcode_fn(self, opcode: int) -> OpcodeAPI:
        """
        Return the function for the given ``opcode``.
        """
        ...

    # -- runtime operations -- #
    @abstractmethod
    def prepare_child_message(
        self,
        gas: int,
        to: Address,
        value: int,
        data: BytesOrView,
        code: bytes,
        **kwargs: Any,
    ) -> MessageAPI:
        """
        Helper method for creating a child computation.
        """
        ...

    @abstractmethod
    def apply_child_computation(
        self,
        child_msg: MessageAPI,
    ) -> "ComputationAPI":
        """
        Apply the vm message ``child_msg`` as a child computation.
        """
        ...

    @abstractmethod
    def generate_child_computation(
        self,
        child_msg: MessageAPI,
    ) -> "ComputationAPI":
        """
        Generate a child computation from the given ``child_msg``.
        """
        ...

    @abstractmethod
    def add_child_computation(
        self,
        child_computation: "ComputationAPI",
    ) -> None:
        """
        Add the given ``child_computation``.
        """
        ...

    # -- account management -- #
    @abstractmethod
    def register_account_for_deletion(self, beneficiary: Address) -> None:
        """
        Register the address of ``beneficiary`` for deletion.
        """
        ...

    @abstractmethod
    def get_accounts_for_deletion(self) -> List[Address]:
        """
        Return a tuple of addresses that are registered for deletion.
        """
        ...

    @abstractmethod
    def get_self_destruct_beneficiaries(self) -> List[Address]:
        """
        Return a list of addresses that were beneficiaries of the self-destruct
        opcode - whether or not the contract was self-destructed, post-Cancun.
        """
        ...

    # -- EVM logging -- #
    @abstractmethod
    def add_log_entry(
        self, account: Address, topics: Tuple[int, ...], data: bytes
    ) -> None:
        """
        Add a log entry.
        """
        ...

    @abstractmethod
    def get_raw_log_entries(
        self,
    ) -> Tuple[Tuple[int, bytes, Tuple[int, ...], bytes], ...]:
        """
        Return a tuple of raw log entries.
        """
        ...

    @abstractmethod
    def get_log_entries(self) -> Tuple[Tuple[bytes, Tuple[int, ...], bytes], ...]:
        """
        Return the log entries for this computation and its children.

        They are sorted in the same order they were emitted during the transaction
        processing, and include the sequential counter as the first element of the
        tuple representing every entry.
        """
        ...

    # -- state transition -- #
    @classmethod
    @abstractmethod
    def apply_message(
        cls,
        state: "StateAPI",
        message: MessageAPI,
        transaction_context: TransactionContextAPI,
        parent_computation: Optional["ComputationAPI"] = None,
    ) -> "ComputationAPI":
        """
        Execute a VM message. This is where the VM-specific call logic exists.
        """
        ...

    @classmethod
    @abstractmethod
    def apply_create_message(
        cls,
        state: "StateAPI",
        message: MessageAPI,
        transaction_context: TransactionContextAPI,
        parent_computation: Optional["ComputationAPI"] = None,
    ) -> "ComputationAPI":
        """
        Execute a VM message to create a new contract. This is where the VM-specific
        create logic exists.
        """
        ...

    @classmethod
    @abstractmethod
    def apply_computation(
        cls,
        state: "StateAPI",
        message: MessageAPI,
        transaction_context: TransactionContextAPI,
    ) -> "ComputationAPI":
        """
        Execute the logic within the message: Either run the precompile, or
        step through each opcode.  Generally, the only VM-specific logic is for
        each opcode as it executes.

        This should rarely be called directly, because it will skip over other
        important VM-specific logic that happens before or after the execution.

        Instead, prefer :meth:`~apply_message` or :meth:`~apply_create_message`.
        """
        ...


class StateAPI(ABC):
    """
    The base class that encapsulates all of the various moving parts related to
    the state of the VM during execution.
    Each :class:`~eth.abc.VirtualMachineAPI` must be configured with a subclass of the
    :class:`~eth.abc.StateAPI`.

      .. note::

        Each :class:`~eth.abc.StateAPI` class must be configured with:

        - ``computation_class``: The :class:`~eth.abc.ComputationAPI` class for
          vm execution.
        - ``transaction_context_class``: The :class:`~eth.abc.TransactionContextAPI`
          class for vm execution.
    """

    #
    # Set from __init__
    #
    execution_context: ExecutionContextAPI

    computation_class: Type[ComputationAPI]
    transaction_context_class: Type[TransactionContextAPI]
    account_db_class: Type[AccountDatabaseAPI]
    transaction_executor_class: Type[TransactionExecutorAPI] = None

    @abstractmethod
    def __init__(self, engine, execution_context: ExecutionContextAPI) -> None:
        """
        Initialize the state.
        """
        ...

    #
    # Block Object Properties (in opcodes)
    #
    @property
    @abstractmethod
    def coinbase(self) -> Address:
        """
        Return the current ``coinbase`` from the current :attr:`~execution_context`
        """
        ...

    @property
    @abstractmethod
    def timestamp(self) -> int:
        """
        Return the current ``timestamp`` from the current :attr:`~execution_context`
        """
        ...

    @property
    @abstractmethod
    def block_number(self) -> BlockNumber:
        """
        Return the current ``block_number`` from the current :attr:`~execution_context`
        """
        ...

    @property
    @abstractmethod
    def difficulty(self) -> int:
        """
        Return the current ``difficulty`` from the current :attr:`~execution_context`
        """
        ...

    @property
    @abstractmethod
    def mix_hash(self) -> Hash32:
        """
        Return the current ``mix_hash`` from the current :attr:`~execution_context`
        """
        ...

    @property
    @abstractmethod
    def gas_limit(self) -> int:
        """
        Return the current ``gas_limit`` from the current :attr:`~transaction_context`
        """
        ...

    @property
    @abstractmethod
    def base_fee(self) -> int:
        """
        Return the current ``base_fee`` from the current :attr:`~execution_context`

        Raises a ``NotImplementedError`` if called in an execution context
        prior to the London hard fork.
        """
        ...

    @abstractmethod
    def get_gas_price(self, transaction: SignedTransactionAPI) -> int:
        """
        Return the gas price of the given transaction.

        Factor in the current block's base gas price, if appropriate. (See EIP-1559)
        """
        ...

    @abstractmethod
    def get_tip(self, transaction: SignedTransactionAPI) -> int:
        """
        Return the gas price that gets allocated to the miner/validator.

        Pre-EIP-1559 that would be the full transaction gas price. After, it
        would be the tip price (potentially reduced, if the base fee is so high
        that it surpasses the transaction's maximum gas price after adding the
        tip).
        """
        ...

    @property
    @abstractmethod
    def blob_base_fee(self) -> int:
        """
        Return the current ``blob_base_fee`` from the current :attr:`~execution_context`

        Raises a ``NotImplementedError`` if called in an execution context
        prior to the Cancun hard fork.
        """
        ...

    #
    # Access to accoun db
    #
    @classmethod
    @abstractmethod
    def get_account_db_class(cls) -> Type[AccountDatabaseAPI]:
        """
        Return the :class:`~eth.abc.AccountDatabaseAPI` class that the
        state class uses
        """
        ...

    @property
    @abstractmethod
    def state_root(self) -> Hash32:
        """
        Return the current ``state_root`` from the underlying database
        """
        ...

    @abstractmethod
    def make_state_root(self) -> Hash32:
        """
        Create and return the state root.
        """
        ...

    @abstractmethod
    def get_storage(
        self, address: Address, slot: int, from_journal: bool = True
    ) -> int:
        """
        Return the storage at ``slot`` for ``address``.
        """
        ...

    @abstractmethod
    def set_storage(self, address: Address, slot: int, value: int) -> None:
        """
        Write ``value`` to the given ``slot`` at ``address``.
        """
        ...

    @abstractmethod
    def delete_storage(self, address: Address) -> None:
        """
        Delete the storage at ``address``
        """
        ...

    @abstractmethod
    def delete_account(self, address: Address) -> None:
        """
        Delete the account at the given ``address``.
        """
        ...

    @abstractmethod
    def get_balance(self, address: Address) -> int:
        """
        Return the balance for the account at ``address``.
        """
        ...

    @abstractmethod
    def set_balance(self, address: Address, balance: int) -> None:
        """
        Set ``balance`` to the balance at ``address``.
        """
        ...

    @abstractmethod
    def delta_balance(self, address: Address, delta: int) -> None:
        """
        Apply ``delta`` to the balance at ``address``.
        """
        ...

    @abstractmethod
    def get_nonce(self, address: Address) -> int:
        """
        Return the nonce at ``address``.
        """
        ...

    @abstractmethod
    def set_nonce(self, address: Address, nonce: int) -> None:
        """
        Set ``nonce`` as the new nonce at ``address``.
        """
        ...

    @abstractmethod
    def increment_nonce(self, address: Address) -> None:
        """
        Increment the nonce at ``address``.
        """
        ...

    @abstractmethod
    def get_code(self, address: Address) -> bytes:
        """
        Return the code at ``address``.
        """
        ...

    @abstractmethod
    def set_code(self, address: Address, code: bytes) -> None:
        """
        Set ``code`` as the new code at ``address``.
        """
        ...

    @abstractmethod
    def get_code_hash(self, address: Address) -> Hash32:
        """
        Return the hash of the code at ``address``.
        """
        ...

    @abstractmethod
    def delete_code(self, address: Address) -> None:
        """
        Delete the code at ``address``.
        """
        ...

    @abstractmethod
    def has_code_or_nonce(self, address: Address) -> bool:
        """
        Return ``True`` if either a nonce or code exists at the given ``address``.
        """
        ...

    @abstractmethod
    def account_exists(self, address: Address) -> bool:
        """
        Return ``True`` if an account exists at ``address``.
        """
        ...

    @abstractmethod
    def touch_account(self, address: Address) -> None:
        """
        Touch the account at the given ``address``.
        """
        ...

    @abstractmethod
    def account_is_empty(self, address: Address) -> bool:
        """
        Return ``True`` if the account at ``address`` is empty, otherwise ``False``.
        """
        ...

    @abstractmethod
    def is_storage_warm(self, address: Address, slot: int) -> bool:
        """
        Was the storage slot accessed during this transaction?

        See EIP-2929
        """
        ...

    @abstractmethod
    def mark_storage_warm(self, address: Address, slot: int) -> None:
        """
        Mark the storage slot as accessed during this transaction.

        See EIP-2929
        """
        ...

    @abstractmethod
    def is_address_warm(self, address: Address) -> bool:
        """
        Was the account accessed during this transaction?

        See EIP-2929
        """
        ...

    @abstractmethod
    def mark_address_warm(self, address: Address) -> None:
        """
        Mark the account as accessed during this transaction.

        See EIP-2929
        """
        ...

    #
    # transient storage
    #
    @abstractmethod
    def get_transient_storage(self, address: Address, slot: int) -> bytes:
        """
        Return the transient storage for ``address`` at slot ``slot``.
        """
        ...

    @abstractmethod
    def set_transient_storage(self, address: Address, slot: int, value: bytes) -> None:
        """
        Return the transient storage for ``address`` at slot ``slot``.
        """
        ...

    @abstractmethod
    def clear_transient_storage(self) -> None:
        """
        Clear the transient storage. Should be done at the start of every transaction
        """
        ...

    #
    # Access self._chaindb
    #
    @abstractmethod
    def snapshot(self) -> Tuple[Hash32, DBCheckpoint]:
        """
        Perform a full snapshot of the current state.

        Snapshots are a combination of the :attr:`~state_root` at the time of the
        snapshot and the checkpoint from the journaled DB.
        """
        ...

    @abstractmethod
    def revert(self, snapshot: Tuple[Hash32, DBCheckpoint]) -> None:
        """
        Revert the VM to the state at the snapshot
        """
        ...

    @abstractmethod
    def commit(self, snapshot: Tuple[Hash32, DBCheckpoint]) -> None:
        """
        Commit the journal to the point where the snapshot was taken.  This
        merges in any changes that were recorded since the snapshot.
        """
        ...

    @abstractmethod
    def lock_changes(self) -> None:
        """
        Locks in all changes to state, typically just as a transaction starts.

        This is used, for example, to look up the storage value from the start
        of the transaction, when calculating gas costs in EIP-2200: net gas metering.
        """
        ...

    @abstractmethod
    def persist(self) -> None:
        """
        Persist the current state to the database.
        """
        ...

    #
    # Access self.prev_hashes (Read-only)
    #
    @abstractmethod
    def get_ancestor_hash(self, block_number: BlockNumber) -> Hash32:
        """
        Return the hash for the ancestor block with number ``block_number``.
        Return the empty bytestring ``b''`` if the block number is outside of the
        range of available block numbers (typically the last 255 blocks).
        """
        ...

    #
    # Computation
    #
    @abstractmethod
    def get_computation(
        self, message: MessageAPI, transaction_context: TransactionContextAPI
    ) -> ComputationAPI:
        """
        Return a computation instance for the given `message` and `transaction_context`
        """
        ...

    #
    # Transaction context
    #
    @classmethod
    @abstractmethod
    def get_transaction_context_class(cls) -> Type[TransactionContextAPI]:
        """
        Return the :class:`~eth.vm.transaction_context.BaseTransactionContext` class
        that the state class uses.
        """
        ...

    #
    # Execution
    #
    @abstractmethod
    def apply_transaction(
        self,
        transaction: SignedTransactionAPI,
    ) -> ComputationAPI:
        """
        Apply transaction to the vm state

        :param transaction: the transaction to apply
        :return: the computation
        """
        ...

    @abstractmethod
    def get_transaction_executor(self) -> TransactionExecutorAPI:
        """
        Return the transaction executor.
        """
        ...

    @abstractmethod
    def costless_execute_transaction(
        self,
        transaction: SignedTransactionAPI,
    ) -> ComputationAPI:
        """
        Execute the given ``transaction`` with a gas price of ``0``.
        """
        ...

    @abstractmethod
    def override_transaction_context(self, gas_price: int) -> ContextManager[None]:
        """
        Return a :class:`~typing.ContextManager` that overwrites the current
        transaction context, applying the given ``gas_price``.
        """
        ...

    @abstractmethod
    def validate_transaction(self, transaction: SignedTransactionAPI) -> None:
        """
        Validate the given ``transaction``.
        """
        ...

    @abstractmethod
    def get_transaction_context(
        self, transaction: SignedTransactionAPI
    ) -> TransactionContextAPI:
        """
        Return the :class:`~eth.abc.TransactionContextAPI` for the given ``transaction``
        """
        ...

    #
    # Withdrawals
    #
    def apply_withdrawal(self, withdrawal) -> None: ...

    def apply_all_withdrawals(self, withdrawals) -> None: ...
