import urllib.request
import urllib.parse
import json
import sys
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
            data = res_json.get("data", res_json) # Fallback if not wrapped?
            print(f"[OK] GET {path} - {len(data)} items")
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
        # Read error body if possible
        try:
             err_body = e.read().decode() if hasattr(e, 'read') else str(e)
        except:
             err_body = str(e)
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


def post_list(path, token, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            data = res.get("data", res)
            print(f"[OK] POST {path} - {len(data)} items")
            return data
    except Exception as e:
        print(f"[FAIL] POST {path}: {e}")
        sys.exit(1)

def get_public(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            data = res_json.get("data", res_json)
            print(f"[OK] GET {path} - {len(data)} items")
            return data
    except Exception as e:
        print(f"[FAIL] GET {path}: {e}")
        sys.exit(1)


def post_public(path, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            data = res.get("data", res)
            print(f"[OK] POST {path} - ID: {data.get('id')}")
            return data
    except Exception as e:
        try:
            err_body = e.read().decode() if hasattr(e, 'read') else str(e)
        except:
            err_body = str(e)
        print(f"[FAIL] POST {path}: {e} - {err_body}")
        sys.exit(1)


def patch_public(path, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PATCH")
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


def main():
    print("--- Smoke Tests ---")
    
    # 1. Login
    admin_token = login("admin@gardensolutions.com", "admin123")
    sales_token = login("sales@gardensolutions.com", "sales123")
    mfg_token = login("manufacturing@gardensolutions.com", "mfg123")
    delivery_token = login("delivery@gardensolutions.com", "delivery123")

    # 2. Public Products
    public_products = get_public("/public/products")
    if not public_products:
        print("[FAIL] No public products found")
        sys.exit(1)

    if not public_products[0].get("skus"):
        print("[FAIL] Public products missing skus")
        sys.exit(1)

    sku_id = public_products[0]["skus"][0]["id"]

    # 3. Public Clients
    public_clients = get_public("/public/clients")
    if not public_clients:
        print("[FAIL] No public clients found")
        sys.exit(1)

    client_id = public_clients[0]["id"]

    # 4. Create product + SKU (admin)
    product = post(
        "/products",
        admin_token,
        {"name": "Smoke Test Product", "description": "Smoke test", "category": "Smoke"},
    )
    product_id = product["id"]
    sku = post(
        f"/products/{product_id}/skus",
        admin_token,
        {
            "code": f"SMOKE-{product_id[:6]}",
            "size": "M",
            "color": "Grey",
            "base_price_rands": 99.99,
            "stock_quantity": 10,
        },
    )

    # 5. Upload product image
    image_path = Path(__file__).parent / "fixtures" / "product_image.png"
    upload_url = f"{BASE_URL}/products/{product_id}/image"
    boundary = "----SmokeTestBoundary"
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    multipart = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="product_image.png"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(upload_url, data=multipart, method="POST")
    req.add_header("Authorization", f"Bearer {admin_token}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        uploaded = res.get("data", res)
        if not uploaded.get("image_url"):
            print("[FAIL] Product image upload missing image_url")
            sys.exit(1)
        image_url = uploaded["image_url"]

    # Verify static URL returns 200
    static_url = f"http://localhost:8000{image_url}"
    try:
        with urllib.request.urlopen(static_url) as response:
            if response.status != 200:
                print("[FAIL] Static image URL returned non-200")
                sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Static image URL fetch failed: {e}")
        sys.exit(1)

    # 6. Bulk import (admin)
    bulk_payload = {
        "products": [
            {
                "name": "Smoke Bulk Product",
                "category": "Smoke",
                "description_html": "Bulk import",
                "skus": [
                    {
                        "code": "SMOKE-BULK-001",
                        "size": "M",
                        "color": "Black",
                        "base_price_rands": 199.99,
                        "stock_quantity": 5,
                    }
                ],
            }
        ]
    }
    bulk_result = post_list("/products/bulk", admin_token, bulk_payload)
    if not bulk_result:
        print("[FAIL] Bulk import returned empty result")
        sys.exit(1)

    # 7. Public products should include new product
    public_products_after = get_public("/public/products")
    if not any(p["id"] == product_id for p in public_products_after):
        print("[FAIL] Public products missing newly created product")
        sys.exit(1)

    # 8. Deactivate product and verify it disappears from public list
    patch(f"/products/{product_id}", admin_token, {"is_active": False})
    public_products_after_deactivate = get_public("/public/products")
    if any(p["id"] == product_id for p in public_products_after_deactivate):
        print("[FAIL] Deactivated product still visible in public products")
        sys.exit(1)

    # 9. Authenticated Products (existing endpoint)
    products = get("/products", sales_token)
    if not products:
        print("[FAIL] No products found")
        sys.exit(1)
    
    # 10. Authenticated Clients (existing endpoint)
    clients = get("/clients", sales_token)
    if not clients:
        print("[FAIL] No clients found")
        sys.exit(1)
    
    # 11. Resolve sales agent code (public)
    agent = post_public("/sales-agents/resolve", {"code": "S-TEST"})

    # 12. Resolve store code (public)
    store = post_public("/stores/resolve", {"code": "POT-001"})

    # 13. Public Create Store Order (no client_id)
    store_order_payload = {
        "store_code": store["code"],
        "delivery_date": "2024-12-31",
        "items": [
            {"sku_id": sku_id, "quantity_ordered": 2}
        ]
    }
    post_public("/public/orders", store_order_payload)

    # 14. Public Create Client Order
    order_payload = {
        "client_id": client_id,
        "delivery_date": "2024-12-31", # YYYY-MM-DD
        "sales_agent_code": agent["code"],
        "items": [
            {"sku_id": sku_id, "quantity_ordered": 5}
        ]
    }
    order = post_public("/public/orders", order_payload)
    order_id = order["id"]
    
    # 15. Approve Order
    # Assuming PATCH /orders/{id}/status expecting { "status": "Approved" }
    # Check STATUS_MODEL.md or API_REFERENCE for precise string.
    # Usually "Approved" or "APPROVED". The seed uses Enums in Python. The JSON usually outputs what the Enum value is.
    # I'll check what the order status currently is.
    print(f"Current Status: {order['status']}")
    
    patch(f"/orders/{order_id}/status", admin_token, {"status": "approved"})

    # 16. Manufacturing: mark all items for created order as manufactured
    for item in order["items"]:
        patch(
            f"/order-items/{item['id']}/manufactured",
            mfg_token,
            {"quantity_manufactured": item["quantity_ordered"]},
        )

    # 17. Assign delivery team (admin)
    teams = post_public("/delivery-teams/resolve", {"code": "D-TEST"})
    patch(f"/orders/{order_id}/assign-delivery-team", admin_token, {"delivery_team_id": teams["id"]})

    # 18. Public delivery queue should include order for team and date
    delivery_queue = get_public(f"/public/delivery/queue?team_code={teams['code']}&date=2024-12-31")
    if not delivery_queue:
        print("[FAIL] Delivery queue is empty")
        sys.exit(1)

    delivery_order = next((o for o in delivery_queue if o["id"] == order_id), None)
    if not delivery_order:
        print("[FAIL] Created order not found in delivery queue")
        sys.exit(1)

    delivery_item_id = delivery_order["items"][0]["id"]

    # 19. Public partial outcome
    patch_public(
        f"/public/delivery/orders/{order_id}/outcome",
        {
            "team_code": teams["code"],
            "outcome": "partial",
            "receiver_name": "Front Desk",
            "reason": "Partial stock delivered",
            "items": [{"order_item_id": delivery_item_id, "quantity_delivered": 1}],
        },
    )

    # 20. Public delivered outcome (complete)
    patch_public(
        f"/public/delivery/orders/{order_id}/outcome",
        {
            "team_code": teams["code"],
            "outcome": "delivered",
            "receiver_name": "Front Desk",
        },
    )

    # 21. Delivery queue should no longer include order
    delivery_queue_after = get_public(f"/public/delivery/queue?team_code={teams['code']}&date=2024-12-31")
    if any(o["id"] == order_id for o in delivery_queue_after):
        print("[FAIL] Delivered order still in delivery queue")
        sys.exit(1)
    
    print("\n[SUCCESS] All Smoke Tests Passed!")

if __name__ == "__main__":
    main()
