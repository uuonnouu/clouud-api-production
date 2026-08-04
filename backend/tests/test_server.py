import pytest

from backend import server


def test_normalize_and_encode_empty():
    assert server.normalize_and_encode({}) == ["STATE_TRANSITION|empty|null"]


def test_normalize_and_encode_order():
    assert server.normalize_and_encode({"b": 2, "a": 1}) == [
        "STATE_TRANSITION|a|1",
        "STATE_TRANSITION|b|2",
    ]


def test_generate_merkle_chain_consistency():
    states = ["STATE_TRANSITION|a|1", "STATE_TRANSITION|b|2"]
    root, hashes = server.generate_merkle_chain(states)
    assert root == hashes[-1]
    assert len(hashes) == 2
    assert all(isinstance(h, str) for h in hashes)


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({}, ["STATE_TRANSITION|empty|null"]),
        ({"x": {"y": 1}}, ["STATE_TRANSITION|x|{\"y\": 1}"]),
    ],
)
def test_normalize_and_encode_nested(payload, expected):
    assert server.normalize_and_encode(payload) == expected
