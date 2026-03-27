# Testing Strategy

## 1. What Must Be Unit Tested (Backend)
- **Service Logic**: Pricing calculations, recursive tier discounts, status transitions.
- **Pydantic Models**: Validation rules (e.g., "Quantity > 0").
- **Utility Functions**: Date helpers, formatters.
- **Coverage Target**: 80% on Service layer.

## 2. What Must Be Integration Tested (API)
- **Happy Paths**: Create Order -> Approve -> Deliver.
- **Auth Enforcement**: Verify Sales user cannot access Admin endpoints.
- **DB Constraints**: unique emails, foreign keys.

## 3. Critical Critical Flows (Must Have Tests)
These strictly require E2E or Integration tests:
1.  **Offline Sync Simulation**:
    - Create mutation -> Serialize -> Mock Network -> Deserialize -> API Process.
    - Verify Idempotency (Replay same mutation 3 times = 1 DB record).
2.  **Partial Delivery Math**:
    - Order 10 -> Deliver 3 -> Expect 7 Outstanding.
    - Deliver 8 -> Expect Error (3+8 > 10).
3.  **Manufacturing Updates**:
    - Ensure status flips to `Ready for Delivery` exactly when last item completes.

## 4. Manual Testing Acceptance (V1)
- **UI Responsiveness**: Checking layout on actual iPad/Mobile.
- **Offline Hard Toggle**: Turning off WiFi on device and attempting flows.
- **Background Sync**: Closing the app and reopening to check sync.

## 5. Explicitly Not Tested in V1
- **Load Testing**: We assume volume is low (<1000 orders/day).
- **Chaos Engineering**: Random server kills not simulated.
- **Browser Compatibility**: We target Chrome/Safari (Webkit/Blink) latest. IE/Old Edge ignored.
