# pylint: disable=missing-docstring,protected-access,unused-argument,redefined-outer-name,invalid-name
from dataclasses import dataclass
from typing import Any
import pytest

from zetta_utils import builder


PARSE_KEY = "@type"
RECURSIVE_KEY = "@recursive_parse"
MODE_KEY = "@mode"


@dataclass
class DummyA:
    a: Any


@dataclass
class DummyB:
    b: Any


@pytest.fixture
def register_dummy_a():
    builder.parser.register("dummy_a")(DummyA)
    yield
    del builder.parser.REGISTRY["dummy_a"]


@pytest.fixture
def register_dummy_b():
    builder.parser.register("dummy_b")(DummyB)
    yield
    del builder.parser.REGISTRY["dummy_b"]


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        "abc",
        (1, "abc"),
        {"int": 1, "str": "abc", "tuple": (1, 2, 3), "dict": {"yes": "sir"}},
    ],
)
def test_identity_builds(value):
    result = builder.parser._build(value)
    assert result == value


@pytest.mark.parametrize(
    "value, expected_exc",
    [
        [1, TypeError],
        ["yo", TypeError],
        [{}, ValueError],
        [{"a": "b"}, ValueError],
        [{"@type": "something_not_registered"}, KeyError],
        [{"@type": "dummy_a", "a": 1, "@mode": "unsupported_mode_5566"}, ValueError],
        [{"@type": "dummy_a", "a": TypeError}, ValueError],
    ],
)
def test_parse_exc(value, expected_exc, register_dummy_a):
    with pytest.raises(expected_exc):
        builder.build(value)


def test_register(register_dummy_a):
    assert builder.parser.REGISTRY["dummy_a"] == DummyA


@pytest.mark.parametrize(
    "spec, expected",
    [
        [{"a": "b"}, {"a": "b"}],
        [{PARSE_KEY: "dummy_a", "a": 2}, DummyA(a=2)],
        [{PARSE_KEY: "dummy_b", "b": 2}, DummyB(b=2)],
        [
            {PARSE_KEY: "dummy_a", "a": [{PARSE_KEY: "dummy_b", "b": 3}]},
            DummyA(a=[DummyB(b=3)]),
        ],
        [
            {
                PARSE_KEY: "dummy_a",
                RECURSIVE_KEY: True,
                "a": ({PARSE_KEY: "dummy_b", "b": 3},),
            },
            DummyA(a=(DummyB(b=3),)),
        ],
        [
            {
                PARSE_KEY: "dummy_a",
                RECURSIVE_KEY: False,
                "a": ({PARSE_KEY: "dummy_b", "b": 3},),
            },
            DummyA(a=({PARSE_KEY: "dummy_b", "b": 3},)),
        ],
        [
            {PARSE_KEY: "dummy_a", MODE_KEY: "partial", "a": [{PARSE_KEY: "dummy_b", "b": 3}]},
            builder.ComparablePartial(DummyA, a=[DummyB(b=3)]),
        ],
    ],
)
def test_build(spec: dict, expected: Any, register_dummy_a, register_dummy_b):
    result = builder.build(spec, must_build=False)
    assert result == expected
    if hasattr(result, "__dict__"):
        assert result.__init_builder_spec == spec
