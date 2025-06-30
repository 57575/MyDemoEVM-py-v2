import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from eth_utils import to_canonical_address

from vm.db.AccountInfoBatchDB import AccountInfoBatchDB
from vm.config import MOCK_DATABASE_URI
from vm.db import check_database
from vm.db.StateDBModel import AccountModel

CANONICAL_ADDRESS_A = to_canonical_address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
CANONICAL_ADDRESS_B = to_canonical_address("0xcd1722f3947def4cf144679da39c4c32bdc35681")
CANONICAL_ADDRESS_C = b"\xee" * 20
CANONICAL_ZERO_ADDRESS = b"\0" * 20


# 定义测试夹具
@pytest.fixture
def engine() -> Engine:
    return check_database(MOCK_DATABASE_URI)


@pytest.fixture
def db(engine: Engine) -> AccountInfoBatchDB:
    return AccountInfoBatchDB(engine)


# 测试基本功能
def test_set_and_get_item(db: AccountInfoBatchDB) -> None:
    # 设置项目
    db.set_item(b"key1", b"value1")

    # 获取项目
    assert db.get_item(b"key1") == b"value1"

    # 测试未设置的项目
    assert db.get_item(b"key2") is None


def test_set_item_overwrite(db: AccountInfoBatchDB) -> None:
    # 首次设置
    db.set_item(b"key", b"value1")
    assert db.get_item(b"key") == b"value1"

    # 覆盖设置
    db.set_item(b"key", b"value2")
    assert db.get_item(b"key") == b"value2"


def test_set_item_empty(db: AccountInfoBatchDB) -> None:
    # 设置项目
    db.set_item(b"key", b"value")
    assert db.get_item(b"key") == b"value"


def test_delete_item(db: AccountInfoBatchDB) -> None:
    # 测试删除已存在的项目
    db.set_item(CANONICAL_ADDRESS_A, b"value1")
    assert db.get_item(CANONICAL_ADDRESS_A) == b"value1"

    db.delete_item(CANONICAL_ADDRESS_A)
    assert db.get_item(CANONICAL_ADDRESS_A) is None

    # 测试删除不存在的项目（应抛出KeyError）
    with pytest.raises(KeyError) as exc_info:
        db.delete_item(CANONICAL_ADDRESS_B)
    assert "key could not be deleted" in str(exc_info.value)


# ===== 事务管理测试 =====
# 测试检查点功能
def test_record_checkpoint(db: AccountInfoBatchDB) -> None:
    # 记录第一个检查点
    cp1 = db.record_checkpoint()
    assert len(db._checkpoint_stack) == 2
    assert db.has_checkpoint(cp1)

    # 记录第二个检查点
    cp2 = db.record_checkpoint()
    assert len(db._checkpoint_stack) == 3
    assert db.has_checkpoint(cp2)


# 使用自定义检查点
def test_custom_checkpoint(db: AccountInfoBatchDB) -> None:
    custom_cp = 100
    cp = db.record_checkpoint(custom_cp)
    assert cp == 100
    assert db.has_checkpoint(custom_cp)

    # 尝试使用已存在的检查点
    with pytest.raises(Exception) as exc_info:
        db.record_checkpoint(custom_cp)
    assert "Tried to record with an existing checkpoint:" in str(exc_info.value)


# 测试提交和丢弃检查点
def test_commit_checkpoint(db: AccountInfoBatchDB) -> None:
    origin_checkpoint_stack = db._checkpoint_stack.copy()
    # 记录检查点
    cp1 = db.record_checkpoint()
    db.set_item(b"key", b"value1")

    cp2 = db.record_checkpoint()
    db.set_item(b"key", b"value2")

    # 提交检查点1
    db.commit_checkpoint(cp1)

    # 验证当前值
    assert db.get_item(b"key") == b"value2"

    # 验证检查点栈
    assert db._checkpoint_stack == origin_checkpoint_stack


