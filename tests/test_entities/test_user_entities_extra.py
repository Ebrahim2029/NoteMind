import pytest
from core.entities.user import User
from core.entities.value_objects.user_id import UserId
from core.exceptions.user_exceptions import InvalidUserAttributeException

# =====================
# Tests for User._validate
# =====================



def test_user_validate_invalid_email():
    with pytest.raises(InvalidUserAttributeException):
        User(username="validname", email="invalid-email")

def test_user_validate_is_active_not_bool():
    with pytest.raises(InvalidUserAttributeException):
        User(username="validname", email="valid@example.com", is_active="yes")

def test_user_validate_preferences_not_dict():
    with pytest.raises(InvalidUserAttributeException):
        User(username="validname", email="valid@example.com", preferences="not-a-dict")

def test_user_validate_success():
    user = User(username="validname", email="valid@example.com")
    assert user.username == "validname"
    assert user.is_active is True
    assert isinstance(user.preferences, dict)

# =====================
# Tests for UserId
# =====================

def test_userid_str_and_validation():
    valid_id = str(UserId())
    assert isinstance(str(UserId(valid_id)), str)  # __str__
    with pytest.raises(ValueError):
        UserId("invalid-uuid")
