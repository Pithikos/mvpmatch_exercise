from api.models import User, Product

import pytest
from rest_framework.test import APIClient


USER_COUNTER = 0


@pytest.fixture
def client():
    yield APIClient()


def _user_factory(username, **kwargs):
    global USER_COUNTER
    USER_COUNTER += 1
    return User.objects.create(username=f"{username}{USER_COUNTER}", **kwargs)


@pytest.fixture
def user_factory(db):
    def factory(username, **kwargs):
        user = _user_factory(username, **kwargs)
        yield user
        user.delete()
    return factory


@pytest.fixture
def user(user_factory):
    yield from user_factory(username="testuser", role="buyer")


@pytest.fixture
def seller(user_factory):
    yield from user_factory(username="testuser", role="seller")


@pytest.fixture
def buyer(user_factory):
    yield from user_factory(username="testuser", role="buyer")
