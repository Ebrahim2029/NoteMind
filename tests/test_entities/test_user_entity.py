import pytest
from datetime import datetime
from core.entities.user import User
from core.exceptions.user_exceptions import InvalidUserAttributeException
from core.exceptions.note_exceptions import InvalidNoteAttributeException

class TestUserEntity:
    """Tests for User entity"""

    @pytest.fixture
    def valid_user(self):
        return User(username="validuser", email="valid@example.com")

    def test_user_initialization(self, valid_user):
        assert valid_user.username == "validuser"
        assert valid_user.email == "valid@example.com"
        assert valid_user.is_active is True

    @pytest.mark.parametrize("username,email,expected_exception", [
        ("ab", "valid@test.com", InvalidNoteAttributeException),  # Short username
        ("a"*31, "valid@test.com", InvalidNoteAttributeException),  # Long username
        ("valid", "invalid-email", InvalidUserAttributeException),  # Invalid email
    ])
    def test_validation_errors(self, username, email, expected_exception):
        with pytest.raises(expected_exception):
            User(username=username, email=email)

    def test_update_username(self, valid_user):
        original_time = valid_user.modified_date.value
        valid_user.update_username("newusername")
        assert valid_user.username == "newusername"
        assert valid_user.modified_date.value > original_time

    def test_update_email(self, valid_user):
        original_time = valid_user.modified_date.value
        valid_user.update_email("new@example.com")
        assert valid_user.email == "new@example.com"
        assert valid_user.modified_date.value > original_time

    def test_preference_management(self, valid_user):
        valid_user.set_preference("theme", "dark")
        assert valid_user.get_preference("theme") == "dark"
        assert valid_user.get_preference("missing") is None

    def test_account_status(self, valid_user):
        valid_user.deactivate()
        assert valid_user.is_active is False
        valid_user.activate()
        assert valid_user.is_active is True

