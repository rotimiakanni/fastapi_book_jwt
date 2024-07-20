import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from book_app.database import Base, get_db
from book_app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///"

engine = create_engine(SQLALCHEMY_DATABASE_URL, 
                       connect_args={"check_same_thread": False}, 
                       poolclass=StaticPool,)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.parametrize("username, password, full_name", [("testuser", "testpassword", "Test User")])
def test_signup(client, setup_database, username, password, full_name):
    response = client.post("/signup", json={"username": username, "password": password, "full_name": full_name})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username

@pytest.mark.parametrize("username, password, full_name", [("testuser2", "testpassword", "Test User")])
def test_login(client, setup_database, username, password, full_name):
    # First, sign up the user
    response = client.post("/signup", json={"username": username, "password": password, "full_name": full_name})
    assert response.status_code == 200

    # Then, log in the user
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.parametrize("username, password", [("testuser", "testpassword")])
def test_get_books(client, setup_database, username, password):
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Then, get the books
    response = client.get("/books/")
    assert response.status_code == 401
    response = client.get("/books/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data

@pytest.mark.parametrize("username, password", [("testuser", "testpassword")])
def test_create_book(client, setup_database, username, password):
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Then, create a book
    book_data = {"title": "Test Book", "author": "Test Author", "description": "A good book"}
    response = client.post("/books", json=book_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data['data']['title'] == "Test Book"