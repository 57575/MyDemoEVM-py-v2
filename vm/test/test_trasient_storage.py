import pytest
from eth_utils import int_to_big_endian, ValidationError
from eth_typing import Address

from vm.utils.EVMTyping import DBCheckpoint

from vm.transient_storage import TransientStorage, EMPTY_VALUE


@pytest.fixture(scope="function")
def storage() -> TransientStorage:
    return TransientStorage()


# ===== 基础功能测试 =====
def test_set_and_get(storage: TransientStorage) -> None:
    address = Address(b"\x11" * 20)
    slot = 123
    value = b"\x01\x02\x03"

    # 设置值
    storage.set_transient_storage(address, slot, value)

    # 获取值
    assert storage.get_transient_storage(address, slot) == value


def test_get_missing_value(storage: TransientStorage) -> None:
    address = Address(b"\x22" * 20)
    slot = 456

    # 未设置的值应返回EMPTY_VALUE
    assert storage.get_transient_storage(address, slot) == EMPTY_VALUE


def test_overwrite_value(storage: TransientStorage) -> None:
    address = Address(b"\x33" * 20)
    slot = 789

    # 首次设置
    storage.set_transient_storage(address, slot, b"old")

    # 覆盖设置
    storage.set_transient_storage(address, slot, b"new")

    # 验证最终值
    assert storage.get_transient_storage(address, slot) == b"new"


# ===== 事务管理测试 =====
def test_record_and_commit(storage: TransientStorage) -> None:
    address = Address(b"\x44" * 20)
    slot = 100

    # 设置初始值
    storage.set_transient_storage(address, slot, b"init")

    # 创建检查点
    checkpoint = DBCheckpoint(1)
    storage.record(checkpoint)

    # 修改值
    storage.set_transient_storage(address, slot, b"updated")

    # 提交检查点
    storage.commit(checkpoint)

    # 验证修改生效
    assert storage.get_transient_storage(address, slot) == b"updated"


def test_commit_checkpoint(storage: TransientStorage) -> None:
    address = Address(b"\x44" * 20)
    slot = 100
    origin_checkpoint_stack = storage._db._journal._checkpoint_stack.copy()
    # 记录检查点
    cp1 = storage._db.record()
    storage.set_transient_storage(address, slot, b"value1")

    cp2 = storage._db.record()
    storage.set_transient_storage(address, slot, b"value2")

    # 提交检查点1
    storage.commit(cp1)

    # 验证当前值
    assert storage.get_transient_storage(address, slot) == b"value2"

    # 验证检查点栈
    assert storage._db._journal._checkpoint_stack == origin_checkpoint_stack


# 测试提交和丢弃检查点
def test_record_and_discard(storage: TransientStorage) -> None:
    address = Address(b"\x55" * 20)
    slot = 200

    # 设置初始值
    storage.set_transient_storage(address, slot, b"init")

    # 创建检查点
    checkpoint = DBCheckpoint(2)
    storage.record(checkpoint)

    # 修改值
    storage.set_transient_storage(address, slot, b"updated")

    # 丢弃检查点
    storage.discard(checkpoint)

    # 验证回滚到初始值
    assert storage.get_transient_storage(address, slot) == b"init"


def test_explicit_checkpoint_management(storage: TransientStorage) -> None:
    address = Address(b"\xaa" * 20)
    slot = 123

    # 初始状态
    assert storage.get_transient_storage(address, slot) == EMPTY_VALUE

    # 设置值（初始检查点0）
    storage.set_transient_storage(address, slot, b"v1")
    assert storage.get_transient_storage(address, slot) == b"v1"

    # 创建检查点1
    cp1 = DBCheckpoint(1)
    storage.record(cp1)

    # 修改值
    storage.set_transient_storage(address, slot, b"v2")
    assert storage.get_transient_storage(address, slot) == b"v2"

    # 创建检查点2
    cp2 = DBCheckpoint(2)
    storage.record(cp2)

    # 再次修改值
    storage.set_transient_storage(address, slot, b"v3")
    assert storage.get_transient_storage(address, slot) == b"v3"

    # 回滚到检查点2
    storage.discard(cp2)
    assert storage.get_transient_storage(address, slot) == b"v2"

    # 提交检查点1
    storage.commit(cp1)
    assert storage.get_transient_storage(address, slot) == b"v2"

    # 尝试回滚到已提交的检查点1（应失败）
    with pytest.raises(ValidationError) as exc_info:
        storage.discard(cp1)
    assert f"No checkpoint {cp1}" in str(exc_info.value)


