import math
from eth_utils import (
    big_endian_to_int,
)
from vm.utils.address import (
    force_bytes_to_address,
)
from vm.utils.numeric import (
    get_highest_bit_index,
)
from vm.utils.padding import (
    zpad_right,
)
from vm.precompiles.sha256 import sha256
from vm.precompiles.identity import identity
from vm.precompiles.ecrecover import ecrecover
from vm.precompiles.ripemd160 import ripemd160
from vm.precompiles.modexp import modexp, extract_lengths
from vm.precompiles.ecadd import ecadd
from vm.precompiles.ecmul import ecmul
from vm.precompiles.ecpairing import ecpairing
from vm.precompiles.blake2 import blake2b_fcompress
from vm.precompiles.point_evaluation import point_evaluation_precompile
from vm.utils.address import force_bytes_to_address
from vm.utils.constant import (
    POINT_EVALUATION_PRECOMPILE_ADDRESS,
    GAS_MOD_EXP_QUADRATIC_DENOMINATOR_EIP_2565,
    GAS_ECADD,
    GAS_ECMUL,
    GAS_ECPAIRING_BASE,
    GAS_ECPAIRING_PER_POINT,
)


def _calculate_multiplication_complexity(base_length: int, modulus_length: int) -> int:
    max_length = max(base_length, modulus_length)
    words = math.ceil(max_length / 8)
    return words**2


def _calculate_iteration_count(
    exponent_length: int, first_32_exponent_bytes: bytes
) -> int:
    first_32_exponent = big_endian_to_int(first_32_exponent_bytes)

    highest_bit_index = get_highest_bit_index(first_32_exponent)

    if exponent_length <= 32:
        iteration_count = highest_bit_index
    else:
        iteration_count = highest_bit_index + (8 * (exponent_length - 32))

    return max(iteration_count, 1)


def _compute_modexp_gas_fee_eip_2565(data: bytes) -> int:
    base_length, exponent_length, modulus_length = extract_lengths(data)

    base_end_idx = 96 + base_length
    exponent_end_idx = base_end_idx + exponent_length

    first_32_exponent_bytes = zpad_right(
        data[base_end_idx:exponent_end_idx],
        to_size=min(exponent_length, 32),
    )[:32]
    iteration_count = _calculate_iteration_count(
        exponent_length,
        first_32_exponent_bytes,
    )

    multiplication_complexity = _calculate_multiplication_complexity(
        base_length, modulus_length
    )
    return max(
        200,
        multiplication_complexity
        * iteration_count
        // GAS_MOD_EXP_QUADRATIC_DENOMINATOR_EIP_2565,
    )


CANCUN_PRECOMPILES = {
    force_bytes_to_address(b"\x01"): ecrecover,
    force_bytes_to_address(b"\x02"): sha256,
    force_bytes_to_address(b"\x03"): ripemd160,
    force_bytes_to_address(b"\x04"): identity,
    force_bytes_to_address(b"\x05"): modexp(
        gas_calculator=_compute_modexp_gas_fee_eip_2565
    ),
    force_bytes_to_address(b"\x06"): ecadd(gas_cost=GAS_ECADD),
    force_bytes_to_address(b"\x07"): ecmul(gas_cost=GAS_ECMUL),
    force_bytes_to_address(b"\x08"): ecpairing(
        gas_cost_base=GAS_ECPAIRING_BASE,
        gas_cost_per_point=GAS_ECPAIRING_PER_POINT,
    ),
    force_bytes_to_address(b"\x09"): blake2b_fcompress,
    force_bytes_to_address(
        POINT_EVALUATION_PRECOMPILE_ADDRESS
    ): point_evaluation_precompile,
}
