# Change Management

## 1. Philosophy
- **Documentation is Code**: Changes to logic start in Markdown, not Typescript.
- **Zero Scope Creep**: "Cool ideas" go to `FUTURE_FEATURES.md`, not the codebase.

## 2. Process for New Features
1.  **Proposal**: Discuss with Stakeholders.
2.  **Doc Update**:
    - Add to `PRODUCT_REQUIREMENTS.md`.
    - Update `DATA_MODEL.md`.
    - Update `API_REFERENCE.md`.
3.  **Approval**: Lead Architect approves Doc changes.
4.  **Implementation**: Coding begins.

## 3. Instructing AI Agents
When asking an AI Agent (Antigravity/Claude) to implement a change:
- **Reference**: explicitly point them to the updated docs.
- **Constraint**: Tell them "Do not infer logic; follow `USER_FLOWS.md` strictly".
- **Verification**: Ask them to update `TESTING_STRATEGY.md` if the feature is critical.

## 4. Documentation Updates
- Docs must be kept "Live".
- If a developer realizes the `DATA_MODEL.md` is impossible to implement physically (e.g., circular dependency), they must update the doc **before** working around it.