def test_multiple_records_without_commit(storage: TransientStorage) -> None:
    address = Address(b"\xbb" * 20)
    slot = 456

    # 设置初始值
    storage.set_transient_storage(address, slot, b"base")

    # 创建检查点1并修改
    cp1 = DBCheckpoint(1)
    storage.record(cp1)
    storage.set_transient_storage(address, slot, b"cp1")

    # 创建检查点2并修改
    cp2 = DBCheckpoint(2)
    storage.record(cp2)
    storage.set_transient_storage(address, slot, b"cp2")

    # 创建检查点3并修改
    cp3 = DBCheckpoint(3)
    storage.record(cp3)
    storage.set_transient_storage(address, slot, b"cp3")

    # 逐级回滚
    storage.discard(cp3)
    assert storage.get_transient_storage(address, slot) == b"cp2"

    storage.discard(cp2)
    assert storage.get_transient_storage(address, slot) == b"cp1"

    storage.discard(cp1)
    assert storage.get_transient_storage(address, slot) == b"base"


def test_commit_interleaved_checkpoints(storage: TransientStorage) -> None:
    address = Address(b"\xcc" * 20)
    slot = 789

    # 创建检查点1并设置值
    cp1 = DBCheckpoint(1)
    storage.record(cp1)
    storage.set_transient_storage(address, slot, b"cp1")

    # 创建检查点2并设置值
    cp2 = DBCheckpoint(2)
    storage.record(cp2)
    storage.set_transient_storage(address, slot, b"cp2")

    # 提交检查点2 （中间提交）
    storage.commit(cp2)
    assert storage.get_transient_storage(address, slot) == b"cp2"

    # 提交检查点1
    storage.commit(cp1)
    assert storage.get_transient_storage(address, slot) == b"cp2"

    # 尝试回滚到已提交的检查点（应失败）
    with pytest.raises(ValidationError) as exc_info:
        storage.discard(cp1)
    assert f"No checkpoint {cp1} was found" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        storage.discard(cp2)
    assert f"No checkpoint {cp2} was found" in str(exc_info.value)


def test_commit_multiple_checkpoints(storage: TransientStorage) -> None:
    address = Address(b"\xcc" * 20)
    slot = 789
    assert len(storage._db._journal._checkpoint_stack) == 1
    cp0 = storage._db._journal._checkpoint_stack[0]
    # 创建检查点1并设置值
    cp1 = storage._db.record()
    storage.set_transient_storage(address, slot, b"cp1")

    # 创建检查点2并设置值
    cp2 = storage._db.record()
    storage.set_transient_storage(address, slot, b"cp2")

    # 创建检查点3并设置值
    cp3 = storage._db.record()
    storage.set_transient_storage(address, slot, b"cp3")

    # 创建检查点4并设置值
    cp4 = storage._db.record()
    storage.set_transient_storage(address, slot, b"cp4")

    # 提交检查点2
    storage.commit(cp2)
    assert storage.get_transient_storage(address, slot) == b"cp4"

    # 提交检查点4（应失败)
    with pytest.raises(ValidationError) as exc_info:
        storage.commit(cp4)
    assert f"No checkpoint {cp4} was found" in str(exc_info.value)

    # 提交检查点3（应失败)
    with pytest.raises(ValidationError) as exc_info:
        storage.commit(cp3)
    assert f"No checkpoint {cp3} was found" in str(exc_info.value)

    # 提交检查点0（应失败)
    with pytest.raises(ValidationError) as exc_info:
        storage.commit(cp0)
    assert "Should not commit root changeset with commit_changeset," in str(
        exc_info.value
    )


