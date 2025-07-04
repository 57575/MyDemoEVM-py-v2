import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from eth_typing import Hash32
from eth_utils import decode_hex
from vm.test.test_opcode_arithmetic import (
    run_general_computation,
    build_state,
    CANONICAL_ADDRESS_A,
)
import vm.OpcodeValues as opcode_values
from vm.EthereumAPI import EthereumAPI
from vm.Message import Message
from vm.TransactionContext import BaseTransactionContext

BLOCK_NUMBER = "0x1595125"
TRANSACTION_HASH = "0xa2f9eebf3b447ec6ba385ee0a52119615197c0c4631bc4532193d48f89aed735"


@pytest.mark.parametrize(
    "block_number, expected",
    [
        (0x1595124, 0x80ED8761BE1B9EADA245283FD49C941D49B94B20718C57F39606D6E542590B9E),
    ],
)
def test_blockhash(block_number, expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.stack_push_int(block_number)
    computation.opcodes[opcode_values.BLOCKHASH](computation)

    result = computation.stack_pop1_int()

    assert result == expected


@pytest.mark.parametrize(
    "expected",
    [
        (bytes.fromhex("0x95222290DD7278AA3DDD389CC1E1D165CC4BAFE5"[2:])),
    ],
)
def test_coinbase(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.COINBASE](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected


@pytest.mark.parametrize(
    "expected",
    [
        (0x6840204B),
    ],
)
def test_timestamp(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.TIMESTAMP](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "expected",
    [
        (0x1595125),
    ],
)
def test_number(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.NUMBER](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "expected",
    [
        decode_hex(
            "0x39DB467826A2138D92D939A6CF4A52AC1FDCE8D7115E14D7DB85596BA963B01A"
        ),
    ],
)
def test_prevrandao(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.PREVRANDAO](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected


@pytest.mark.parametrize(
    "expected",
    [
        (0x2255100),
    ],
)
def test_gaslimit(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.GASLIMIT](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize(
    "expected",
    [
        (0x01),
    ],
)
def test_chainid(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.CHAINID](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("expected", [123456])
def test_selfbalance(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.state.set_balance(CANONICAL_ADDRESS_A, expected)
    computation.opcodes[opcode_values.SELFBALANCE](computation)
    result = computation.stack_pop1_int()
    assert result == expected


@pytest.mark.parametrize("expected", [0xAA3F787C])
def test_base_fee(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.BASEFEE](computation)

    result = computation.stack_pop1_int()

    assert result == expected


@pytest.mark.parametrize(
    "index, expected",
    [
        (
            0,
            decode_hex(
                "0x0145f7e174abab3e1d588023b2712ca73c9c3bd5d51862f23cb223c7fb164ece"
            ),
        )
    ],
)
def test_blob_hash(index, expected):
    transaction = EthereumAPI.get_transaction_by_hash(TRANSACTION_HASH)
    state = build_state(BLOCK_NUMBER)

    msg = Message(
        gas=int(transaction.get("gas"), 16),
        to=decode_hex(transaction.get("to")),
        sender=decode_hex(transaction.get("from")),
        value=int(transaction.get("value"), 16),
        data=decode_hex(transaction.get("input")),
        code=b"",
    )
    blob_versioned_hashes_raw = transaction.get("blobVersionedHashes", [])
    transaction_ctx = BaseTransactionContext(
        gas_price=int(transaction.get("gasPrice"), 16),
        origin=decode_hex(transaction.get("from")),
        blob_versioned_hashes=[
            Hash32(decode_hex(h)) for h in blob_versioned_hashes_raw
        ],
    )
    computation = state.build_computation(msg, transaction_ctx)
    computation.stack_push_int(index)
    computation.opcodes[opcode_values.BLOBHASH](computation)
    result = computation.stack_pop1_bytes()
    assert result == expected


@pytest.mark.parametrize("expected", [0x1])
def test_blob_base_fee(expected):
    computation = run_general_computation(block_number=BLOCK_NUMBER)
    computation.opcodes[opcode_values.BLOBBASEFEE](computation)
    result = computation.stack_pop1_int()
    assert result == expected
