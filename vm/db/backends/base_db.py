from typing import (
    Iterator,
)

from vm.AbstractClass import (
    DatabaseAPI,
)


class BaseDB(DatabaseAPI):
    """
    This is an abstract key/value lookup with all :class:`bytes` values,
    with some convenience methods for databases. As much as possible,
    you can use a DB as if it were a :class:`dict`.

    Notable exceptions are that you cannot iterate through all values or get the length.
    (Unless a subclass explicitly enables it).

    All subclasses must implement these methods:
    __init__, __getitem__, __setitem__, __delitem__

    Subclasses may optionally implement an _exists method
    that is type-checked for key and value.
    """

    def set(self, key: bytes, value: bytes) -> None:
        self[key] = value

    def exists(self, key: bytes) -> bool:
        return self.__contains__(key)

    def __contains__(self, key: bytes) -> bool:  # type: ignore # Breaks LSP
        if hasattr(self, "_exists"):
            # Classes which inherit this class would have `_exists` attr
            return self._exists(key)
        else:
            return super().__contains__(key)

    def delete(self, key: bytes) -> None:
        try:
            del self[key]
        except KeyError:
            pass

    def __iter__(self) -> Iterator[bytes]:
        raise NotImplementedError("By default, DB classes cannot be iterated.")

    def __len__(self) -> int:
        raise NotImplementedError(
            "By default, DB classes cannot return the total number of keys."
        )
