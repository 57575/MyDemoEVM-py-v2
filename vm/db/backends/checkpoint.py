from typing import Callable, cast
from vm.utils.EVMTyping import DBCheckpoint
from itertools import (
    count,
)

get_next_checkpoint = cast(Callable[[], DBCheckpoint], count().__next__)
