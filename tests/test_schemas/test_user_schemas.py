import asyncio
import uuid
import pytest
from app.services.user_service import UserService
from pydantic import ValidationError
from datetime import datetime
from app.schemas.user_schemas import UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse, LoginRequest

# Fixtures for common test data
@pytest.fixture
def user_base_data():
    return {
        "nickname": "john_doe_123",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "AUTHENTICATED",
        "bio": "I am a software engineer with over 5 years of experience.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe.jpg",
        "linkedin_profile_url": "https://linkedin.com/in/johndoe",
        "github_profile_url": "https://github.com/johndoe"
    }

@pytest.fixture
def user_create_data(user_base_data):
    return {**user_base_data, "password": "SecurePassword123!"}

# TEST 9 - Integration Tests with Email Service
def test_user_registration_with_email_confirmation(user_create_data, db_session, email_service_mock):
    user = asyncio.run(UserService.register_user(db_session, user_create_data, email_service_mock))
    assert user is not None
    email_service_mock.send_verification_email.assert_called_once_with(user.email)

# TEST 8 - Security Tests
def test_password_hashing_on_creation(user_create_data, db_session):
    user = asyncio.run(UserService.create(db_session, user_create_data, None))
    assert user.password != user_create_data["password"]  # Assuming password is hashed and therefore different

@pytest.fixture
def user_update_data():
    return {
        "email": "john.doe.new@example.com",
        "nickname": "j_doe",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "I specialize in backend development with Python and Node.js.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe_updated.jpg"
    }

# TEST 5 - Boundary Tests for User Fields
@pytest.mark.parametrize("nickname", ["a"*50, "b"*2])  # Assuming 50 is max and 2 is min
def test_user_nickname_boundaries(nickname, user_base_data):
    user_base_data["nickname"] = nickname
    if len(nickname) >= 3 and len(nickname) <= 50:
        user = UserBase(**user_base_data)
        assert user.nickname == nickname
    else:
        with pytest.raises(ValidationError):
            UserBase(**user_base_data)


@pytest.fixture
def user_response_data(user_base_data):
    return {
        "id": uuid.uuid4(),
        "nickname": user_base_data["nickname"],
        "first_name": user_base_data["first_name"],
        "last_name": user_base_data["last_name"],
        "role": user_base_data["role"],
        "email": user_base_data["email"],
        # "last_login_at": datetime.now(),
        # "created_at": datetime.now(),
        # "updated_at": datetime.now(),
        "links": []
    }

# TEST 6 - Temporal Field Tests
def test_user_temporal_fields(user_response_data):
    now = datetime.now()
    user_response_data.update({"last_login_at": now, "created_at": now, "updated_at": now})
    user = UserResponse(**user_response_data)
    assert user.last_login_at == now
    assert user.created_at == now
    assert user.updated_at == now

@pytest.fixture
def login_request_data():
    return {"email": "john_doe_123@emai.com", "password": "SecurePassword123!"}

# Tests for UserBase
def test_user_base_valid(user_base_data):
    user = UserBase(**user_base_data)
    assert user.nickname == user_base_data["nickname"]
    assert user.email == user_base_data["email"]

# Tests for UserCreate
def test_user_create_valid(user_create_data):
    user = UserCreate(**user_create_data)
    assert user.nickname == user_create_data["nickname"]
    assert user.password == user_create_data["password"]

# Tests for UserUpdate
def test_user_update_valid(user_update_data):
    user_update = UserUpdate(**user_update_data)
    assert user_update.email == user_update_data["email"]
    assert user_update.first_name == user_update_data["first_name"]

# Tests for UserResponse
def test_user_response_valid(user_response_data):
    user = UserResponse(**user_response_data)
    assert user.id == user_response_data["id"]
    # assert user.last_login_at == user_response_data["last_login_at"]

# Tests for LoginRequest
def test_login_request_valid(login_request_data):
    login = LoginRequest(**login_request_data)
    assert login.email == login_request_data["email"]
    assert login.password == login_request_data["password"]

# Parametrized tests for nickname and email validation
@pytest.mark.parametrize("nickname", ["test_user", "test-user", "testuser123", "123test"])
def test_user_base_nickname_valid(nickname, user_base_data):
    user_base_data["nickname"] = nickname
    user = UserBase(**user_base_data)
    assert user.nickname == nickname

@pytest.mark.parametrize("nickname", ["test user", "test?user", "", "us"])
def test_user_base_nickname_invalid(nickname, user_base_data):
    user_base_data["nickname"] = nickname
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# Parametrized tests for URL validation
@pytest.mark.parametrize("url", ["http://valid.com/profile.jpg", "https://valid.com/profile.png", None])
def test_user_base_url_valid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    user = UserBase(**user_base_data)
    assert user.profile_picture_url == url

@pytest.mark.parametrize("url", ["ftp://invalid.com/profile.jpg", "http//invalid", "https//invalid"])
def test_user_base_url_invalid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# TEST 7 - Concurrency Tests (example concept, practical implementation would depend on your test setup and framework)
def test_concurrent_user_creations(user_create_data, db_session):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(asyncio.run, UserService.create(db_session, user_create_data, None)) for _ in range(10)]
        results = [f.result() for f in futures]
        # Verify all users are created without any data corruption or lost updates
        assert all(result is not None for result in results)
        assert len(set(user.email for user in results)) == 10  # assuming email should be unique and is adjusted in user_create_data
