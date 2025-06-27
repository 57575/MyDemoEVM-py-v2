import pytest

from vm.db.backends.memory_db import MemoryDB


@pytest.fixture
def memory_db():
    return MemoryDB()


def test_set_and_get(
    memory_db,
):
    memory_db.set(b"1", b"2")
    assert memory_db.get(b"1") == b"2"


def test_set_on_existing_value(memory_db):
    memory_db.set(b"1", b"2")
    memory_db.set(b"1", b"3")
    assert memory_db.get(b"1") == b"3"


def test_exists(memory_db):
    memory_db.set(b"1", b"1")
    assert memory_db.exists(b"1") == True
    assert memory_db.exists(b"2") == False


def test_delete(memory_db):
    memory_db.set(b"1", b"1")
    memory_db.delete(b"1")
    assert memory_db.exists(b"1") == False
    memory_db.delete(b"non_existent")
    assert memory_db.exists(b"non_existent") == False


def test_empty_key_and_value(memory_db):
    # 空键
    memory_db.set(b"", b"empty_key")
    assert memory_db.get(b"") == b"empty_key"

    # 空值
    memory_db.set(b"key", b"")
    assert memory_db.get(b"key") == b""

    # 空键和空值
    memory_db.set(b"", b"")
    assert memory_db.get(b"") == b""


# 新增：异常处理测试
def test_get_missing_key(memory_db):
    memory_db.get(b"missing") == None
    with pytest.raises(KeyError):
        memory_db["missing"]


def test_delete_missing_key(memory_db):
    # 删除不存在的键应无异常（幂等性）
    memory_db.delete(b"missing")
    assert not memory_db.exists(b"missing")
