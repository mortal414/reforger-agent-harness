# Pinned vehicle candidate preflight

Use one addon-owned `candidate-ledger.json` for the selected candidate. This is an
optional extension of `tools/workflow.py`, not another harness or native adapter.
It applies to tanks, tank destroyers, antiaircraft vehicles and gun cars through
explicit per-vehicle contracts. No particular bone, fuel capacity or single-tank
layout is a global rule. Do not copy private ledgers or source into this repository.

```powershell
python -B tools/workflow.py preflight --ledger '<addon>/qa/candidate-ledger.json'
python -B tools/workflow.py plan --job '<addon>/qa/integrated-job.json'
```

An existing job opts in with `"candidateLedger": "candidate-ledger.json"`. Its
manifest must include the actual planned project and world. Planning pins the
ledger, manifest, facts, every declared source file and restored Library artifact;
the existing before/after-case verification detects later edits. Old jobs retain
their existing behavior. No command here launches an application, sends input,
transfers files, modifies a Library helper, claims/releases a lease or retries an API.

Exit 0 means no declared contradiction was found; output remains `NOT_TESTED`.
Exit 2 means a missing/malformed/stale artifact or a known readiness contradiction.
Neither result establishes native compile/load, complete source coverage, correct
effective inheritance, actual input or vehicle acceptance.

## Three existing artifact roles, one selected ledger

The addon owner supplies a complete source manifest and exports normalized facts
using its existing source/registry inspection or read-only observer. This checker
does **not** parse Enfusion inheritance or generate correct facts from a prefab.
Facts must describe the real effective inherited configuration, not just the local
override; a hand-written assertion is not independent engine evidence. Preserve
the raw source/registry/readback receipt beside the facts, record its provenance
in the addon handoff, and retain fresh native readback as an acceptance gate.

The ledger uses schema 1, a safe `candidateId`, optional `supersedes` IDs, SHA256
pins for `manifest`/`facts`, `contracts`, and optional `libraryPins`. Paths in pins
resolve beside the ledger; source and resource paths resolve beside the manifest.

```json
{
  "schema": 1,
  "candidateId": "vehicle-service-r2",
  "supersedes": ["vehicle-service-r1"],
  "manifest": {"path": "source-manifest.json", "sha256": "<64 lowercase hex>"},
  "facts": {"path": "preflight-facts.json", "sha256": "<64 lowercase hex>"},
  "contracts": {
    "contexts": [
      {"name": "cargo", "frame": "entity", "position": [0, 1, -2], "tolerance": 0.001}
    ],
    "fuelNodes": [{"nodeId": "inherited-stock-node-id", "capacity": 50}]
  },
  "libraryPins": []
}
```

The illustrative capacity/point are placeholders, not stock vehicle values. An
intentionally multi-tank vehicle declares each distinct effective node. Omit a
contract only when it is outside this change's preflight scope; omission does not
remove its integrated acceptance requirement or turn it into PASS.

The manifest is `{"schema":1,"files":[...]}`. Each file has `path`, `sha256` and
optionally an uppercase 16-digit `resourceId`. Supply full source closure, not only
changed files. Selected IDs must be unique; exported facts must match the exact
declared path/ID map. Normal project/dependency/world checks still run separately.

Facts have these required fields:

```json
{
  "schema": 1,
  "candidateId": "vehicle-service-r2",
  "manifestSha256": "<hash of the exact source-manifest.json>",
  "resources": [{"path": "addon.gproj", "resourceId": "0123456789ABCDEF"}],
  "contexts": [{"name": "cargo", "frame": "entity", "position": [0, 1, -2]}],
  "fuelNodes": [{"nodeId": "inherited-stock-node-id", "capacity": 50}]
}
```

Facts are pinned to the candidate and manifest. Hashing a new manifest does not
refresh an old readback. Re-export/review facts after a source change; never relabel
an old failure to satisfy the checker. XYZ tolerance is an explicit contract value.

## Optional readiness evidence

An `input` facts object has boolean `capability`, `foreground`, `occupied`,
`reservationsReleased`, an array `transitionTags` containing observed active
primary/secondary transition tags, and integer `requestedEvents`/`deliveredEvents`.
Use the actual source slot/manager and fresh target identity in the addon adapter.
An empty tag array is a measured result, not a default for unavailable graph data.

- Capability/readiness with counts 0/0 means `readyForProbe`, not input success.
- A positive request with zero or partial delivery blocks with `INPUT_NOT_DELIVERED`.
  Preserve the attempted pulse and possible partial side effects; no blind retry.
- Complete reported delivery still has `behaviorQualified: false` and status
  `NOT_TESTED`; a physical positive control and actual vehicle response remain.
- Missing input evidence remains untested. The checker never calls SendInput.

