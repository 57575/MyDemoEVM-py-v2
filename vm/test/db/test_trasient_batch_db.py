import pytest
from typing import Dict, Optional
from unittest.mock import MagicMock, patch
from eth_utils import ValidationError

from vm.db.backends.base_db import BaseDB
from vm.db.backends.memory_db import MemoryDB
from vm.utils.EVMTyping import DBCheckpoint
from vm.db.transient_batch_db import TransientBatchDB


@pytest.fixture
def wrapped_db() -> BaseDB:
    return MemoryDB()


@pytest.fixture
def transient_db(wrapped_db: BaseDB) -> TransientBatchDB:
    return TransientBatchDB(wrapped_db)


# ===== 基础功能测试 =====
def test_set_and_get(transient_db: TransientBatchDB) -> None:
    # 设置值并直接获取
    transient_db[b"key"] = b"value"
    assert transient_db[b"key"] == b"value"

    # 验证包装的数据库尚未更新
    with pytest.raises(KeyError):
        transient_db._wrapped_db[b"key"]


def test_delete_existing_key(transient_db: TransientBatchDB) -> None:
    # 先设置值
    transient_db[b"key"] = b"value"
    assert transient_db[b"key"] == b"value"

    # 删除并验证
    del transient_db[b"key"]
    with pytest.raises(KeyError):
        transient_db[b"key"]


def test_delete_missing_key(transient_db: TransientBatchDB) -> None:
    # 尝试删除不存在的键
    with pytest.raises(KeyError) as exc_info:
        del transient_db[b"missing"]
    assert "key could not be deleted" in str(exc_info.value)


def test_exists(transient_db: TransientBatchDB) -> None:
    # 不存在的键
    assert not transient_db._exists(b"missing")

    # 设置后存在
    transient_db[b"key"] = b"value"
    assert transient_db._exists(b"key")

    # 删除后不存在
    del transient_db[b"key"]
    assert not transient_db._exists(b"key")


# ===== 事务管理测试 =====
def test_checkpoint_and_commit(transient_db: TransientBatchDB) -> None:
    # 设置初始值
    transient_db[b"key1"] = b"value1"

    # 创建检查点
    checkpoint = transient_db.record()

    # 在检查点后修改数据
    transient_db[b"key2"] = b"value2"
    del transient_db[b"key1"]

    # 提交检查点
    transient_db.commit(checkpoint)

    # 验证结果
    assert not transient_db._exists(b"key1")
    assert transient_db[b"key2"] == b"value2"


def test_checkpoint_and_discard(transient_db: TransientBatchDB) -> None:
    # 设置初始值
    transient_db[b"key1"] = b"value1"

    # 创建检查点
    checkpoint = transient_db._journal.record_checkpoint()

    # 在检查点后修改数据
    transient_db[b"key2"] = b"value2"
    del transient_db[b"key1"]

    # 丢弃检查点
    transient_db.discard(checkpoint)

    # 验证结果回滚
    assert transient_db._exists(b"key1")
    assert transient_db[b"key1"] == b"value1"
    assert not transient_db._exists(b"key2")


# ===== 边界条件测试 =====
def test_get_from_wrapped_db(transient_db: TransientBatchDB) -> None:
    # 直接在包装的数据库中设置值
    transient_db._wrapped_db[b"direct_key"] = b"direct_value"

    # 通过包装类获取
    assert transient_db[b"direct_key"] == b"direct_value"


def test_delete_wrapped_key(transient_db: TransientBatchDB) -> None:
    # 直接在包装的数据库中设置值
    transient_db._wrapped_db[b"wrapped_key"] = b"wrapped_value"

    # 通过包装类删除
    del transient_db[b"wrapped_key"]

    # 验证已标记删除
    with pytest.raises(KeyError) as exc_info:
        transient_db[b"wrapped_key"]
    assert "item is deleted in JournalDB" in str(exc_info.value)


def test_double_delete(transient_db: TransientBatchDB) -> None:
    # 设置值后删除
    transient_db[b"key"] = b"value"
    del transient_db[b"key"]

    # 再次删除应报错
    with pytest.raises(KeyError) as exc_info:
        del transient_db[b"key"]
    assert "key could not be deleted" in str(exc_info.value)


def test_clear(transient_db: TransientBatchDB) -> None:
    # 设置多个值
    transient_db[b"key1"] = b"value1"
    transient_db[b"key2"] = b"value2"

    # 清除
    transient_db.clear()

    # 验证全部清除
    assert not transient_db._exists(b"key1")
    assert not transient_db._exists(b"key2")


def test_reset(transient_db: TransientBatchDB) -> None:
    # 设置值并创建检查点
    transient_db[b"key"] = b"value"
    checkpoint = transient_db._journal.record_checkpoint()

    # 修改值
    transient_db[b"key"] = b"new_value"

    # 重置
    transient_db.reset()

    # 验证所有更改被丢弃
    assert not transient_db._exists(b"key")


# ===== 异常处理测试 =====
def test_invalid_checkpoint(transient_db: TransientBatchDB) -> None:
    # 尝试提交无效检查点
    invalid_checkpoint = DBCheckpoint(9999)
    with pytest.raises(ValidationError) as exc_info:
        transient_db.commit(invalid_checkpoint)
    assert "No checkpoint" in str(exc_info.value)

    # 尝试丢弃无效检查点
    with pytest.raises(ValidationError) as exc_info:
        transient_db.discard(invalid_checkpoint)
    assert "No checkpoint" in str(exc_info.value)


# ===== 交互测试 =====
def test_discard_all_changes(transient_db: TransientBatchDB) -> None:
    # 设置值并创建检查点
    transient_db[b"key"] = b"value"
    checkpoint = transient_db._journal.record_checkpoint()

    # 修改值
    transient_db[b"key"] = b"new_value"

    # 丢弃所有更改
    transient_db.discard(checkpoint)

    # 验证回滚到检查点
    assert transient_db[b"key"] == b"value"
