from eth_utils import (
    encode_hex,
)
from eth_typing import Address
from vm.AbstractClass import ComputationAPI
import vm.utils.constant as constants
from vm.utils.address import force_bytes_to_address
from vm import (
    mnemonics,
)
from vm.Exception import (
    Halt,
)
from vm.logic.system import selfdestruct_eip161_on_address
from vm.utils.constant import COLD_ACCOUNT_ACCESS_COST


def tstore(computation: ComputationAPI) -> None:
    address = computation.msg.storage_address
    slot = computation.stack_pop1_int()
    value = computation.stack_pop1_bytes()
    computation.state.set_transient_storage(address, slot, value)


def tload(computation: ComputationAPI) -> None:
    address = computation.msg.storage_address
    slot = computation.stack_pop1_int()
    value = computation.state.get_transient_storage(address, slot)
    computation.stack_push_bytes(value)


def _mark_address_warm(computation: ComputationAPI, address: Address) -> bool:
    """
    Mark the given address as warm if it was not previously.

    :return was_cold: True if the account was not previously accessed
        during this transaction
    """
    if computation.state.is_address_warm(address):
        return False
    else:
        computation.state.mark_address_warm(address)
        return True


def selfdestruct_eip2929(computation: ComputationAPI) -> None:
    beneficiary = force_bytes_to_address(computation.stack_pop1_bytes())

    if _mark_address_warm(computation, beneficiary):
        gas_cost = COLD_ACCOUNT_ACCESS_COST
        computation.consume_gas(
            gas_cost,
            reason=f"Implicit account load during {mnemonics.SELFDESTRUCT}",
        )

    selfdestruct_eip161_on_address(computation, beneficiary)


def selfdestruct_eip6780(computation: ComputationAPI) -> None:
    contract_address = computation.msg.storage_address

    if contract_address in computation.contracts_created:
        if computation.logger.show_debug2:
            computation.logger.debug2(
                "Contract created within computation and allowed to self destruct: "
                f"{encode_hex(contract_address)} "
            )
        selfdestruct_eip2929(computation)
    else:
        # disallow contract to selfdestruct but all other logic remains the same
        if computation.logger.show_debug2:
            computation.logger.debug2(
                "Contract was not created within computation and thus not allowed to "
                f"self destruct: {encode_hex(contract_address)}."
            )

        beneficiary = force_bytes_to_address(computation.stack_pop1_bytes())
        if _mark_address_warm(computation, beneficiary):
            gas_cost = COLD_ACCOUNT_ACCESS_COST
            computation.consume_gas(
                gas_cost,
                reason=f"Implicit account load during {mnemonics.SELFDESTRUCT}",
            )

        # # from vm/logic/system.py -> selfdestruct_eip161_on_address
        is_dead = not computation.state.account_exists(
            beneficiary
        ) or computation.state.account_is_empty(beneficiary)
        if is_dead and computation.state.get_balance(contract_address):
            computation.consume_gas(
                constants.GAS_SELFDESTRUCT_NEWACCOUNT,
                reason=mnemonics.SELFDESTRUCT,
            )

        # transfer contract balance to beneficiary
        contract_balance = computation.state.get_balance(contract_address)
        computation.state.delta_balance(beneficiary, contract_balance)
        computation.state.delta_balance(contract_address, -1 * contract_balance)
        computation.beneficiaries.append(beneficiary)

        computation.logger.debug2(
            f"SELFDESTRUCT: {encode_hex(contract_address)} "
            f"({contract_balance}) -> {encode_hex(beneficiary)}"
        )
        raise Halt("SELFDESTRUCT")