An optional `transfer` object has `metadataSupported` (boolean), `expectedFiles`,
`completedFiles` (integers), and `error` (null or the original error string).
Unsupported metadata or an `os.setxattr` error is `TRANSFER_CAPABILITY_ERROR`;
zero/partial files are `TRANSFER_INCOMPLETE`. Do not patch a managed helper, omit
required metadata or bypass a denied transfer API. Report the original operation,
target and error; use only a separately authorized supported transfer route.

Successful local transfer consistency requires one `libraryPins` entry per file:
`path`, `sha256`, durable `fileId` and `version`. Keep those pins in the persistent
addon ledger/handoff independently of a disposable workspace. After a reset,
restore the exact approved Library version through authorized tools and recheck
its bytes. Missing or different local bytes block. These pins do not independently
verify a remote upload, remote version identity, permissions or transfer success.

An optional `previousAttempt` has `state`, `operationId`, `reason`,
`verifiedExited`, `leaseReleased`. It admits only `EXITED_VERIFIED` with both
booleans true. Pending/uncertain/denied operations and a shutdown hang stop planning;
a timeout or new ledger does not authorize resubmission, process closure or release.
The addon owner must first reconcile the same operation and obtain fresh ownership
evidence. Pinned receipts are historical observations, never a live lease census.

## Failure-to-check and change-to-test matrix

These are offline fixtures/mocks, not native qualification. Retain the existing
46-test coordinator/recipe suite plus the candidate fixtures in `test_workflow.py`.

| Failure / root cause | Preventive check and offline test | Next manual/native gate |
|---|---|---|
| E98 service points used the `v_body` frame for entity coordinates | Explicit frame/XYZ contract; `test_wrong_bone_frame_blocks_before_any_launch`, position/missing-fact tests | Native actual-point readback and ordinary reachable prompts |
| E98 local fuel node added beside inherited stock node | Exact effective node IDs/count/capacity; additional-node and duplicate-node tests; explicit multi-node exception test | Native effective node readback, finite transfer, capacity/cancel/conservation and drive |
| Stale source, world, resource or handoff selected | Full manifest/facts hashes, candidate ID and resource map; changed-source/resource, stale-facts and project/world-binding tests | Fresh registry/compile/load of the exact selected closure |
| Windows Library metadata API missing; zero files | Transfer capability/error and verified-count checks; metadata-error, zero-file and transfer-pin tests | Supported authorized transfer receipt, exact remote version and restored bytes |
| Workspace reset loses local evidence | Durable Library ID/version/hash pins; missing/changed/restored-byte tests | Restore exact approved artifact; independently verify remote identity |
| SendInput returned 0 or partial delivery | Separate capability and event counts; zero/partial delivery tests | Fresh target/focus, one admitted pulse and observed positive-control behavior |
| Seat/controller settled before door graph cleanup | Reservation plus actual active-transition evidence; graph/readiness tests | Ordinary single action after measured source cleanup, both-side/return-leg checks |
| Shutdown hang or unresolved handoff | Previous-operation state plus explicit exit/release; pending/uncertain/denied test | Owner reconciles exact operation/session/lease; no inferred closure or retry |

Select the smallest next native set by the changed ownership boundary:

| Change | Required next set | Historical matrices normally held |
|---|---|---|
| Ledger, docs, transfer or offline checker only | Offline coordinator/candidate suite; artifact identity check | Gameplay matrices; no gameplay PASS inferred |
| Context/fuel/service-only production change | Source/compile/registry once; one integrated cargo/refuel/light/repair course; adjacent drive/crew/weapon smoke on that frozen candidate | Full graph/physics/ballistics sweeps while those owners remain hash-identical |
| Graph/compartment/input change | Matched stock/accepted control, actual cleanup, both-side entry/exit, seat-switch return and restored use | Armor/ballistics and full handling matrix if unrelated owners are unchanged |
| Physics, hull/child ownership or driving change | Signed powered driving/braking/slope/contact and crew/weapon interaction regression | Unaffected release-image/transfer matrices |
| Weapon/damage/repair owner change | Indexed fire/empty/reload/refire/rearm, native damage and restored-function regression | Unaffected model/export or transfer matrices |
| Accepted source ready for promotion | Integrated ordinary-use smoke and one batched appearance/audio pass, package/notices/dependency review | Repeat already-qualified isolated failures only when new evidence changes attribution |

Skipping an unaffected historical matrix is a scoped reuse decision, not a PASS.
The integrated ordinary-use acceptance remains required. Preserve E89 rollback,
E88 failures/E91 cleanup controls, E96's limited repair proof and E98/E99 evidence
in the private addon history; do not copy private fixtures into the public harness.
MP/JIP, historical ballistics and destructive stress remain separate obligations.

Record each future issue in the addon ledger/handoff as failure, root cause or
explicit unknown, preventive check, offline test, remaining manual gate and exact
next operation/owner. This extends the existing workflow; do not reapply the prior
49-line handoff/recovery documentation patch or make a new framework per vehicle.
