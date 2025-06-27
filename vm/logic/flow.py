from vm.AbstractClass import ComputationAPI

from vm.Exception import Halt, InvalidInstruction, InvalidJumpDestination

from vm.OpcodeValues import JUMPDEST


def stop(computation: ComputationAPI) -> None:
    raise Halt("STOP")


def jump(computation: ComputationAPI) -> None:
    jump_dest = computation.stack_pop1_int()

    computation.code.program_counter = jump_dest

    next_opcode = computation.code.peek()

    if next_opcode != JUMPDEST:
        raise InvalidJumpDestination("Invalid Jump Destination")

    if not computation.code.is_valid_opcode(jump_dest):
        raise InvalidInstruction("Jump resulted in invalid instruction")


def jumpi(computation: ComputationAPI) -> None:
    jump_dest, check_value = computation.stack_pop_ints(2)

    if check_value:
        computation.code.program_counter = jump_dest

        next_opcode = computation.code.peek()

        if next_opcode != JUMPDEST:
            raise InvalidJumpDestination("Invalid Jump Destination")

        if not computation.code.is_valid_opcode(jump_dest):
            raise InvalidInstruction("Jump resulted in invalid instruction")


def jumpdest(computation: ComputationAPI) -> None:
    pass


def program_counter(computation: ComputationAPI) -> None:
    pc = max(computation.code.program_counter - 1, 0)

    computation.stack_push_int(pc)


def gas(computation: ComputationAPI) -> None:

    computation.get_debug_logger().warning(
        "The code invoked the GAS instruction and returned a virtual value, which posed unforeseen risks to the code."
    )

    gas_remaining = computation.get_gas_remaining()

    computation.stack_push_int(gas_remaining)
