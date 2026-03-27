import urllib.request
import urllib.parse
import json
import sys
import uuid
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def login(email, password):
    url = f"{BASE_URL}/auth/login"
    data = urllib.parse.urlencode({
        "username": email,
        "password": password
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            print(f"[OK] Login {email}")
            return res_json["data"]["access_token"]
    except Exception as e:
        print(f"[FAIL] Login {email}: {e}")
        sys.exit(1)

def get(path, token):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            data = res_json.get("data", res_json)
            # Handle list vs dict
            count = len(data) if isinstance(data, list) else 1
            print(f"[OK] GET {path} - {count} items")
            return data
    except Exception as e:
        print(f"[FAIL] GET {path}: {e}")
        sys.exit(1)

def post(path, token, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            data = res.get("data", res)
            print(f"[OK] POST {path} - ID: {data.get('id')}")
            return data
    except Exception as e:
        err_body = str(e)
        try:
             err_body = e.read().decode() if hasattr(e, 'read') else str(e)
        except:
             pass
        print(f"[FAIL] POST {path}: {e} - {err_body}")
        sys.exit(1)

def patch(path, token, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PATCH")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            data = res.get("data", res)
            print(f"[OK] PATCH {path}")
            return data
    except Exception as e:
        print(f"[FAIL] PATCH {path}: {e}")
        sys.exit(1)

def delete(path, token, expect_fail=False):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="DELETE")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as response:
            if expect_fail:
                print(f"[FAIL] DELETE {path} succeeded but expected failure")
                sys.exit(1)
            print(f"[OK] DELETE {path}")
            return True
    except urllib.error.HTTPError as e:
        if expect_fail and e.code == 409:
            print(f"[OK] DELETE {path} failed as expected (409)")
            return False
        print(f"[FAIL] DELETE {path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] DELETE {path}: {e}")
        sys.exit(1)

def main():
    print("--- Price Tiers Verification ---")
    
    # 1. Login
    admin_token = login("admin@gardensolutions.com", "admin123")
    
    # 2. Create Price Tier
    suffix = str(uuid.uuid4())[:8]
    tier_name = f"Tier Verify {suffix}"
    tier = post(
        "/price-tiers",
        admin_token,
        {"name": tier_name, "discount_percentage": 0.15, "is_active": True}
    )
    tier_id = tier["id"]

    # 3. List Tiers
    tiers = get("/price-tiers", admin_token)
    if not any(t["id"] == tier_id for t in tiers):
        print(f"[FAIL] Created tier {tier_id} not found in list")
        sys.exit(1)

    # 4. Update Tier
    updated_tier = patch(
        f"/price-tiers/{tier_id}",
        admin_token,
        {"name": f"{tier_name} Updated", "discount_percentage": 0.20}
    )
    if updated_tier["discount_percentage"] != "0.2000" and float(updated_tier["discount_percentage"]) != 0.2:
        print(f"[FAIL] Updated discount mismatch: {updated_tier['discount_percentage']}")
        sys.exit(1)

    # 5. Check Usage (should be empty)
    usage = get(f"/price-tiers/{tier_id}/usage", admin_token)
    if usage["client_count"] != 0 or usage["store_count"] != 0:
        print(f"[FAIL] Usage not empty for new tier: {usage}")
        sys.exit(1)

    # 6. Assign to Client
    # Pick a client
    clients = get("/clients", admin_token)
    if not clients:
        print("[SKIP] No clients to test assignment")
    else:
        client_id = clients[0]["id"]
        original_tier = clients[0]["tier_id"]
        
        # Update client
        patch(f"/clients/{client_id}", admin_token, {"tier_id": tier_id})
        
        # Verify Usage
        usage = get(f"/price-tiers/{tier_id}/usage", admin_token)
        if usage["client_count"] != 1:
            print(f"[FAIL] Usage client_count expected 1, got {usage['client_count']}")
            sys.exit(1)

        # 7. Try Delete (Should Fail)
        delete(f"/price-tiers/{tier_id}", admin_token, expect_fail=True)

        # 8. Unassign (Revert)
        patch(f"/clients/{client_id}", admin_token, {"tier_id": original_tier})
        
        # Verify Usage Empty
        usage = get(f"/price-tiers/{tier_id}/usage", admin_token)
        if usage["client_count"] != 0:
             # Wait, maybe there's a delay? No, should be immediate transaction.
             print(f"[WARN] Usage not zero yet? {usage}. Proceeding to delete might fail.")

    # 9. Delete (Should Succeed)
    delete(f"/price-tiers/{tier_id}", admin_token)

    # 10. Verify Deleted
    tiers_after = get("/price-tiers", admin_token)
    if any(t["id"] == tier_id for t in tiers_after):
        print("[FAIL] Tier still exists in list after delete")
        sys.exit(1)

    print("\n[SUCCESS] Price Tiers Verification Passed!")

if __name__ == "__main__":
    main()
