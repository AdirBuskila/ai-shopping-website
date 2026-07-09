from app.core.security import (create_access_token, decode_token,
                               hash_password, verify_password)


def test_hash_roundtrip():
    h = hash_password("s3cret")
    assert h != "s3cret"  # never plaintext
    assert verify_password("s3cret", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    tok = create_access_token("42")
    assert decode_token(tok) == "42"


def test_jwt_tampered_returns_none():
    assert decode_token("not.a.jwt") is None
