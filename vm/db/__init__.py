from sqlalchemy import create_engine, Engine
from sqlalchemy import inspect
from vm.db.StateDBModel import Base


def check_database(database_uri: str) -> Engine:
    # 创建数据库引擎
    engine = create_engine(database_uri)
    # 检查表是否存在
    inspector = inspect(engine)
    if "account_storage" in inspector.get_table_names():
        print("表 'account_storage' 已创建。")
    else:
        print("表 'account_storage' 不存在。")
        # 创建所有表
        Base.metadata.create_all(engine)
    return engine
