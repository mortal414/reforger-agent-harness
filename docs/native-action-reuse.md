# Reuse existing native actions before desktop input

This is an implementation handoff, not a new native driver or a prerequisite for
the current ASU owner. The staged programmatic-course12 bindings/passive probe
remain owner-controlled, uninstalled and uncompiled at the inspected receipt.
Keep its four source/world files and current session unchanged. Existing qualified
Gepard recipes can continue under their existing coordinator pin; the new routing
contract is adopted only at a future safe boundary.

The persistent QA fixture contains concrete reusable action code in
`GEP_DamageScenario683.c`; its Python bridge already measures traverse, muzzle
ammunition and completed public reentry. Retained October20 evidence supports
that narrow recipe, while the unchanged reverse course failed. This is a source
and retained-receipt assessment, not fresh qualification of ASU.

| ASU course operation | Small supported route to adapt | Required evidence / limit |
| --- | --- | --- |
| Seat/entry P01 | Existing fixture obtains the seat's public get-in action, sets its actual authored context, checks CanBeShown/CanBePerformed, calls OnActionStart/PerformAction and waits for CrewReady. Course12 alternatively maps guarded CompartmentAccessComponent.GetInVehicle with forceTeleport=false and actual door admission. | Observe exact actor/slot occupancy and completed transition. Do not copy the fixture's separate forced initial seating setup into public-entry proof. Physical F reachability and animations remain separate. |
| Engine P02 | Existing action course uses TrackedEngineStart and observes EngineIsOn/RPM. Course12 maps TryStartEngine through normal callbacks. | Source/build-matched fuel/controller callbacks and time-varying RPM; no force-start or power override. |
| Mobility P03 | Prefer existing pre-physics SetActionValue course: TrackedThrottle, TrackedBrake, TrackedHandBrake, TrackedSteeringLeft/Right; actual action values plus motion/power/contact telemetry feed driving_review.py. | Requalify effective ASU track indices, player/driver admission and control semantics. The Gepard reverse failure remains a failure. Direct VehicleTrackedSimulation.SetInputs, if separately qualified, is simulation-command evidence, not registered action or keyboard delivery. Never use transform/velocity/force setters as propulsion proof. |
| Aim P06 | GEP_DamageScenario683.InputQA uses TurretAimRight/TurretAimLeft with neutral release; OperationQA establishes controlled crew, native PlayerCamera, ADS and TurretContext, then measures actual sights direction over time. | This is a concrete registered-action lead for ASU adaptation, not a promised ASU motor fix. Observe real muzzle/animation movement, stops and obstruction response. SetAimingAngles is cinematic and SetBaseRotation/transform setters cannot qualify powered aim. |
| Fire P04 | Existing InputQA uses TurretFire and observes both native muzzle debits. Course12 maps SelectWeapon and SetFireWeaponWanted. | Extend the ASU assertion to actual projectile/trajectory/impact, unique-owner finite ammo debit and cooldown. Wanted flags or counts alone do not satisfy its stronger firing contract. Label component-command separately. |
| Reload P05 | Existing GEP_StationaryAcceptance stages a guarded native TurretReload action after actual weapon/ADS selection and records reload state. This is a source-backed lead only; verify the installed action/context and ASU inventory command path before adapting. | That fixture can skip to direct-feed service and does not establish normal ASU reload timing. Require actual reload-state interval, existing magazine transfer, parent/storage ownership, conserved ammo and interrupted/empty cases. DoReloadWeaponWith is instant and excluded from normal timing proof. |

Do not copy private addon code or stock package bytes into the reusable harness.
Read and minimally adapt the current addon-owned implementation with exact
source/manifest pins. Release only the action values owned by that test on
normal/cancel paths; preserve shared native ownership and the existing cooperative
close protocol. If context/controller readiness fails, stop with NOT_TESTED
instead of installing a forced override or falling back to blind keys.

## Adapter contract for a future adoption

1. Keep the existing request/result/CANCEL protocol and exact run/case/source,
   world, actor, compartment, weapon/magazine identities. Verify full input
   closure and fresh native compile/load before interpreting behavior.
2. Select one bounded operation/case, declare the actual stimulus mechanism and
   reuse the existing passive telemetry. In the new route catalog use
   `native-actions` / `registered-action`, `native-component-commands` /
   `component-command`, or `native-simulation-commands` / `simulation-command`.
   Do not label setters, passive getters or direct simulation controls as
   ordinary player-action delivery.
   When attaching a stock control, pin separate stock/candidate source/build/fixture
   manifests in route context `inputControlSources`. Verify their loaded closure
   and return the exact request `inputControlIdentity` SHA-256 pair as the control's
   `sourceIdentity`; a self-reported build label or a different fixture is rejected.
3. Return ordinary domain assertions with real actual measurements, retained raw
   evidence and separate lifecycle. For the new coordinator also return
   `routeEvidence` with selected route ID/method and actual numeric/boolean
   measurements. Native and desktop-delivered functional PASS assertions need actual readbacks; measurement
   presence is not enough without the assertion's domain threshold. Missing proof remains NOT_TESTED; existing pinned coordinators
   can retain their current result schema until migration.
4. Leave slopes, damage reuse, MP/JIP, performance, LODs and physical acceptance
   untested unless measured. Run the short separate human course at the stable
   candidate. The parent/native owner controls transitions, installation,
   compilation, renderer access and qualification; this source change launches
   none of those operations.
