import pytest
from main import func


def test_answer():
    assert func(3) == 5
