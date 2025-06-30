# %%
from sqlalchemy import Column, String, LargeBinary
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator

from eth_typing import Address

# 创建 ORM 基类
Base = declarative_base()


class AddressType(TypeDecorator):
    impl = LargeBinary(20)
    cache_ok = True

    def process_bind_param(self, value: Address, dialect):
        if value is None:
            return None
        if not isinstance(value, bytes) or len(value) != 20:
            raise TypeError("Address must be 20-byte bytes")
        return value

    def process_result_value(self, value: bytes, dialect) -> Address:
        if value is None:
            return None
        return Address(value)


# 定义账户存储表
class AccountStorageModel(Base):
    __tablename__ = "account_storage"

    account_address = Column(AddressType, primary_key=True)
    slot = Column(LargeBinary, primary_key=True)
    value = Column(LargeBinary)

    def __init__(self, address: Address, slot: bytes, value: bytes):
        self.account_address = address
        self.slot = slot
        self.value = value


class CodeStorageModel(Base):
    __tablename__ = "code"

    code_hash = Column(LargeBinary, nullable=False, primary_key=True)
    code = Column(LargeBinary, nullable=False)

    def __init__(self, code_hash: bytes, code: bytes):
        self.code_hash = code_hash
        self.code = code


class AccountModel(Base):
    __tablename__ = "account"

    address = Column(AddressType, primary_key=True)
    rlp_account = Column(LargeBinary, nullable=False)

    def __init__(self, address: Address, rlp_account: bytes):
        self.address = address
        self.rlp_account = rlp_account
