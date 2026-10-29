# Accomplish the work without desktop control

Find a supported programmatic route for each requested result. Reuse CLI tools,
existing scripts, editable configuration/resources, addon-owned registered
actions, telemetry and file-based requests. Split a large UI workflow into
operations: prepare files, run a supported native import/build, verify readbacks,
drive a deterministic test and batch captures. Build a small supported addon
adapter when that removes repeated desktop work. A missing adapter calls for
research/adaptation, not an assumption that mouse/keyboard is necessary.

Desktop input is the residual route after relevant supported alternatives are
shown unavailable for the exact task. Keep a short separate human acceptance
course for ordinary discovery, controls and integrated use. Registered actions
and state setters cannot satisfy that physical-input gate.

The ASU course is primarily an evaluation of how much the harness and Codex can
implement, diagnose and validate autonomously. A pending physical-usability claim
does not block supported programmatic functional tests or recoveries. Do not
offload a test to a person for convenience; ask only for a demonstrated residual
limit. For each attempt retain the action route, measured outcome, fixture
validity, any human intervention and the reusable workflow change learned.
Publishing is a separate explicitly authorized activity, not the purpose of a
functional harness pass.

## Discover before executing

```powershell
python tools/workflow.py routes --task create --claim job-created
python tools/workflow.py routes --task import --claim native-import
python tools/workflow.py routes --task playtest --claim measured-behavior
python tools/workflow.py lessons --symptom injected-input-zero-events
```

These commands start nothing, send no input and change no settings. The catalog
lists actual source paths, command shapes, evidence boundaries and concrete next
steps. Placeholder commands are recommendations to parameterize, never shell
strings executed by the router. `status: NOT_TESTED` always remains visible:
route admission does not prove behavior or grant permission.

| Task / exact claim | First supported route |
| --- | --- |
| Research / `source-discovery` | Configured installed source/docs/sample search and bounded readable resource metadata, `src/cli.ts` |
| Creation / `job-created`; validation / `static-plan` | Bindings and `workflow.py init/plan`; creates a QA job, not an addon/model |
| Configuration / `config-written` | `server:config` and explicit private job/binding files; effective inheritance needs native readback |
| Import / `import-plan` | Asset preparation recipe, existing addon exporter, official metadata contract and parity witnesses |
| Import / `native-import`; configuration / `native-resource-config` | Resource/import API or addon batch plugin remains **unverified** in this harness; inspect/adapt it before editor input |
| Validation / `scripts-compiled` | `workbench validate` with fresh diagnostics |
| Packaging / `package-artifact` | `workbench pack`, fresh output and pinned trio |
| Validation / `native-load` | Explicit direct-world client or qualified adapter; verify exact world as well as GAME |
| Playtest / `measured-behavior` | Addon registered actions and actual traverse/ammunition/crew/motion deltas; inspect persistent bindings first |
| Playtest or capture / `fixture-state` | Setup/reset/pose/seat helpers only; setters cannot qualify powered movement or public interaction |
| Capture / `native-image` | Native camera file job and telemetry/pixel reviewer; batch views instead of mouse positioning |
| Playtest / `injected-input-delivery` | Residual supported automation-delivery question, one bounded observed probe and stock control |
| Human acceptance / `human-usability` | Small exact-candidate physical course; HUMAN_REQUIRED, never autoexecuted |