def test_discard_after_commit_fails(storage: TransientStorage) -> None:
    address = Address(b"\xdd" * 20)
    slot = 1000

    # 创建并提交检查点1
    cp1 = DBCheckpoint(1)
    storage.record(cp1)
    storage.set_transient_storage(address, slot, b"cp1")
    storage.commit(cp1)

    # 创建检查点2但不提交
    cp2 = DBCheckpoint(2)
    storage.record(cp2)
    storage.set_transient_storage(address, slot, b"cp2")

    # 提交检查点2
    storage.commit(cp2)
    assert storage.get_transient_storage(address, slot) == b"cp2"

    # 尝试回滚到已提交的检查点1（应失败）
    with pytest.raises(ValidationError) as exc_info:
        storage.discard(cp1)
    assert f"No checkpoint {cp1} was found" in str(exc_info.value)

    # 尝试回滚到已提交的检查点2（应失败）
    with pytest.raises(ValidationError) as exc_info:
        storage.discard(cp2)
    assert f"No checkpoint {cp2} was found" in str(exc_info.value)


def test_clear_with_checkpoints(storage: TransientStorage) -> None:
    address = Address(b"\xee" * 20)
    slot = 1111

    # 设置初始值
    storage.set_transient_storage(address, slot, b"init")

    # 创建检查点1
    cp1 = storage._db.record()

    # 修改值
    storage.set_transient_storage(address, slot, b"update")

    # 清除所有状态
    storage.clear()
    assert storage.get_transient_storage(address, slot) == EMPTY_VALUE


@pytest.mark.parametrize("checkpoint_value", [1, 2, 3])
def test_commit_multiple_and_discard_later(
    checkpoint_value, storage: TransientStorage
) -> None:
    address = Address(b"\xbb" * 20)
    slot = 67890

    # 设置初始值
    storage.set_transient_storage(address, slot, b"init")

    # 创建检查点1并提交
    checkpoint1 = storage._db.record()
    storage.set_transient_storage(address, slot, b"cp1")
    storage.commit(checkpoint1)

    # 创建检查点2并提交
    checkpoint2 = storage._db.record()
    storage.set_transient_storage(address, slot, b"cp2")
    storage.commit(checkpoint2)

    # 创建检查点3（未提交）
    checkpoint3 = storage._db.record()
    storage.set_transient_storage(address, slot, b"cp3")

    match checkpoint_value:
        case 1:
            # 尝试丢弃检查点1（已提交，应失败）
            with pytest.raises(ValidationError) as exc_info:
                storage.discard(checkpoint1)
            assert f"No checkpoint {checkpoint1} was found" in str(exc_info.value)
        case 2:
            # 尝试丢弃检查点2（已提交，应失败）
            with pytest.raises(ValidationError) as exc_info:
                storage.discard(checkpoint2)
            assert f"No checkpoint {checkpoint2} was found" in str(exc_info.value)
        case 3:
            # 丢弃检查点3（未提交，应成功）
            storage.discard(checkpoint3)
            assert storage.get_transient_storage(address, slot) == b"cp2"

            # 提交检查点3（已丢弃，应失败）
            with pytest.raises(ValidationError) as exc_info:
                storage.commit(checkpoint3)
            assert f"No checkpoint {checkpoint3} was found" in str(exc_info.value)


