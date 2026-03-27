# Quality Gates

## 1. Definition of Done (Feature)
- [ ] Code committed and merged to `main`.
- [ ] Unit tests pass.
- [ ] Documentation updated (if flow changed).
- [ ] Verified manually on "Mobile View" (DevTools).

## 2. Definition of Done (Order Data)
- **Pre-Approval**: Client Credit Check confirmed (manual).
- **Post-Delivery**: POD (Proof of Delivery) name recorded. Correct quantities logged.

## 3. Merge Checks (CI Execution)
- **Lint**: No ESLint warnings.
- **Format**: Prettier check passes.
- **Type Check**: `tsc --noEmit` passes (Zero TS errors).
- **Test**: `pytest` passes.

## 4. Release Checks (Staging to Prod)
- **Database**: Migrations applied successfully on Staging.
- **Smoke Test**: Admin can login. Sales agent can load catalogue.

## 5. Blocking Issues (Cannot Release)
- **Data Loss Risk**: Any bug in Sync logic.
- **Security**: Auth bypass possibilities.
- **Calculation Error**: Pricing or Quantity math wrong.

## 6. Non-Blocking Issues (Can Release with Known Bugs)
- **UI Glitches**: Minor pixel misalignment.
- **Performance**: Dasboard takes 2s to load (acceptable for V1).
- **Sort Order**: Lists not perfectly sorted by default.
