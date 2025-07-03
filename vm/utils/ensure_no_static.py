import functools
from typing import (
    Any,
    Callable,
)

from vm.AbstractClass import (
    ComputationAPI,
)
from vm.Exception import WriteProtection


def ensure_no_static(opcode_fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(opcode_fn)
    def inner(computation: ComputationAPI) -> Callable[..., Any]:
        if computation.msg.is_static:
            raise WriteProtection(
                "Cannot modify state while inside of a STATICCALL context"
            )
        return opcode_fn(computation)

    return inner
