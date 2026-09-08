import requests

base = "http://127.0.0.1:8000/api"
reg = {
    "username": "paballo_api_test",
    "email": "paballo_api_test@example.com",
    "password": "TestPassword123",
    "first_name": "Paballo",
    "last_name": "Mofokeng",
    "role": "reader",
}

r = requests.post(base + "/register/", json=reg, timeout=10)
print("REG", r.status_code)
print(r.text)

tok = {"username": "paballo_api_test", "password": "TestPassword123"}
t = requests.post(base + "/token/", json=tok, timeout=10)
print("TOKEN", t.status_code)
print(t.text)

if t.status_code == 200:
    token = t.json().get("access")
    headers = {"Authorization": "Bearer " + token}
    u = requests.get(base + "/users/me/", headers=headers, timeout=10)
    print("ME", u.status_code)
    print(u.text)
