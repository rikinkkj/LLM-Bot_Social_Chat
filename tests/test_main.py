import pytest
from main import _parse_memory_string

@pytest.mark.parametrize("input_string, expected_output", [
    ("key: value", ("key", "value")),
    ("  key  :  value  ", ("key", "value")),
    ("complex key: a value with a : colon", ("complex key", "a value with a : colon")),
    ("key:value", ("key", "value")),
    ("None", None),
    ("none", None),
    ("NONE", None),
    ("No significant memory was formed.", None),
    ("key value", None),
    ("", None),
    (None, None)
])
def test_parse_memory_string(input_string, expected_output):
    """
    Tests the memory parsing logic with various valid and invalid inputs.
    """
    assert _parse_memory_string(input_string) == expected_output
