from typing import Union, NewType

DBCheckpoint = NewType("DBCheckpoint", int)

BytesOrView = Union[bytes, memoryview]