def test_discard_checkpoint(db: AccountInfoBatchDB) -> None:
    origin_checkpoint_stack = db._checkpoint_stack.copy()
    # 记录检查点
    cp1 = db.record_checkpoint()
    db.set_item(b"key", b"value1")

    cp2 = db.record_checkpoint()
    db.set_item(b"key", b"value2")

    # 丢弃检查点2
    db.discard(cp2)

    # 验证值回滚到检查点1
    assert db.get_item(b"key") == b"value1"

    # 验证检查点栈
    origin_checkpoint_stack.append(cp1)
    assert db._checkpoint_stack == origin_checkpoint_stack


def test_discard_nonexistent_checkpoint(db: AccountInfoBatchDB) -> None:
    # 尝试丢弃不存在的检查点
    with pytest.raises(Exception) as exc_info:
        db.discard(100)
    assert f"No checkpoint {100} was found" in str(exc_info.value)


def test_explicit_checkpoint_management(db: AccountInfoBatchDB) -> None:
    key = b"\x00"

    # 初始状态
    assert db.get_item(key) is None

    # 设置值（初始检查点0）
    db.set_item(key, b"v1")
    assert db.get_item(key) == b"v1"

    # 创建检查点1
    cp1 = db.record_checkpoint()

    # 修改值
    db.set_item(key, b"v2")
    assert db.get_item(key) == b"v2"

    # 创建检查点2
    cp2 = db.record_checkpoint()

    # 再次修改值
    db.set_item(key, b"v3")
    assert db.get_item(key) == b"v3"

    # 回滚到检查点2
    db.discard(cp2)
    assert db.get_item(key) == b"v2"

    # 提交检查点1
    db.commit_checkpoint(cp1)
    assert db.get_item(key) == b"v2"

    # 尝试回滚到已提交的检查点1（应失败）
    with pytest.raises(Exception) as exc_info:
        db.discard(cp1)
    assert f"No checkpoint {cp1} was found" in str(exc_info.value)


def test_multiple_records_without_commit(db: AccountInfoBatchDB) -> None:
    key = b"\x01"

    # 设置初始值
    db.set_item(key, b"base")

    # 创建检查点1并修改
    cp1 = db.record_checkpoint()
    db.set_item(key, b"cp1")

    # 创建检查点2并修改
    cp2 = db.record_checkpoint()
    db.set_item(key, b"cp2")

    # 创建检查点3并修改
    cp3 = db.record_checkpoint()
    db.set_item(key, b"cp3")

    # 逐级回滚
    db.discard(cp3)
    assert db.get_item(key) == b"cp2"

    db.discard(cp2)
    assert db.get_item(key) == b"cp1"

    db.discard(cp1)
    assert db.get_item(key) == b"base"


def test_commit_interleaved_checkpoints(db: AccountInfoBatchDB) -> None:
    key = b"\x01"
    origin_cp_stack = db._checkpoint_stack.copy()

    # 创建检查点1并设置值
    cp1 = db.record_checkpoint()
    db.set_item(key, b"cp1")

    # 创建检查点2并设置值
    cp2 = db.record_checkpoint()
    db.set_item(key, b"cp2")

    # 提交检查点2 （中间提交）
    db.commit_checkpoint(cp2)
    assert db.get_item(key) == b"cp2"
    inter_cp_stack = origin_cp_stack.copy()
    inter_cp_stack.append(cp1)
    assert inter_cp_stack == db._checkpoint_stack

    # 提交检查点1
    db.commit_checkpoint(cp1)
    assert db.get_item(key) == b"cp2"
    assert origin_cp_stack == db._checkpoint_stack

    # 尝试回滚到已提交的检查点（应失败）
    with pytest.raises(Exception) as exc_info:
        db.discard(cp1)
    assert f"No checkpoint {cp1} was found" in str(exc_info.value)

    with pytest.raises(Exception) as exc_info:
        db.discard(cp2)
    assert f"No checkpoint {cp2} was found" in str(exc_info.value)


