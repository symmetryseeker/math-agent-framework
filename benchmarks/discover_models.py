"""Attempt to discover models from BIT MAAS platform."""
import urllib.request, urllib.parse, json, http.cookiejar, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

USERNAME = "3120251973"
PASSWORD = "A@mkwcdf8"
BASE = "https://maas.bit.edu.cn"

# Step 1: Try to login to GPUStack web app
data = urllib.parse.urlencode({"username": USERNAME, "password": PASSWORD}).encode()
paths = [
    "/api/v1/login/access-token",
    "/login/access-token",
    "/api/token",
    "/token",
    "/api/v1/token",
]

token = None
for path in paths:
    try:
        req = urllib.request.Request(
            f"{BASE}{path}", data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        resp = opener.open(req, timeout=10)
        body = json.loads(resp.read())
        print(f"{path}: {json.dumps(body)[:200]}")
        if "access_token" in body:
            token = body["access_token"]
            break
        if "token" in body:
            token = body["token"]
            break
    except Exception as e:
        print(f"{path}: {e}")

if token:
    print(f"\nGot token! Using it to list models...")
    req2 = urllib.request.Request(
        f"{BASE}/v1-openai/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    resp2 = opener.open(req2, timeout=10)
    models = json.loads(resp2.read())
    print(json.dumps(models, indent=2)[:1000])
else:
    print("\nCould not get token. The platform requires an API key from the web console.")
    print("Please login to https://maas.bit.edu.cn/ and create an API Key.")
