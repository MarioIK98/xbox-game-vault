# AGENTS.md — MARIO WORKSYSTEM 4.2

## Identity
- PROJECT_OBJECT_ID: P-007
- APPLICATION_OBJECT_ID: A-004
- ENGINEERING_WORKSPACE_ID: E-004
- CANONICAL_PROJECT: Game Vault

## Authority
Codex is the engineering executor for this repository.
It may inspect, implement, build, test, debug, and prepare commits within the authorized task.
It does not redefine product goals, FINAL/FROZEN decisions, publication policy, inventory truth, pricing rules, or project CURRENT.

## Existing-system-first
Before creating a new branch, worktree, helper, workflow, registry, or replacement implementation:
1. inspect the existing repository and current branch;
2. identify unrelated user changes;
3. prefer REUSE → REPAIR → ADAPT → EXTEND;
4. create NEW only when the existing path cannot satisfy the task cleanly;
5. document why a parallel worktree/path is necessary.

Do not create a second project truth.

## Evidence
Every completion claim must identify, when applicable:
- repository
- branch/worktree
- commit or working-tree state
- toolchain/version
- commands/tests
- exact pass/fail/partial result
- artifact
- unresolved defects

## State separation
Code change ≠ build success ≠ test success ≠ publication acceptance.

## Publication policy
Game Vault has an existing public web presence.
Do not change public publication semantics, legal notices, pricing rules, inventory truth, buyer-flow behavior, or release state outside an explicitly authorized task.

## Unified execution loop
INTAKE → CURRENT_BEFORE → INSPECT → IMPLEMENT → TEST → EVIDENCE → PROPOSED_CURRENT_AFTER → HANDOFF.

The canonical project chat/authority accepts or rejects PROPOSED_CURRENT_AFTER.
Codex does not set project CURRENT by itself.

## Completion handoff
Return:
- object/task identity
- CURRENT_BEFORE
- what changed
- files/commits/worktree
- tests and exact results
- artifacts
- evidence
- remaining failures/open items
- PROPOSED_CURRENT_AFTER
- rollback/recovery note
- reusable learning
- what the canonical project chat must decide next
