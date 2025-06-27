# %%
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from eth_typing import Address
from sqlalchemy import create_engine

from vm.db.AccountBatchDB import AccountBatchDB
from vm.AbstractClass import ComputationAPI, StateAPI, ExecutionContextAPI
from vm.Message import Message
from vm.TransactionContext import BaseTransactionContext
from vm.Computation import Computation
from vm.State import BaseState
from vm.ExecutionContext import ExecutionContext
from vm.EthereumAPI import EthereumAPI


def create_execution_context() -> ExecutionContextAPI:

    block = EthereumAPI.get_block_by_number(block_number_hex="latest")

    return ExecutionContext(
        coinbase=block.get(
            "miner"
        ),  # the eth_coinbase method is not supported from v1.14.0
        timestamp=block.get("timestamp"),
        block_number=block.get("number"),
        difficulty=block.get("difficulty"),
        mix_hash=block.get("mixHash"),
        gas_limit=block.get("gasLimit"),
        chain_id=0x01,
        base_fee_per_gas=block.get("baseFeePerGas"),
        excess_blob_gas=block.get("excessBlobGas"),
    )


def build_state() -> StateAPI:
    execution_context = create_execution_context()
    engine = create_engine("sqlite:///accounts.db")
    return BaseState(engine=engine, execution_context=execution_context)


# 修改为每笔transaction从公共API初始化状态
def execute_bytecode(
    origin: Address,
    gas_price: int,
    gas: int,
    to: Address,
    sender: Address,
    value: int,
    data: bytes,
    code: bytes,
    code_address: Address = None,
) -> ComputationAPI:
    if origin is None:
        origin = sender

    # Construct a message
    message = Message(
        gas=gas,
        to=to,
        sender=sender,
        value=value,
        data=data,
        code=code,
        code_address=code_address,
    )

    # Construction a tx context
    transaction_context = BaseTransactionContext(
        gas_price=gas_price,
        origin=origin,
    )
    state = build_state()

    # Execute it in the VM
    return Computation.apply_computation(
        state,
        message,
        transaction_context,
    )


# %%
