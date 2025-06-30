from eth_hash.auto import (
    keccak,
)
from eth_utils import (
    ValidationError,
)
import pytest
from sqlalchemy.engine import Engine

from vm.utils.constant import EMPTY_SHA3
from vm.db.Account import AccountDB
from vm.config import MOCK_DATABASE_URI
from vm.db import check_database

ADDRESS = b"\xaa" * 20
OTHER_ADDRESS = b"\xbb" * 20
INVALID_ADDRESS = b"aa" * 20


@pytest.fixture
def base_db() -> Engine:
    return check_database(MOCK_DATABASE_URI)


@pytest.fixture
def account_db(base_db):
    return AccountDB(base_db)


def test_balance(account_db):
    assert account_db.get_balance(ADDRESS) == 0

    account_db.set_balance(ADDRESS, 1)
    assert account_db.get_balance(ADDRESS) == 1
    assert account_db.get_balance(OTHER_ADDRESS) == 0

    with pytest.raises(ValidationError):
        account_db.get_balance(INVALID_ADDRESS)
    with pytest.raises(ValidationError):
        account_db.set_balance(INVALID_ADDRESS, 1)
    with pytest.raises(ValidationError):
        account_db.set_balance(ADDRESS, 1.0)


def test_nonce(account_db):
    assert account_db.get_nonce(ADDRESS) == 0

    account_db.set_nonce(ADDRESS, 5)
    assert account_db.get_nonce(ADDRESS) == 5
    assert account_db.get_nonce(OTHER_ADDRESS) == 0

    account_db.increment_nonce(ADDRESS)
    assert account_db.get_nonce(ADDRESS) == 6
    assert account_db.get_nonce(OTHER_ADDRESS) == 0

    with pytest.raises(ValidationError):
        account_db.get_nonce(INVALID_ADDRESS)
    with pytest.raises(ValidationError):
        account_db.set_nonce(INVALID_ADDRESS, 1)
    with pytest.raises(ValidationError):
        account_db.increment_nonce(INVALID_ADDRESS)
    with pytest.raises(ValidationError):
        account_db.set_nonce(ADDRESS, 1.0)


def test_code(account_db):
    assert account_db.get_code(ADDRESS) == b""
    assert account_db.get_code_hash(ADDRESS) == EMPTY_SHA3

    account_db.set_code(ADDRESS, b"code")
    assert account_db.get_code(ADDRESS) == b"code"
    assert account_db.get_code(OTHER_ADDRESS) == b""
    assert account_db.get_code_hash(ADDRESS) == keccak(b"code")

    with pytest.raises(ValidationError):
        account_db.get_code(INVALID_ADDRESS)
    with pytest.raises(ValidationError):
        account_db.set_code(INVALID_ADDRESS, b"code")
    with pytest.raises(ValidationError):
        account_db.set_code(ADDRESS, "code")


def test_accounts(account_db):
    assert not account_db.account_exists(ADDRESS)
    assert not account_db.account_has_code_or_nonce(ADDRESS)

    account_db.touch_account(ADDRESS)
    assert account_db.account_exists(ADDRESS)
    assert account_db.get_nonce(ADDRESS) == 0
    assert account_db.get_balance(ADDRESS) == 0
    assert account_db.get_code(ADDRESS) == b""

    assert not account_db.account_has_code_or_nonce(ADDRESS)
    account_db.increment_nonce(ADDRESS)
    assert account_db.account_has_code_or_nonce(ADDRESS)

    account_db.delete_account(ADDRESS)
    assert not account_db.account_exists(ADDRESS)
    assert not account_db.account_has_code_or_nonce(ADDRESS)

    with pytest.raises(ValidationError):
        account_db.account_exists(INVALID_ADDRESS)
    with pytest.raises(ValidationError):
        account_db.delete_account(INVALID_ADDRESS)
    with pytest.raises(ValidationError):
        account_db.account_has_code_or_nonce(INVALID_ADDRESS)


def test_storage(account_db):
    assert account_db.get_storage(ADDRESS, 0) == 0

    account_db.set_storage(ADDRESS, 0, 123)
    assert account_db.get_storage(ADDRESS, 0) == 123
    assert account_db.get_storage(ADDRESS, 1) == 0
    assert account_db.get_storage(OTHER_ADDRESS, 0) == 0


def test_storage_deletion(account_db):
    account_db.set_storage(ADDRESS, 0, 123)
    account_db.set_storage(OTHER_ADDRESS, 1, 321)
    account_db.delete_storage(ADDRESS)
    assert account_db.get_storage(ADDRESS, 0) == 0
    assert account_db.get_storage(OTHER_ADDRESS, 1) == 321


def test_account_db_storage_root(account_db):
    """
    Make sure that pruning doesn't screw up addresses
    that temporarily share storage roots
    """
    account_db.set_storage(ADDRESS, 1, 2)
    account_db.set_storage(OTHER_ADDRESS, 1, 2)

    # both addresses will share the same root
    account_db.make_state_root()

    account_db.set_storage(ADDRESS, 3, 4)
    account_db.set_storage(OTHER_ADDRESS, 3, 5)

    # addresses will have different roots
    account_db.make_state_root()

    assert account_db.get_storage(ADDRESS, 1) == 2
    assert account_db.get_storage(OTHER_ADDRESS, 1) == 2
    assert account_db.get_storage(ADDRESS, 3) == 4
    assert account_db.get_storage(OTHER_ADDRESS, 3) == 5

    account_db.persist()

    assert account_db.get_storage(ADDRESS, 1) == 2
    assert account_db.get_storage(OTHER_ADDRESS, 1) == 2
    assert account_db.get_storage(ADDRESS, 3) == 4
    assert account_db.get_storage(OTHER_ADDRESS, 3) == 5


def test_account_db_update_then_make_root_then_read(account_db):
    assert account_db.get_storage(ADDRESS, 1) == 0
    account_db.set_storage(ADDRESS, 1, 2)
    assert account_db.get_storage(ADDRESS, 1) == 2

    account_db.make_state_root()

    assert account_db.get_storage(ADDRESS, 1) == 2

    account_db.persist()
    assert account_db.get_storage(ADDRESS, 1) == 2


def test_account_db_read_then_update_then_make_root_then_read(account_db):
    account_db.set_storage(ADDRESS, 1, 2)

    # must always explicitly make the root before persisting
    account_db.make_state_root()
    account_db.persist()

    # read out of a non-empty account, to build a read-cache trie
    assert account_db.get_storage(ADDRESS, 1) == 2

    account_db.set_storage(ADDRESS, 1, 3)

    assert account_db.get_storage(ADDRESS, 1) == 3

    account_db.make_state_root()

    assert account_db.get_storage(ADDRESS, 1) == 3

    account_db.persist()
    # if you start caching read tries, then you might get this answer wrong:
    assert account_db.get_storage(ADDRESS, 1) == 3