There is no invented universal headless FBX importer, vehicle creator or resource
mutation API here. Check version-matched installed APIs, stock/examples and
working addon scripts, then register a minimal supported batch action if feasible.
Use the [research/reuse workflow](workflows.md#research-and-reuse-before-implementation)
to record the actual implementation, choice and remaining gap.

The [native action reuse map](native-action-reuse.md) supplies concrete existing
aim/drive/fire/reentry code locations and a reload-action lead for the staged ASU
course. Public component commands and direct simulation commands have distinct
catalog routes/methods; neither implies registered-action or physical delivery.

## Scoped preflight and adoption

Copy [route-context.example.json](../examples/workflows/route-context.example.json)
to the addon QA directory. Record current permission, ownership and prior outcome
truthfully. Unknown/pending states HOLD; denials stop the same goal across all
routes. A routing file records existing authorization and does not create it.
Never change a denied goal's route to evade a security boundary.

| Capability state | Meaning |
| --- | --- |
| `available` | Implementation exists; current native behavior remains unqualified |
| `validated` | Scoped retained evidence supports this route on the stated source/build; still not new-candidate acceptance |
| `unsupported` | Pinned scoped evidence shows this route cannot accomplish this claim in the current environment |
| `unverified` | Missing knowledge, implementation, measurements or applicability; research/adapt before desktop |

An assessment can promote `native-actions` or establish an unsupported alternative.
Its reason must name the exact candidate/build and capability; evidence pins
the reviewed implementation and relevant receipts. For example, add this under
`assessments`, replacing all placeholders with real current values:

```json
{
  "native-actions": {
    "state": "available",
    "reason": "Exact QA candidate/build and reviewed action adapter; native requalification still required",
    "evidence": [
      {"path": "adapter.py", "sha256": "<actual adapter SHA-256>"},
      {"path": "checks/healthy.json", "sha256": "<actual receipt SHA-256>"}
    ]
  }
}
```

Inspect those files: hashes establish identity, not truth. Old healthy evidence
does not qualify changed sources. Missing catalog source remains unverified even
with an assessment. Explicit desktop selection cannot override an available
programmatic alternative. Every relevant programmatic alternative must be
evidenced unsupported; unknown is a HOLD. Record `desktopReason` with the exact
residual operation and necessity. Native/desktop ownership must be clear;
independent authorized offline preparation may continue under an occupied session.

```powershell
python tools/workflow.py routes --context '<addon>/qa/route.json'
python tools/workflow.py init --help
python tools/workflow.py plan --job '<addon>/qa/job.json'
```

`routes --context` exits 2 for HOLD/HUMAN_REQUIRED, 0 for READY. Discovery exits 0
while displaying its unknown-state HOLD. Plans always remain NOT_TESTED.
`init --route-context <file>` adds the new job's `routeContext` path; an existing
job adds that one field. Paths inside the context resolve beside it. Planning
pins the context, catalog, lessons, route module, sources and assessment evidence;
the coordinator checks these pins around every case.

For desktop input probes, also add `inputControlSources` to that context. It is
an explicit pair of reviewed source/build/fixture manifests, each pinned by path
and SHA-256. Other input routes need the same pair whenever they supply a stock
control. Each manifest must identify the applicable resources, source/build,
fixture, dependencies and relevant test configuration; the adapter verifies that
closure against what the engine actually loads. A label or an unrelated file is
not qualification. The coordinator checks manifest bytes and equality; the owner
still reviews their contents and applicability.

```json
{
  "inputControlSources": {
    "stock": {"path": "stock-source-fixture.json", "sha256": "<actual manifest SHA-256>"},
    "candidate": {"path": "candidate-source-fixture.json", "sha256": "<actual manifest SHA-256>"}
  }
}
```

Planning hashes these files, pins them and carries their exact SHA-256 pair in
request `inputControlIdentity`. Missing pair holds desktop-probe admission.

**Execution admission changes in this version:** legacy jobs still plan and show
recommendations, but execute refuses before output creation/adapter launch until
a reviewed route context is READY. Template and claim must agree (`startup`:
native load or a measured healthy-control behavior case; `visual`: native image; `release`: package; other functional templates:
measured behavior). Adopt at a new session boundary, never by replacing a running
pinned coordinator. Adapter and job migration are required.

## Route evidence and behavior

Requests contain `route` (ID, mode, method, limits) and `claim`; planned cases add
mandatory `route.evidence`. Adapters return usual assertions plus actual reported
measurement provenance, for example (illustrative numbers, not native results):

```json
{
  "routeEvidence": {
    "routeId": "native-actions",
    "method": "registered-action",
    "measurements": {"actualTraverseDegrees": 12.4, "leftRoundsUsed": 2, "rightRoundsUsed": 2}
  }
}
```

Use current-run finite numeric/boolean measurements and durable raw evidence.
Missing proof keeps `route.evidence` NOT_TESTED even when all adapter assertions
say PASS. Wrong mechanisms or empty/null/string-only measurements cannot pass.
A route.evidence PASS establishes reported measurement presence/provenance only;
every passing native or desktop-delivered functional domain assertion also needs actual numeric/boolean readback
(possibly nested with its identities). Missing actual values remain NOT_TESTED;
existing domain assertions still require actual thresholds, controls, source and
actor identity, completed transitions, power/contact overlap and lifecycle.
Trusted adapters can lie: this contract is not an engine oracle or a sandbox.
Registered actions, setters, compile, GAME and images never imply physical input.

Supported desktop delivery probes also return `inputControl` (see
`workflow_routes.input_control`): same request run/case, an explicit `sourceIdentity`
pair (`stock` and `candidate` manifest SHA-256s matching request
`inputControlIdentity`), explicit
stock/candidate spawned/requested/delivered/behavior observations and a physical
stock observation (`null` if unknown). Unknown counts are null, never default zero.

```powershell
python tools/workflow.py diagnose-input --receipt '<saved-input-control.json>' --context '<reviewed-route-context.json>'
```

Missing control, stock zero events, failed stock behavior or incomplete candidate
delivery keep infrastructure NOT_TESTED, censor vehicle attribution and stop the
next case. Supplied failed stock controls censor other input routes too. Qualified
delivery still cannot pass gameplay or human usability. Physical stock success
supports that observation; it neither diagnoses automation nor accepts a candidate.

Missing/malformed identities, either mismatched manifest hash or missing expected
identity keep the control unqualified and infrastructure NOT_TESTED. A standalone
diagnostic without a separate pinned context reports identity UNBOUND; even
perfect delivery counts cannot make it qualified. `observationClassification`
preserves the observed symptom separately from the identity failure.

Keep exact-candidate human acceptance in a separate owner receipt, bound to the
candidate source/build/fixture, acceptance scope and actual human observation.
`physicalStockObserved` is only a stock observation. Automated boolean/readback
fields never qualify reserved assertions `release.human-acceptance`,
`human.acceptance` or `input.physical-acceptance`; reported PASS on those remains
NOT_TESTED in automated results. Other custom human-named assertions still need
owner review; generic adapter trust is not physical acceptance.

## Update lessons when evidence arrives

Immediately retain exact source/run, symptom, route, failed measurements and
changed next action in the addon-owned attempt. Update
[lessons.json](../examples/workflows/lessons.json) with the reusable symptom and
source link in the same change. Cause/recovery stay null until evidenced. For a
verified recovery retain the failure, record the exact changed operation and add
a discriminating regression before promoting a recipe. Route planning surfaces
input lessons automatically. New routes require real entrypoints, evidence
semantics and source/tests; do not build a custom OS injection system as recovery.
