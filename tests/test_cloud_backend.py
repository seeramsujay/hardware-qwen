import math
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cloud_backend import calculate_spoilage_curve, load_env_file

def test_spoilage_curve_safe_threshold():
    assert calculate_spoilage_curve(-25.0) == 999.0
    assert calculate_spoilage_curve(-18.0) == 999.0

def test_spoilage_curve_decay():
    # delta = 8.0 -> 48 * exp(-2) ~ 6.496 -> 6.5
    res = calculate_spoilage_curve(-10.0)
    expected = round(48.0 * math.exp(-0.25 * 8.0), 1)
    assert res == expected

    # extreme temperature
    res_high = calculate_spoilage_curve(50.0)
    assert res_high == 0.1

def test_load_env_file(tmp_path):
    env_file = tmp_path / ".env.test"
    env_file.write_text("""
    # This is a comment
    FOO=bar
    BAZ="qux"
    EMPTY=
    """)
    load_env_file(str(env_file))
    assert os.environ.get("FOO") == "bar"
    assert os.environ.get("BAZ") == "qux"
