# %%
import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from eth_utils import (
    ValidationError,
    decode_hex,
    encode_hex,
    hexstr_if_str,
    int_to_big_endian,
    to_bytes,
    to_canonical_address,
)
from sqlalchemy import create_engine, inspect, text
from eth_typing import Address, BlockNumber, Hash32


from vm.Message import Message
from vm.State import BaseState
from vm.ExecutionContext import ExecutionContext
from vm.EthereumAPI import EthereumAPI
from vm.AbstractClass import ComputationAPI, StateAPI, ExecutionContextAPI
from vm.TransactionContext import BaseTransactionContext
from vm.config import SQLALCHEMY_DATABASE_URI
import vm.OpcodeValues as opcode_values

NORMALIZED_ADDRESS_A = "0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"
NORMALIZED_ADDRESS_B = "0xcd1722f3947def4cf144679da39c4c32bdc35681"
ADDRESS_WITH_CODE = ("0xddd722f3947def4cf144679da39c4c32bdc35681", b"pseudocode")
EMPTY_ADDRESS_IN_STATE = NORMALIZED_ADDRESS_A
ADDRESS_NOT_IN_STATE = NORMALIZED_ADDRESS_B
ADDRESS_WITH_JUST_BALANCE = "0x0000000000000000000000000000000000000001"
CANONICAL_ADDRESS_A = to_canonical_address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
CANONICAL_ADDRESS_B = to_canonical_address("0xcd1722f3947def4cf144679da39c4c32bdc35681")
CANONICAL_ADDRESS_C = b"\xee" * 20
CANONICAL_ZERO_ADDRESS = b"\0" * 20


def test_connect_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    inspector = inspect(engine)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT sqlite_version();"))
        version = result.fetchone()
        print(f"\r\nSQLite 版本: {version[0]}")
    assert set(["account", "account_storage", "code"]).issubset(
        inspector.get_table_names()
    )


def create_execution_context(block_number: str = "latest") -> ExecutionContextAPI:
    block = EthereumAPI.get_block_by_number(block_number_hex=block_number)

    return ExecutionContext(
        coinbase=Address(
            decode_hex(block.get("miner"))
        ),  # the eth_coinbase method is not supported from v1.14.0
        timestamp=int(block.get("timestamp"), 16),
        block_number=BlockNumber(int(block.get("number"), 16)),
        difficulty=int(block.get("difficulty"), 16),
        mix_hash=Address(decode_hex(block.get("mixHash"))),
        gas_limit=int(block.get("gasLimit"), 16),
        chain_id=0x01,
        base_fee_per_gas=int(block.get("baseFeePerGas"), 16),
        excess_blob_gas=int(block.get("excessBlobGas"), 16),
    )


def build_state(block_number: str = "latest") -> BaseState:
    execution_context = create_execution_context(block_number)
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    return BaseState(engine=engine, execution_context=execution_context)


def run_computation(
    state: BaseState,
    create_address,
    code: bytes,
    gas=1000000,
    gas_price=1,
    to=CANONICAL_ADDRESS_A,
    transaction_sender=b"\x11" * 20,
    data=b"",
):
    message = Message(
        to=to,
        sender=CANONICAL_ADDRESS_B,
        create_address=create_address,
        value=0,
        data=data,
        code=code,
        gas=gas,
    )
    transaction_ctx = BaseTransactionContext(
        gas_price=gas_price, origin=transaction_sender
    )
    return state.build_computation(message, transaction_context=transaction_ctx)


def run_general_computation(
    create_address=None,
    code=b"",
    block_number: str = "latest",
    gas=1000000,
    gas_price=1,
    to=CANONICAL_ADDRESS_A,
    transaction_sender=b"\x11" * 20,
    data=b"",
) -> ComputationAPI:
    state = build_state(block_number=block_number)

    state.touch_account(decode_hex(EMPTY_ADDRESS_IN_STATE))
    state.set_code(decode_hex(ADDRESS_WITH_CODE[0]), ADDRESS_WITH_CODE[1])

    state.set_balance(decode_hex(ADDRESS_WITH_JUST_BALANCE), 1)

    return run_computation(
        state=state,
        create_address=create_address,
        code=code,
        gas=gas,
        gas_price=gas_price,
        to=to,
        transaction_sender=transaction_sender,
        data=data,
    )


@pytest.mark.parametrize(
    "val1, val2, expected",  # 参数名称
    [  # 测试用例列表
        (1, 1, 2),  # 第一组参数
    ],
)
def test_add(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val1)
    computation.stack_push_int(val2)
    computation.opcodes[opcode_values.ADD](computation)

    result = computation.stack_pop1_int()

    assert result == expected


@pytest.mark.parametrize("val1, val2, expected", [(2, 3, 6)])
def test_mul(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val1)
    computation.stack_push_int(val2)
    computation.opcodes[opcode_values.MUL](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, expected",
    [(5, 2, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD)],
)
def test_sub(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val1)
    computation.stack_push_int(val2)
    computation.opcodes[opcode_values.SUB](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("val1, val2, expected", [(2, 10, 5), (10, 2, 0)])
def test_div(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val1)
    computation.stack_push_int(val2)
    computation.opcodes[opcode_values.DIV](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, expected",
    [
        (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF6, 2, 0),
        (
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
            2,
        ),
    ],
)
def test_sdiv(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val1)
    computation.stack_push_int(val2)
    computation.opcodes[opcode_values.SDIV](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("val1, val2, expected", [(3, 10, 1), (5, 17, 2)])
def test_mod(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val1)
    computation.stack_push_int(val2)
    computation.opcodes[opcode_values.MOD](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, expected",
    [
        (
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD,
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF8,
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
        ),
        (3, 10, 1),
    ],
)
def test_smod(val1, val2, expected):
    computation = run_general_computation()
    computation.stack_push_int(val1)
    computation.stack_push_int(val2)
    computation.opcodes[opcode_values.SMOD](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, mod, expected",
    [
        (10, 10, 8, 4),
        (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 2, 2, 1),
    ],
)
def test_addmod(val1, val2, mod, expected):
    computation = run_general_computation()
    computation.stack_push_int(mod)
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.ADDMOD](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "val1, val2, mod, expected",
    [
        (10, 10, 8, 4),
        (
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            12,
            9,
        ),
    ],
)
def test_mulmod(val1, val2, mod, expected):
    computation = run_general_computation()
    computation.stack_push_int(mod)
    computation.stack_push_int(val2)
    computation.stack_push_int(val1)
    computation.opcodes[opcode_values.MULMOD](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("base, exponent, expected", [(2, 3, 8), (10, 2, 100)])
def test_exp(base, exponent, expected):
    computation = run_general_computation()
    computation.stack_push_int(exponent)
    computation.stack_push_int(base)
    computation.opcodes[opcode_values.EXP](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "byte_index, value, expected",
    [
        (0, 0x7F, 0x7F),
        (0, 0xFF, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
    ],
)
def test_signextend(byte_index, value, expected):
    computation = run_general_computation()
    computation.stack_push_int(value)
    computation.stack_push_int(byte_index)
    computation.opcodes[opcode_values.SIGNEXTEND](computation)
    result = computation.stack_pop1_int()
    assert result == expected
