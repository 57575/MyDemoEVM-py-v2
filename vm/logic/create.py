from vm.utils.numeric import (
    ceil32,
)
from eth_typing import (
    Address,
)
from vm.logic.system import CreateOpcodeStackData, Create2, CreateByzantium

from vm.utils.constant import (
    INITCODE_WORD_COST,
)
from vm.AbstractClass import ComputationAPI


class CreateEIP2929(CreateByzantium):
    def generate_contract_address(
        self,
        stack_data: CreateOpcodeStackData,
        call_data: bytes,
        computation: ComputationAPI,
    ) -> Address:
        address = super().generate_contract_address(stack_data, call_data, computation)
        computation.state.mark_address_warm(address)
        return address


class Create2EIP2929(Create2):
    def generate_contract_address(
        self,
        stack_data: CreateOpcodeStackData,
        call_data: bytes,
        computation: ComputationAPI,
    ) -> Address:
        address = super().generate_contract_address(stack_data, call_data, computation)
        computation.state.mark_address_warm(address)
        return address


class CreateEIP3860(CreateEIP2929):
    def get_gas_cost(self, data: CreateOpcodeStackData) -> int:
        eip2929_gas_cost = super().get_gas_cost(data)
        eip3860_gas_cost = INITCODE_WORD_COST * ceil32(data.memory_length) // 32
        return eip2929_gas_cost + eip3860_gas_cost


class Create2EIP3860(Create2EIP2929):
    def get_gas_cost(self, data: CreateOpcodeStackData) -> int:
        eip2929_gas_cost = super().get_gas_cost(data)
        eip3860_gas_cost = INITCODE_WORD_COST * ceil32(data.memory_length) // 32
        return eip2929_gas_cost + eip3860_gas_cost
