# # 尝试先使用sqlite实现，同时，查找一下在线的DB API https://ethereum.org/en/developers/docs/nodes-and-clients/nodes-as-a-service/

# from utils.ImmutableConstant import ImmutableConstant
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from Repository import SimpleStorageManager
# from eth_typing import Address
# from Validation import validate_canonical_address, validate_uint256


# class Storage:
#     def __init__(self):
#         dbname = ImmutableConstant("EVM_Storage.db")
#         engine = create_engine("sqlite:///" + dbname.value)
#         Session = sessionmaker(bind=engine)
#         session = Session()
#         # 初始化 SimpleStorageManager
#         self.manager = SimpleStorageManager(session)
#         self.storage = {}

#     def set(self, account_address: Address, slot: int, value: int):
#         validate_uint256(value, title="Storage Value")
#         validate_uint256(slot, title="Storage Slot")
#         validate_canonical_address(account_address, title="Storage Address")

#         self.manager.add(id=slot, account=account_address, value=value)

#     def get(self, account_address: Address, slot: int):
#         validate_canonical_address(account_address, title="Storage Address")
#         validate_uint256(slot, title="Storage Slot")

#         row = self.manager.get_by_index(index=slot)
#         if row is not None:
#             result = row.value
#         else:
#             raise RuntimeError("Storage key is none")
#         return result