def test_commit_multiple_checkpoints(db: AccountInfoBatchDB) -> None:
    key = b"\x01"
    assert len(db._checkpoint_stack) == 1
    cp0 = db._checkpoint_stack[0]
    # 创建检查点1并设置值
    cp1 = db.record_checkpoint()
    db.set_item(key, b"cp1")

    # 创建检查点2并设置值
    cp2 = db.record_checkpoint()
    db.set_item(key, b"cp2")

    # 创建检查点3并设置值
    cp3 = db.record_checkpoint()
    db.set_item(key, b"cp3")

    # 创建检查点4并设置值
    cp4 = db.record_checkpoint()
    db.set_item(key, b"cp4")

    # 提交检查点2
    db.commit_checkpoint(cp2)
    assert db.get_item(key) == b"cp4"

    # 提交检查点4（应失败)
    with pytest.raises(Exception) as exc_info:
        db.commit_checkpoint(cp4)
    assert f"No checkpoint {cp4} was found" in str(exc_info.value)

    # 提交检查点3（应失败)
    with pytest.raises(Exception) as exc_info:
        db.commit_checkpoint(cp3)
    assert f"No checkpoint {cp3} was found" in str(exc_info.value)

    # 提交检查点0（应失败)
    with pytest.raises(Exception) as exc_info:
        db.commit_checkpoint(cp0)
    assert "Should not commit root changeset with commit_changeset," in str(
        exc_info.value
    )


def test_discard_after_commit_fails(db: AccountInfoBatchDB) -> None:
    key = b"\x01"

    # 创建并提交检查点1
    cp1 = db.record_checkpoint()
    db.set_item(key, b"cp1")
    db.commit_checkpoint(cp1)

    # 创建检查点2但不提交
    cp2 = db.record_checkpoint()
    db.set_item(key, b"cp2")

    # 提交检查点2
    db.commit_checkpoint(cp2)
    assert db.get_item(key) == b"cp2"

    # 尝试回滚到已提交的检查点1（应失败）
    with pytest.raises(Exception) as exc_info:
        db.discard(cp1)
    assert f"No checkpoint {cp1} was found" in str(exc_info.value)

    # 尝试回滚到已提交的检查点2（应失败）
    with pytest.raises(Exception) as exc_info:
        db.discard(cp2)
    assert f"No checkpoint {cp2} was found" in str(exc_info.value)


@pytest.mark.parametrize("checkpoint_value", [1, 2, 3])
def test_commit_multiple_and_discard_later(
    checkpoint_value, db: AccountInfoBatchDB
) -> None:
    key = b"\x01"

    # 设置初始值
    db.set_item(key, b"init")

    # 创建检查点1并提交
    checkpoint1 = db.record_checkpoint()
    db.set_item(key, b"cp1")
    db.commit_checkpoint(checkpoint1)

    # 创建检查点2并提交
    checkpoint2 = db.record_checkpoint()
    db.set_item(key, b"cp2")
    db.commit_checkpoint(checkpoint2)

    # 创建检查点3（未提交）
    checkpoint3 = db.record_checkpoint()
    db.set_item(key, b"cp3")

    match checkpoint_value:
        case 1:
            # 尝试丢弃检查点1（已提交，应失败）
            with pytest.raises(Exception) as exc_info:
                db.discard(checkpoint1)
            assert f"No checkpoint {checkpoint1} was found" in str(exc_info.value)
        case 2:
            # 尝试丢弃检查点2（已提交，应失败）
            with pytest.raises(Exception) as exc_info:
                db.discard(checkpoint2)
            assert f"No checkpoint {checkpoint2} was found" in str(exc_info.value)
        case 3:
            # 丢弃检查点3（未提交，应成功）
            db.discard(checkpoint3)
            assert db.get_item(key) == b"cp2"

            # 提交检查点3（已丢弃，应失败）
            with pytest.raises(Exception) as exc_info:
                db.commit_checkpoint(checkpoint3)
            assert f"No checkpoint {checkpoint3} was found" in str(exc_info.value)


