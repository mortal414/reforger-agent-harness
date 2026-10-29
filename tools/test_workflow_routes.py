"""Route/lesson admission tests. No UI, native engine, GPU, network or security changes."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import workflow as w
import workflow_routes as r


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.proof=self.root/'adapter-review.txt'
        self.proof.write_text('Synthetic scoped capability review, not a native result')
        self.pin={'path':str(self.proof),'sha256':w.sha(self.proof)}
        self.context={'schema':1,'task':'playtest','claim':'measured-behavior','permission':'allowed',
                      'ownership':'clear','previousAttempt':'none'}
        self.context['inputControlSources']={}
        for name in ('stock','candidate'):
            manifest=self.root/(name+'-source.json');manifest.write_text(json.dumps({'fixture':name}))
            self.context['inputControlSources'][name]={'path':str(manifest),'sha256':w.sha(manifest)}

    def assess(self,route,state):
        self.context.setdefault('assessments',{})[route]={'state':state,
            'reason':'Synthetic current-candidate capability assessment','evidence':[self.pin]}

    def test_concrete_catalog_sources_and_commands_are_present(self):
        rows=r.catalog()
        self.assertGreaterEqual(len(rows),12)
        for row in rows:
            with self.subTest(route=row['id']):
                self.assertTrue(all((r.ROOT/source).is_file() for source in row['sources']))
                self.assertTrue(row['commands']);self.assertTrue(row['doesNotProve'])
        self.assertEqual(len(r.lessons('injected-input-zero-events')),2)

    def test_available_programmatic_route_precedes_desktop(self):
        self.assess('native-actions','available')
        out=r.preflight(self.context)
        self.assertEqual(out['admission'],'READY')
        self.assertEqual(out['selected']['id'],'native-actions')
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertIn('PENDING',out['humanAcceptance'])

    def test_explicit_desktop_cannot_override_available_programmatic_route(self):
        self.assess('native-actions','validated')
        self.context.update(route='desktop-input-probe',desktopReason='Convenient')
        out=r.preflight(self.context)
        self.assertEqual(out['admission'],'HOLD')
        self.assertIn('PROGRAMMATIC_ROUTE_AVAILABLE',out['reason'])

    def test_unknown_programmatic_capability_is_research_hold_not_desktop_fallback(self):
        out=r.preflight(self.context)
        self.assertEqual(out['admission'],'HOLD')
        self.assertIn('PROGRAMMATIC_ROUTE_UNVERIFIED',out['reason'])
        self.assertIn('registered',next(x for x in out['candidates'] if x['id']=='native-actions')['method'])

    def test_desktop_requires_evidenced_unsupported_alternative_and_reason(self):
        for route in ('native-actions','native-component-commands','native-simulation-commands'):
            self.assess(route,'unsupported')
        self.assertIn('DESKTOP_REASON_REQUIRED',r.preflight(self.context)['reason'])
        self.context['desktopReason']='Residual ordinary supported desktop delivery probe; action API unavailable in scoped fixture, see pinned review'
        out=r.preflight(self.context)
        self.assertEqual(out['admission'],'READY')
        self.assertEqual(out['selected']['id'],'desktop-input-probe')
        self.assertEqual(out['desktopReason'],self.context['desktopReason'])

    def test_desktop_probe_requires_explicit_pinned_source_pair(self):
        for route in ('native-actions','native-component-commands','native-simulation-commands'):
            self.assess(route,'unsupported')
        self.context.update(desktopReason='Residual delivery question with known owner')
        self.context.pop('inputControlSources')
        self.assertIn('INPUT_CONTROL_IDENTITY_REQUIRED',r.preflight(self.context)['reason'])

    def test_native_import_unknown_does_not_default_to_editor(self):
        self.context.update(task='import',claim='native-import')
        self.assertIn('PROGRAMMATIC_ROUTE_UNVERIFIED',r.preflight(self.context)['reason'])
        self.context.update(claim='import-plan')
        self.assertEqual(r.preflight(self.context)['selected']['id'],'import-file-plan')

    def test_permission_denial_blocks_every_alternative(self):
        self.assess('native-actions','available')
        for state in ('denied','unknown'):
            self.context['permission']=state
            out=r.preflight(self.context)
            self.assertEqual(out['admission'],'HOLD');self.assertIsNone(out['selected'])
            self.assertIn('no alternative route bypass',out['reason'])

    def test_pending_unknown_outcome_and_denied_attempt_never_retry(self):
        self.assess('native-actions','available')
        for state in ('pending','uncertain','denied'):
            self.context['previousAttempt']=state
            self.assertEqual(r.preflight(self.context)['admission'],'HOLD')

    def test_unknown_or_occupied_owner_blocks_native_but_allows_independent_offline_plan(self):
        self.assess('native-actions','available')
        for owner in ('unknown','occupied'):
            self.context['ownership']=owner
            self.assertEqual(r.preflight(self.context)['admission'],'HOLD')
        self.context.update(task='create',claim='job-created')
        self.assertEqual(r.preflight(self.context)['selected']['id'],'job-file-plan')

    def test_setter_and_registered_actions_cannot_claim_physical_usability(self):
        self.assess('native-actions','available');self.assess('native-state-setup','available')
        for route in ('native-actions','native-state-setup'):
            self.context.update(claim='human-usability',route=route)
            self.assertIn('CLAIM_UNSUPPORTED',r.preflight(self.context)['reason'])

    def test_human_gate_is_small_separate_and_never_autoexecuted(self):
        self.context.update(task='human-acceptance',claim='human-usability',desktopReason='Physical controls and discovery require a human report')
        out=r.preflight(self.context)
        self.assertEqual(out['admission'],'HUMAN_REQUIRED')
        self.assertEqual(out['status'],'NOT_TESTED')

    def test_assessment_without_evidence_or_changed_evidence_cannot_promote_route(self):
        self.assess('native-actions','available')
        self.proof.write_text('Changed review')
        with self.assertRaisesRegex(w.WorkflowError,'evidence changed'):r.preflight(self.context)
        self.context['assessments']['native-actions']['evidence']=[]
        with self.assertRaisesRegex(w.WorkflowError,'Pinned assessment evidence'):r.preflight(self.context)

    def test_unknown_fields_route_ids_and_states_fail_closed(self):
        for change in ({'permission':'maybe'},{'route':'invented'},{'ownership':None},{'command':'anything'},
                       {'assessments':{'invented':{}}},{'previousAttempt':'apparently-done'}):
            with self.subTest(change=change):
                value=copy.deepcopy(self.context);value.update(change)
                with self.assertRaises(w.WorkflowError):r.preflight(value)

    def test_component_and_simulation_commands_keep_their_distinct_evidence_method(self):
        for route,method in [('native-component-commands','component-command'),('native-simulation-commands','simulation-command')]:
            self.assess(route,'available');self.context['route']=route
            out=r.preflight(self.context)
            self.assertEqual(out['admission'],'READY');self.assertEqual(out['selected']['method'],method)

    def test_missing_catalog_source_cannot_be_promoted_by_assessment(self):
        rows=r.catalog();next(x for x in rows if x['id']=='native-actions')['sources']=['absent.c']
        self.assess('native-actions','validated')
        with patch.object(r,'catalog',return_value=rows):out=r.preflight(self.context)
        self.assertEqual(out['admission'],'HOLD')

    def test_cli_discovery_and_denied_context_never_spawn(self):
        context=self.root/'route.json';self.context['permission']='denied';context.write_text(json.dumps(self.context))
        with patch('workflow.subprocess.Popen',side_effect=AssertionError('spawn')),contextlib.redirect_stdout(io.StringIO()) as stdout:
            code=w.main(['routes','--context',str(context)])
        self.assertEqual(code,2);self.assertEqual(json.loads(stdout.getvalue())['admission'],'HOLD')

    def test_input_history_does_not_invent_a_fix(self):
        for row in r.lessons('injected-input-zero-events'):
            self.assertIsNone(row['cause']);self.assertIsNone(row['recovery'])
        self.assertIn('DestroyLoadingPlaceholder',r.lessons('loading-pattern-image')[0]['recovery'])


class InputControlTests(unittest.TestCase):
    IDENTITY={'stock':'a'*64,'candidate':'b'*64}

    def receipt(self):
        return {'schema':1,'runId':'run','caseId':'case','sourceIdentity':dict(self.IDENTITY),
                'stock':{'spawned':True,'requestedEvents':4,'deliveredEvents':0,'behaviorObserved':False},
                'candidate':{'spawned':True,'requestedEvents':4,'deliveredEvents':0,'behaviorObserved':False},
                'physicalStockObserved':True}

    def test_stock_and_candidate_zero_events_are_not_a_vehicle_failure(self):
        out=r.input_control(self.receipt(),'run','case',self.IDENTITY)
        self.assertEqual(out['classification'],'INPUT_DELIVERY_OR_FIXTURE_UNQUALIFIED')
        self.assertEqual(out['status'],'NOT_TESTED');self.assertFalse(out['vehicleDefectEstablished'])
        self.assertIsNone(out['cause']);self.assertIsNone(out['recovery'])

    def test_missing_measurements_are_unknown_not_zero_or_pass(self):
        value=self.receipt();value['stock']['deliveredEvents']=None
        self.assertEqual(r.input_control(value,expected_identity=self.IDENTITY)['classification'],'STOCK_CONTROL_NOT_TESTED')
        del value['stock']['deliveredEvents']
        with self.assertRaises(w.WorkflowError):r.input_control(value)

    def test_stock_delivered_but_no_behavior_is_control_failure(self):
        value=self.receipt();value['stock']['deliveredEvents']=4
        self.assertEqual(r.input_control(value,expected_identity=self.IDENTITY)['classification'],'STOCK_CONTROL_FAILED')

    def test_stock_pass_does_not_make_undelivered_candidate_a_vehicle_defect(self):
        value=self.receipt();value['stock'].update(deliveredEvents=4,behaviorObserved=True)
        self.assertEqual(r.input_control(value,expected_identity=self.IDENTITY)['classification'],'CANDIDATE_INPUT_PATH_UNQUALIFIED')

    def test_delivery_qualified_is_never_a_gameplay_or_human_pass(self):
        value=self.receipt()
        for key in ('stock','candidate'):value[key].update(deliveredEvents=4,behaviorObserved=True)
        out=r.input_control(value,expected_identity=self.IDENTITY)
        self.assertTrue(out['controlQualified']);self.assertEqual(out['status'],'NOT_TESTED')

    def test_stale_control_wrong_case_and_invalid_counts_rejected(self):
        with self.assertRaisesRegex(w.WorkflowError,'Stale'):r.input_control(self.receipt(),'other','case')
        with self.assertRaisesRegex(w.WorkflowError,'Wrong'):r.input_control(self.receipt(),'run','other')
        for count in (True,-1,5):
            value=self.receipt();value['stock']['deliveredEvents']=count
            with self.assertRaises(w.WorkflowError):r.input_control(value)

    def test_diagnostic_cli_preserves_receipt_identity_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'control.json';path.write_text(json.dumps(self.receipt()))
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(w.main(['diagnose-input','--receipt',str(path)]),0)
            out=json.loads(stdout.getvalue())
            self.assertEqual(out['runId'],'run');self.assertEqual(out['caseId'],'case')
            self.assertEqual(out['sourceIdentity'],self.IDENTITY)
            self.assertFalse(out['controlQualified']);self.assertEqual(out['classification'],'SOURCE_IDENTITY_UNBOUND')
            self.assertEqual(out['pins'][0]['sha256'],w.sha(path))

    def test_correct_counts_never_qualify_missing_unbound_or_mismatched_identity(self):
        for case in ('missing','label','missing-stock','wrong-stock','wrong-candidate','unbound'):
            value=self.receipt()
            for name in ('stock','candidate'):value[name].update(deliveredEvents=4,behaviorObserved=True)
            expected=self.IDENTITY
            if case=='missing':value.pop('sourceIdentity')
            if case=='label':value['sourceIdentity']='unrelated-or-stale-build-identity'
            if case=='missing-stock':value['sourceIdentity'].pop('stock')
            if case=='wrong-stock':value['sourceIdentity']['stock']='c'*64
            if case=='wrong-candidate':value['sourceIdentity']['candidate']='c'*64
            if case=='unbound':expected=None
            with self.subTest(case=case):
                out=r.input_control(value,'run','case',expected)
                self.assertFalse(out['controlQualified']);self.assertFalse(out['sourceIdentityMatched'])
                self.assertEqual(out['status'],'NOT_TESTED')

    def test_diagnostic_can_bind_against_separate_pinned_context(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sources={}
            for name in ('stock','candidate'):
                manifest=root/(name+'.json');manifest.write_text(json.dumps({'fixture':name}))
                sources[name]={'path':manifest.name,'sha256':w.sha(manifest)}
            context=root/'context.json';context.write_text(json.dumps({'inputControlSources':sources}))
            value=self.receipt();value['sourceIdentity']={name:pin['sha256'] for name,pin in sources.items()}
            for name in ('stock','candidate'):value[name].update(deliveredEvents=4,behaviorObserved=True)
            receipt=root/'receipt.json';receipt.write_text(json.dumps(value))
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(w.main(['diagnose-input','--receipt',str(receipt),'--context',str(context)]),0)
            out=json.loads(stdout.getvalue())
            self.assertTrue(out['controlQualified']);self.assertTrue(out['sourceIdentityMatched'])
            self.assertEqual(out['status'],'NOT_TESTED')
            self.assertEqual(len(out['pins']),4)


class CrossRouteEvidenceTests(unittest.TestCase):
    """Independent-review P1/P2 reproductions with the other guard satisfied."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'native.log').write_text('Synthetic evidence, no game process')
        self.identity={'stock':'a'*64,'candidate':'b'*64}
        self.required=['drive.powered','drive.signed-progress','route.evidence']

    def normalize(self,mode,actuals,identity='matched',human=False):
        route={'id':'desktop-input-probe' if mode=='desktop' else 'native-actions',
               'mode':mode,'method':'desktop-injected' if mode=='desktop' else 'registered-action'}
        if mode=='pack':
            route={'id':'workbench-pack','mode':'native','method':'native-package'}
        required=self.required+(['release.human-acceptance'] if human else [])
        request={'runId':'run','caseId':'case','attemptDir':str(self.root),'assertions':required,
                 'route':route,'claim':'measured-behavior','inputControlIdentity':dict(self.identity)}
        control={'schema':1,'runId':'run','caseId':'case','sourceIdentity':dict(self.identity),
                 'stock':{'spawned':True,'requestedEvents':4,'deliveredEvents':4,'behaviorObserved':True},
                 'candidate':{'spawned':True,'requestedEvents':4,'deliveredEvents':4,'behaviorObserved':True},'physicalStockObserved':True}
        if identity=='mismatched':control['sourceIdentity']['candidate']='c'*64
        if identity=='missing':control.pop('sourceIdentity')
        if identity=='unbound':request.pop('inputControlIdentity')
        result={'schema':1,'runId':'run','caseId':'case',
                'infrastructure':{'status':'PASS','reason':'Synthetic transport'},
                'assertions':{name:{'status':'PASS','reason':'Synthetic claimed result',**actuals} for name in required},
                'lifecycle':{'status':'PASS','reason':'No native owner','verifiedExited':True,'leaseReleased':True},
                'evidence':['native.log'],'inputControl':control,
                'routeEvidence':{'routeId':route['id'],'method':route['method'],'measurements':{'deliveredEvents':4}}}
        return w.validate_result(result,request),required

    def test_desktop_and_native_label_only_behavior_never_pass_with_qualified_control(self):
        for mode in ('desktop','native'):
            for actuals in ({},{'actual':None},{'actual':'delivered four events'},{'actual':{'label':'moved'}}):
                with self.subTest(mode=mode,actuals=actuals):
                    result,required=self.normalize(mode,actuals)
                    self.assertEqual(result['infrastructure']['status'],'PASS')
                    self.assertTrue(result['inputAssessment']['controlQualified'])
                    self.assertEqual(w.verdict(result,required),'NOT_TESTED')
                    for name in ('drive.powered','drive.signed-progress'):
                        self.assertEqual(result['assertions'][name]['status'],'NOT_TESTED')

    def test_measured_behavior_and_correct_control_pair_can_pass_on_both_routes(self):
        for mode in ('desktop','native'):
            result,required=self.normalize(mode,{'actual':{'syntheticMeasuredValue':2.5}})
            self.assertEqual(w.verdict(result,required),'PASS')
            self.assertTrue(result['inputAssessment']['sourceIdentityMatched'])

    def test_same_run_wrong_or_missing_build_identity_censors_measured_results(self):
        for mode in ('desktop','native'):
            for identity in ('mismatched','missing','unbound'):
                with self.subTest(mode=mode,identity=identity):
                    result,required=self.normalize(mode,{'actual':2.5},identity)
                    self.assertEqual(result['infrastructure']['status'],'NOT_TESTED')
                    self.assertEqual(w.verdict(result,required),'NOT_TESTED')
                    self.assertFalse(result['inputAssessment']['controlQualified'])

    def test_human_acceptance_stays_separate_even_with_actual_true(self):
        for mode in ('native','desktop','pack'):
            result,required=self.normalize(mode,{'actual':True},human=True)
            self.assertEqual(result['assertions']['release.human-acceptance']['status'],'NOT_TESTED')
            self.assertEqual(w.verdict(result,required),'NOT_TESTED')


if __name__=='__main__':unittest.main()