# ===== 边界条件测试 =====
def test_key_generation(storage: TransientStorage) -> None:
    address = Address(b"\xaa" * 20)
    slot = 0x1234567890

    # 手动计算预期的键
    expected_key = address + int_to_big_endian(slot)

    # 使用反射验证私有方法
    actual_key = storage._get_key(address, slot)  # type: ignore

    assert actual_key == expected_key


def test_max_slot_value(storage: TransientStorage) -> None:
    address = Address(b"\xbb" * 20)
    max_slot = 2**256 - 1  # uint256的最大值
    value = b"\xff" * 32

    # 设置最大值
    storage.set_transient_storage(address, max_slot, value)

    # 获取验证
    assert storage.get_transient_storage(address, max_slot) == value


def test_empty_value(storage: TransientStorage) -> None:
    address = Address(b"\xcc" * 20)
    slot = 500

    # 设置空值
    storage.set_transient_storage(address, slot, EMPTY_VALUE)

    # 获取验证
    assert storage.get_transient_storage(address, slot) == EMPTY_VALUE


# ===== 异常处理测试 =====
def test_invalid_address(storage: TransientStorage) -> None:
    invalid_address = b"\xdd" * 19  # 长度不足20字节
    slot = 600
    value = b"data"

    # 无效地址应抛出异常
    with pytest.raises(ValidationError) as exc_info:
        storage.set_transient_storage(
            # type: ignore  # 故意传入错误类型
            invalid_address,
            slot,
            value,
        )
    assert f"{invalid_address!r} is not a valid canonical address" in str(
        exc_info.value
    )


def test_invalid_slot(storage: TransientStorage) -> None:
    address = Address(b"\xee" * 20)
    invalid_slot = 2**256  # 超出uint256范围
    value = b"data"

    # 无效槽位应抛出异常
    with pytest.raises(ValidationError) as exc_info:
        storage.set_transient_storage(address, invalid_slot, value)
    assert f"Value exceeds maximum uint256 size." in str(exc_info.value)


def test_invalid_value_type(storage: TransientStorage) -> None:
    address = Address(b"\xff" * 20)
    slot = 700
    invalid_value = 123  # 非bytes类型

    # 无效值类型应抛出异常
    with pytest.raises(ValidationError) as exc_info:
        storage.set_transient_storage(
            address,
            slot,
            # type: ignore  # 故意传入错误类型
            invalid_value,
        )
    assert f"Value must be a byte string." in str(exc_info.value)


# ===== 交互测试 =====
def test_multiple_addresses(storage: TransientStorage) -> None:
    address1 = Address(b"\x01" * 20)
    address2 = Address(b"\x02" * 20)
    slot = 800

    # 为不同地址设置相同槽位的值
    storage.set_transient_storage(address1, slot, b"addr1")
    storage.set_transient_storage(address2, slot, b"addr2")

    # 验证独立存储
    assert storage.get_transient_storage(address1, slot) == b"addr1"
    assert storage.get_transient_storage(address2, slot) == b"addr2"


def test_multiple_slots(storage: TransientStorage) -> None:
    address = Address(b"\x03" * 20)
    slot1 = 900
    slot2 = 901

    # 为同一地址设置不同槽位的值
    storage.set_transient_storage(address, slot1, b"slot1")
    storage.set_transient_storage(address, slot2, b"slot2")

    # 验证独立存储
    assert storage.get_transient_storage(address, slot1) == b"slot1"
    assert storage.get_transient_storage(address, slot2) == b"slot2"


# ===== 批量操作测试 =====
def test_clear(storage: TransientStorage) -> None:
    address = Address(b"\x04" * 20)
    slot1 = 1000
    slot2 = 1001

    # 设置多个值
    storage.set_transient_storage(address, slot1, b"val1")
    storage.set_transient_storage(address, slot2, b"val2")

    # 清除所有
    storage.clear()

    # 验证全部清除
    assert storage.get_transient_storage(address, slot1) == EMPTY_VALUE
    assert storage.get_transient_storage(address, slot2) == EMPTY_VALUE