# ===== 边界条件测试 =====
def test_empty_key(db: AccountInfoBatchDB) -> None:
    # 设置空键
    db.set_item(b"", b"value")
    assert db.get_item(b"") == b"value"


# 测试清除和重置功能
def test_clear(db: AccountInfoBatchDB) -> None:
    # 设置项目
    db.set_item(b"key", b"value")

    # 清除
    db.clear()

    # 验证项目被清除
    assert len(db.accessed) == 0
    assert len(db._current_values) == 0
    assert db.get_item(b"key") is None


def test_reset(db: AccountInfoBatchDB) -> None:
    # 设置项目
    db.set_item(b"key", b"value")

    # 重置
    db.reset()

    # 验证项目被重置
    assert len(db.accessed) == 0
    assert len(db._current_values) == 0
    assert db.get_item(b"key") is None
    assert len(db._checkpoint_stack) == 1  # 应该有一个初始检查点


# ===== 测试持久化功能 =====
# 测试持久化功能
def test_persist(db: AccountInfoBatchDB) -> None:
    # 设置项目
    db.set_item(CANONICAL_ADDRESS_A, b"value1")
    db.set_item(CANONICAL_ADDRESS_B, b"value2")

    items = db.accessed.copy()

    # 持久化
    db.persist()

    # 验证当前值被清除
    assert len(db._checkpoint_stack) == 1
    assert len(db._journal_data) == 1
    key, value = next(iter(db._journal_data.items()))
    assert value == {}
    assert len(db._current_values) == 0
    assert len(db.accessed) == 0

    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        existing_data = (
            session.query(AccountModel).filter(AccountModel.address.in_(items)).all()
        )
        assert existing_data[0].address == CANONICAL_ADDRESS_A
        assert (
            isinstance(existing_data[0].address, bytes)
            and len(existing_data[0].address) == 20
        )
        assert existing_data[0].rlp_account == b"value1"
        assert isinstance(existing_data[0].rlp_account, bytes)
        assert existing_data[1].address == CANONICAL_ADDRESS_B
        assert (
            isinstance(existing_data[1].address, bytes)
            and len(existing_data[1].address) == 20
        )
        assert existing_data[1].rlp_account == b"value2"
        assert isinstance(existing_data[1].rlp_account, bytes)


def test_persist_add_new_data(db: AccountInfoBatchDB) -> None:
    # 测试持久化新增数据
    db.set_item(CANONICAL_ADDRESS_A, b"new_value")
    db.persist()

    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        item = session.query(AccountModel).filter_by(address=CANONICAL_ADDRESS_A).one()
        assert item.rlp_account == b"new_value"


def test_persist_update_existing_data(db: AccountInfoBatchDB) -> None:
    # 预填充数据
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        existing = AccountModel(address=CANONICAL_ADDRESS_A, rlp_account=b"old_value")
        session.add(existing)
        session.commit()

    # 更新数据并持久化
    db.set_item(CANONICAL_ADDRESS_A, b"updated_value")
    db.persist()

    # 验证更新结果
    with Session() as session:
        item = session.query(AccountModel).filter_by(address=CANONICAL_ADDRESS_A).one()
        assert item.rlp_account == b"updated_value"


def test_persist_delete_data(db: AccountInfoBatchDB) -> None:
    # 预填充数据
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        existing = AccountModel(
            address=CANONICAL_ADDRESS_A, rlp_account=b"to_be_deleted"
        )
        session.add(existing)
        session.commit()

    # 删除数据并持久化
    db.set_item(CANONICAL_ADDRESS_A, b"to_be_deleted")  # 先设置以标记为已访问
    db.delete_item(CANONICAL_ADDRESS_A)
    db.persist()

    # 验证删除结果
    with Session() as session:
        count = (
            session.query(AccountModel).filter_by(address=CANONICAL_ADDRESS_A).count()
        )
        assert count == 0


