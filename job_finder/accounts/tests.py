import pytest
from accounts.models import CustomUser


@pytest.mark.django_db
class TestCustomUserModel:
    def test_custom_user_creation(self):
        user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.check_password("testpass123")

    def test_custom_user_str_representation(self):
        user = CustomUser.objects.create_user(
            username="johndoe", email="john@example.com", password="pass123"
        )
        assert str(user) == "john@example.com"

    def test_custom_user_email_unique(self):
        CustomUser.objects.create_user(
            username="user1", email="unique@example.com", password="pass123"
        )
        with pytest.raises(Exception):
            CustomUser.objects.create_user(
                username="user2", email="unique@example.com", password="pass123"
            )

    def test_custom_user_allows_empty_email(self):
        """Django's create_user allows empty email string"""
        user = CustomUser.objects.create_user(
            username="testuser", email="", password="pass123"
        )
        assert user.email == ""

    def test_custom_user_superuser(self):
        user = CustomUser.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_custom_user_is_active_default(self):
        user = CustomUser.objects.create_user(
            username="activeuser", email="active@example.com", password="pass123"
        )
        assert user.is_active is True
