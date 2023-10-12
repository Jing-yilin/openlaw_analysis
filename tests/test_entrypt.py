import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from src.utils import encrypt_js

def test_encrypt_js():
    password = "123456"
    encrypted_pwd = encrypt_js(password)
    print(encrypted_pwd)
    pwd_len = len("""Rz3rS4ZDgpFRZUYZ7l/tlr5vUZW0BaSgK8yaMYw8+PoV3IA1mCssbxMH/1ykN0qiOmlHMuiUcltIYnyLLo83b3+wkF8aolRKDoalYXI9M9DFJ5z+2xV+EG4pzlB6dXRJ7OA7s8l0Rk0PmMo1DyiP6rDImUCHpLl82mVWtYj59eFE7HAZacBjBI7ZLA/JhHUsd6WF4cpse1xdo1W3Szj67QL6bvex91xPeLrPLFguWNPq9vwEpLeV2BSdYwcaE67lhG74gIq6s9RaJhB7DO1FNqufwWV4jGquw8AOxnEqhQbXQdGwX05a3tpmZvxZSRDufkHH5ImeMSsv3Ehls3yQgg==:::G1+1NLtfE5ILlt1Jmh+Hhg==""")
    assert len(encrypted_pwd) == pwd_len