def test_persist_multiple_operations(db: AccountInfoBatchDB) -> None:
    # 预填充数据
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        existing1 = AccountModel(address=CANONICAL_ADDRESS_A, rlp_account=b"old_value1")
        existing2 = AccountModel(address=CANONICAL_ADDRESS_B, rlp_account=b"old_value2")
        session.add_all([existing1, existing2])
        session.commit()

    # 组合操作：更新A，删除B，新增C
    db.set_item(CANONICAL_ADDRESS_A, b"updated_value")  # 更新
    db.set_item(CANONICAL_ADDRESS_B, b"old_value2")  # 标记为已访问以便删除
    db.delete_item(CANONICAL_ADDRESS_B)  # 删除
    db.set_item(CANONICAL_ADDRESS_C, b"new_value")  # 新增
    db.persist()

    # 验证组合操作结果
    with Session() as session:
        a_item = (
            session.query(AccountModel).filter_by(address=CANONICAL_ADDRESS_A).one()
        )
        assert a_item.rlp_account == b"updated_value"

        b_count = (
            session.query(AccountModel).filter_by(address=CANONICAL_ADDRESS_B).count()
        )
        assert b_count == 0

        c_item = (
            session.query(AccountModel).filter_by(address=CANONICAL_ADDRESS_C).one()
        )
        assert c_item.rlp_account == b"new_value"


def test_checkpoint_rollback_and_persist(db: AccountInfoBatchDB) -> None:
    # 预先填充CANONICAL_ADDRESS_A的值 (假设初始值为b'initial')
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        initial_data = AccountModel(address=CANONICAL_ADDRESS_A, rlp_account=b"initial")
        session.add(initial_data)
        session.commit()

    # 提交检查点0 (初始化状态)
    checkpoint_0 = db.record_checkpoint()

    # 提交检查点1，在检查点1设置CANONICAL_ADDRESS_A为b'checkpoint1'
    checkpoint_1 = db.record_checkpoint()
    db.set_item(CANONICAL_ADDRESS_A, b"checkpoint1")

    # 提交检查点2，在检查点2删除CANONICAL_ADDRESS_A的值
    checkpoint_2 = db.record_checkpoint()
    db.delete_item(CANONICAL_ADDRESS_A)

    # 提交检查点3，在检查点3设置CANONICAL_ADDRESS_A的值为b'checkpoint3'
    checkpoint_3 = db.record_checkpoint()
    db.set_item(CANONICAL_ADDRESS_A, b"checkpoint3")

    # 验证当前状态
    assert db.get_item(CANONICAL_ADDRESS_A) == b"checkpoint3", "检查点3数据验证"

    # 回滚至检查点0（丢弃所有后续检查点）
    db.discard(checkpoint_0)

    # 验证回滚后状态恢复到初始状态
    assert db.get_item(CANONICAL_ADDRESS_A) is None

    # 持久化到数据库
    db.persist()

    # 验证数据库中的值未被正确清除
    with Session() as session:
        count = (
            session.query(AccountModel).filter_by(address=CANONICAL_ADDRESS_A).count()
        )
        assert count == 1, "持久化后数据未被正确删除"


# 测试异常情况
def test_commit_nonexistent_checkpoint(db: AccountInfoBatchDB) -> None:
    # 尝试提交不存在的检查点
    with pytest.raises(Exception):
        db.commit_checkpoint(100)


def test_discard_after_commit(db: AccountInfoBatchDB) -> None:
    # 记录检查点
    cp1 = db.record_checkpoint()
    db.set_item(b"key", b"value1")

    cp2 = db.record_checkpoint()
    db.set_item(b"key", b"value2")

    # 提交检查点2
    db.commit_checkpoint(cp1)

    # 尝试丢弃检查点1（已提交之后的检查点）
    with pytest.raises(Exception) as exc_info:
        db.discard(cp2)
    assert f"No checkpoint {cp2} was found" in str(exc_info.value)
