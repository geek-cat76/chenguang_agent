from src.utils.jwt_utils import encode_jwt, verify_jwt

def test_encode_verify_jwt():
    jwt_token = encode_jwt({"user_id": 1})
    payload = verify_jwt(jwt_token)
    assert payload["user_id"] == 1


def test_token():
    jwt_token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MiwidXNlcm5hbWUiOiJseWgiLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJleHAiOjE3ODQ3MTM3ODQsImlhdCI6MTc4NDcxMTk4NH0.sSI-XEqd6AtOiZkZosNReQ9SBc6_uQh1puccs7f1EEA"
    payload = verify_jwt(jwt_token)
    print(payload)
    assert payload["id"] == 2
    assert payload["username"] == "lyh"
    assert payload["is_superuser"] == False



