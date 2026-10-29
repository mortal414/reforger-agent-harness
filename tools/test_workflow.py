from pathlib import Path
import contextlib
import io
import json
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import workflow as w

ADAPTER = '''import json,sys,time
from pathlib import Path
request,result,cancel=map(Path,sys.argv[1:])
r=json.loads(request.read_text()); mode=r['parameters'].get('mode','pass')
if mode=='wait':
 while not cancel.exists(): time.sleep(.02)
if mode=='late': time.sleep(3)
if mode=='noisy': print('x'*4096,flush=True)
e=result.parent/'native.log';e.write_text('Synthetic coordinator fixture; not engine evidence')
out={'schema':1,'runId':r['runId'],'caseId':r['caseId'],
 'infrastructure':{'status':'PASS','reason':'synthetic fixture'},
 'assertions':{k:{'status':'PASS','reason':'synthetic fixture','actual':{'syntheticObserved':True}} for k in r['assertions']},
 'lifecycle':{'status':'PASS','reason':'synthetic closure','verifiedExited':True,'leaseReleased':True},
 'evidence':[str(e)]}
out['routeEvidence']={'routeId':r['route']['id'],'method':r['route']['method'],'measurements':{'syntheticObserved':True}}
if mode=='no-route-measurement': del out['routeEvidence']
if mode=='setter-proof': out['routeEvidence']['method']='state-setter'
if mode=='empty-measurements': out['routeEvidence']['measurements']={}
if mode=='missing-domain-measurement': del out['assertions']['world.loaded']['actual']
if mode in ('stock-zero','wrong-stock-source','wrong-candidate-source','missing-control-source','matched-control-source'):
 out['inputControl']={'schema':1,'runId':r['runId'],'caseId':r['caseId'],'sourceIdentity':r.get('inputControlIdentity') or {'stock':'a'*64,'candidate':'b'*64},
 'stock':{'spawned':True,'requestedEvents':4,'deliveredEvents':4,'behaviorObserved':True},
 'candidate':{'spawned':True,'requestedEvents':4,'deliveredEvents':4,'behaviorObserved':True},'physicalStockObserved':True}
 if mode=='stock-zero':
  for key in ('stock','candidate'):out['inputControl'][key].update(deliveredEvents=0,behaviorObserved=False)
 if mode=='wrong-stock-source':out['inputControl']['sourceIdentity']['stock']='0'*64
 if mode=='wrong-candidate-source':out['inputControl']['sourceIdentity']['candidate']='0'*64
 if mode=='missing-control-source':del out['inputControl']['sourceIdentity']
if mode=='fail': out['assertions']['fixture.ready']['status']='FAIL'
if mode=='infra': out['infrastructure']['status']='NOT_TESTED'
if mode=='stale': out['runId']='prior-run'
if mode=='missing': del out['assertions']['world.loaded']
if mode=='lease': out['lifecycle']['leaseReleased']=False
if mode=='malformed': out['assertions']['fixture.ready']['reason']=''
if mode=='status-list': out['infrastructure']['status']=[]
if mode=='status-map': out['lifecycle']['status']={}
if mode=='checks-list': out['assertions']=[]
if mode=='check-list': out['assertions']['fixture.ready']=[]
if mode=='overflow': out['assertions']['fixture.ready']['actual']='OVERFLOW'
result.write_text(json.dumps(out).replace('"OVERFLOW"','1e309'))
'''


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'scripts').mkdir()
        (self.root/'scripts/probe.c').write_text('class ProbeClass : GenericEntity {}')
        (self.root/'Scene.ent').write_text('ProbeClass {}')
        (self.root/'addon.gproj').write_text('GameProject { GUID "0123456789ABCDEF" }')
        (self.root/'adapter.py').write_text(ADAPTER)
        self.job = {'schema':1,'template':'startup','project':'addon.gproj','world':'Scene.ent',
                    'sourceRoots':['.'],'addonRoots':['.'],'requiredFiles':[{'path':'Scene.ent'}],'requiredClasses':['ProbeClass'],
                    'capabilities':['isolated-reset','owned-lifecycle','native-load'],
                    'adapter':{'executable':sys.executable,'script':'adapter.py','args':['{script}','{request}','{result}','{cancel}']},
                    'cases':[self.case('first'),self.case('second')], 'timeoutSeconds':3,'closeGraceSeconds':2,
                    'routeContext':'route.json'}
        self.route={'schema':1,'task':'validate','claim':'native-load','permission':'allowed',
                    'ownership':'clear','previousAttempt':'none'}
        sources={}
        for name in ('stock','candidate'):
            manifest=self.root/(name+'-source.json');manifest.write_text(json.dumps({'syntheticFixture':name}))
            sources[name]={'path':manifest.name,'sha256':w.sha(manifest)}
        self.route['inputControlSources']=sources
        self.write_route()
        self.path = self.root/'job.json'
        self.write_job()

    def case(self, name, mode='pass'):
        return {'id':name,'parameters':{'mode':mode},'assertions':['fixture.ready','world.loaded']}

    def write_job(self):
        self.path.write_text(json.dumps(self.job))

    def write_route(self):
        (self.root/'route.json').write_text(json.dumps(self.route))

    def run_job(self):
        return w.run(self.path,self.root/'batch',execute=True)

    def test_dry_plan_checks_inputs_without_outputs_or_spawn(self):
        with patch('workflow.subprocess.Popen',side_effect=AssertionError('spawn')):
            out=w.run(self.path,self.root/'batch')
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertFalse((self.root/'batch').exists())
        self.assertEqual(out['classDefinitions']['ProbeClass'],[str((self.root/'scripts/probe.c').resolve())])

    def test_missing_spawn_class_stops_before_launch(self):
        (self.root/'scripts/probe.c').write_text('// class ProbeClass {}')
        with self.assertRaisesRegex(w.WorkflowError,'class missing'):
            self.run_job()
        self.assertFalse((self.root/'batch').exists())

    def test_missing_world_or_wrong_pin(self):
        self.job['world']='Absent.ent';self.write_job()
        with self.assertRaisesRegex(w.WorkflowError,'World not found'):w.plan(self.path)
        self.job['world']='Scene.ent';self.job['requiredFiles'][0]['sha256']='0'*64;self.write_job()
        with self.assertRaisesRegex(w.WorkflowError,'Pinned file differs'):w.plan(self.path)

    def test_missing_capability_and_mandatory_assertion(self):
        self.job['capabilities'].remove('native-load');self.write_job()
        with self.assertRaisesRegex(w.WorkflowError,'capabilities'):w.plan(self.path)
        self.job['capabilities'].append('native-load');self.job['cases'][0]['assertions']=['fixture.ready'];self.write_job()
        with self.assertRaisesRegex(w.WorkflowError,'mandatory'):w.plan(self.path)

    def test_measured_failure_preserved_and_next_case_runs(self):
        self.job['cases'][0]=self.case('first','fail');self.write_job()
        out=self.run_job()
        self.assertEqual(out['status'],'FAIL')
        self.assertEqual([r['status'] for r in out['cases']],['FAIL','PASS'])
        self.assertTrue((self.root/'batch/index.md').is_file())

    def test_infrastructure_stops_next_case(self):
        self.job['cases'][0]=self.case('first','infra');self.write_job()
        out=self.run_job()
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertEqual(out['notStarted'],['second'])

    def test_stale_result_never_passes(self):
        self.job['cases'][0]=self.case('first','stale');self.write_job()
        out=self.run_job()
        self.assertEqual(out['cases'][0]['status'],'NOT_TESTED')
        self.assertIn('identity',out['cases'][0]['infrastructure']['reason'])

    def test_missing_assertion_is_not_tested(self):
        self.job['cases'][0]=self.case('first','missing');self.write_job()
        out=self.run_job()
        self.assertEqual(out['cases'][0]['status'],'NOT_TESTED')
        self.assertEqual(len(out['cases']),2)

    def test_lifecycle_blocks_next_case_even_after_behavior_pass(self):
        self.job['cases'][0]=self.case('first','lease');self.write_job()
        out=self.run_job()
        self.assertEqual(out['cases'][0]['status'],'PASS')
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertEqual(out['notStarted'],['second'])

    def test_reason_required(self):
        self.job['cases'][0]=self.case('first','malformed');self.write_job()
        self.assertEqual(self.run_job()['status'],'NOT_TESTED')

    def test_cooperative_cancel_preserves_closure_but_censors_behavior(self):
        self.job['cases'][0]=self.case('first','wait');self.write_job()
        stop=self.root/'STOP'
        timer=threading.Timer(.3,lambda:stop.write_text('human stop'))
        timer.start();self.addCleanup(timer.join)
        out=w.run(self.path,self.root/'batch',True,stop)
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertEqual(out['notStarted'],['second'])
        self.assertTrue(out['cases'][0]['lifecycle']['leaseReleased'])
        self.assertTrue((self.root/'batch/first/CANCEL').exists())

    def test_deadline_requests_cooperative_close(self):
        self.job['cases']=[self.case('first','wait')];self.job['timeoutSeconds']=1;self.write_job()
        out=self.run_job()
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertEqual(out['stopReason'],'deadline')

    def test_unresponsive_adapter_is_preserved_and_reported(self):
        self.job['cases'][0]=self.case('first','late');self.job['timeoutSeconds']=1;self.job['closeGraceSeconds']=1;self.write_job()
        out=self.run_job()
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertIn('adapter still alive',out['stopReason'])
        self.assertEqual(out['notStarted'],['second'])
        self.assertTrue((self.root/'batch/first/adapter-owner.json').exists())
        # Synthetic child exits itself. The coordinator never kills it.
        time.sleep(1.4)

    def test_rerun_never_overwrites_and_fresh_rerun_is_allowed(self):
        self.assertEqual(self.run_job()['status'],'PASS')
        before=w.sha(self.root/'batch/summary.json')
        with self.assertRaisesRegex(w.WorkflowError,'Fresh batch'):self.run_job()
        self.assertEqual(w.sha(self.root/'batch/summary.json'),before)
        out=w.run(self.path,self.root/'fresh',True,only=['second'])
        self.assertEqual(len(out['cases']),1)

    def test_pin_change_stops_before_next_case(self):
        self.job['requiredFiles']=[];self.write_job()
        planned=w.plan(self.path)
        (self.root/'Scene.ent').write_text('changed')
        with self.assertRaisesRegex(w.WorkflowError,'Input changed'):w.verify_pins(planned)

    def test_ambiguous_world_rejected_before_launch(self):
        other=self.root/'other';other.mkdir();(other/'Scene.ent').write_text('other world')
        self.job['sourceRoots'].append('other');self.write_job()
        with self.assertRaisesRegex(w.WorkflowError,'Ambiguous world'):w.plan(self.path)

    def test_malformed_types_leave_attempt_evidence_and_stop(self):
        for mode in ('status-list','status-map','checks-list','check-list','overflow'):
            with self.subTest(mode=mode):
                self.job['cases'][0]=self.case('first',mode);self.write_job()
                output=self.root/mode
                out=w.run(self.path,output,True)
                self.assertEqual(out['status'],'NOT_TESTED')
                self.assertEqual(out['attempted'],['first'])
                self.assertEqual(out['notStarted'],['second'])
                self.assertEqual(out['incomplete'],[])
                self.assertTrue(out['stopReason'])
                result=json.loads((output/'first/result.json').read_text())
                self.assertEqual(result['infrastructure']['status'],'NOT_TESTED')
                self.assertFalse(result['lifecycle']['verifiedExited'])
                self.assertFalse(result['lifecycle']['leaseReleased'])
                self.assertTrue((output/'first/adapter-result.json').exists())

    def test_unexpected_protocol_error_preserves_attempt(self):
        with patch('workflow.validate_result',side_effect=TypeError('unexpected protocol error')):
            out=self.run_job()
        self.assertEqual(out['attempted'],['first'])
        self.assertEqual(out['notStarted'],['second'])
        self.assertIn('TypeError',out['cases'][0]['infrastructure']['reason'])

    def test_invalid_template_container_rejected(self):
        self.job['template']=[];self.write_job()
        with self.assertRaisesRegex(w.WorkflowError,'Unknown template'):w.plan(self.path)

    def registry(self):
        folder=self.root/'local';folder.mkdir(exist_ok=True)
        path=folder/'bindings.json'
        path.write_text(json.dumps({'schema':1,'bindings':{'qualified-fixture':{'job':'../job.json','description':'Synthetic qualified CLI integration fixture; not engine evidence','outputRoot':'../evidence'}}}))
        return path

    def test_binding_paths_resolve_from_registry_and_plan_never_launches(self):
        registry=self.registry()
        self.assertEqual(w.bindings(registry)['bindings']['qualified-fixture']['job'],str(self.path))
        with patch('workflow.subprocess.Popen',side_effect=AssertionError('launch')),contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(w.main(['plan','--binding','qualified-fixture','--registry',str(registry)]),0)
        self.assertEqual(json.loads(stream.getvalue())['job'],str(self.path))
        self.assertFalse((self.root/'evidence').exists())

    def test_binding_runs_real_adapter_with_fresh_output_and_case_selection(self):
        registry=self.registry()
        for _ in range(2):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(w.main(['run','--binding','qualified-fixture','--registry',str(registry),'--case','second','--execute']),0)
        outputs=list((self.root/'evidence/qualified-fixture').iterdir())
        self.assertEqual(len(outputs),2)
        for output in outputs:
            summary=json.loads((output/'summary.json').read_text())
            self.assertEqual(summary['output'],str(output))
            self.assertEqual([row['id'] for row in summary['cases']],['second'])
            self.assertTrue((output/'second/adapter-result.json').exists())

    def test_unknown_binding_or_missing_registry_cannot_create_evidence(self):
        registry=self.registry()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(w.main(['run','--binding','absent','--registry',str(registry),'--execute']),2)
        self.assertFalse((self.root/'evidence').exists())
        with self.assertRaisesRegex(w.WorkflowError,'registry absent'):w.bindings(self.root/'absent.json')

    def test_binding_registry_rejects_malformed_or_command_fields(self):
        registry=self.registry();valid=json.loads(registry.read_text())
        for mutate in (lambda j:j.update(schema=True),lambda j:j.update(bindings=[]),lambda j:j['bindings']['qualified-fixture'].update(outputRoot=False),lambda j:j['bindings']['qualified-fixture'].update(command='run anything')):
            data=json.loads(json.dumps(valid));mutate(data);registry.write_text(json.dumps(data))
            with self.assertRaises(w.WorkflowError):w.bindings(registry)

    def test_direct_job_still_requires_explicit_output(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(w.main(['run','--job',str(self.path),'--execute']),2)
        self.assertFalse((self.root/'batch').exists())

    def test_world_cannot_escape_declared_source_roots(self):
        for world in (str(self.root/'Scene.ent'),'{0123456789ABCDEF}../Scene.ent','../Scene.ent','/Scene.ent'):
            with self.subTest(world=world):
                self.job['world']=world;self.write_job()
                with self.assertRaises(w.WorkflowError):w.plan(self.path)

    def test_duplicate_json_and_nonfinite_values_rejected(self):
        self.path.write_text('{"schema":1,"schema":1}')
        with self.assertRaisesRegex(w.WorkflowError,'Duplicate'):w.read_json(self.path)
        self.path.write_text('{"number":NaN}')
        with self.assertRaisesRegex(w.WorkflowError,'Nonfinite'):w.read_json(self.path)
        self.path.write_text('{"number":1e309}')
        with self.assertRaisesRegex(w.WorkflowError,'Nonfinite'):w.read_json(self.path)

    def test_low_space_refuses_before_writes_or_launch(self):
        with patch('workflow.shutil.disk_usage',return_value=type('Usage',(),{'free':0})()):
            with self.assertRaisesRegex(w.WorkflowError,'2 GiB'):self.run_job()
        self.assertFalse((self.root/'batch').exists())

    def test_noisy_adapter_censors_and_stops_batch(self):
        self.job['cases'][0]=self.case('first','noisy');self.write_job()
        with patch('workflow.MAX_ADAPTER_LOG_BYTES',64):out=self.run_job()
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertIn('adapter-log-limit',out['stopReason'])
        self.assertEqual(out['notStarted'],['second'])

    def test_missing_base_dependency_and_duplicate_guid(self):
        project=self.root/'addon.gproj'
        project.write_text('GameProject { GUID "0123456789ABCDEF" Dependencies { "AAAAAAAAAAAAAAAA" } }')
        with self.assertRaisesRegex(w.WorkflowError,'Missing mounted dependency'):w.plan(self.path)
        (self.root/'base').mkdir()
        (self.root/'base/base.gproj').write_text('GameProject { GUID "AAAAAAAAAAAAAAAA" }')
        self.assertEqual(len(w.plan(self.path)['dependencies']),2)
        (self.root/'base/duplicate.gproj').write_text('GameProject { GUID "AAAAAAAAAAAAAAAA" }')
        with self.assertRaisesRegex(w.WorkflowError,'Duplicate mounted'):w.plan(self.path)

    def test_legacy_job_plans_but_execute_requires_reviewed_route_context(self):
        self.job.pop('routeContext');self.write_job()
        self.assertEqual(w.plan(self.path)['routePreflight']['admission'],'HOLD')
        with patch('workflow.subprocess.Popen',side_effect=AssertionError('launch')):
            with self.assertRaisesRegex(w.WorkflowError,'ROUTE_ADMISSION_HOLD'):self.run_job()
        self.assertFalse((self.root/'batch').exists())

    def test_denied_unknown_and_pending_route_stop_before_output_or_spawn(self):
        for field,value in [('permission','denied'),('permission','unknown'),('ownership','unknown'),
                            ('ownership','occupied'),('previousAttempt','pending'),('previousAttempt','uncertain'),('previousAttempt','denied')]:
            with self.subTest(field=field,value=value):
                original=self.route[field];self.route[field]=value;self.write_route()
                with patch('workflow.subprocess.Popen',side_effect=AssertionError('launch')):
                    with self.assertRaisesRegex(w.WorkflowError,'ROUTE_ADMISSION_HOLD'):self.run_job()
                self.assertFalse((self.root/'batch').exists())
                self.route[field]=original

    def test_route_context_and_catalog_are_pinned(self):
        planned=w.plan(self.path)
        self.route['ownership']='occupied';self.write_route()
        with self.assertRaisesRegex(w.WorkflowError,'Input changed'):w.verify_pins(planned)
        self.assertIn('routes.json',{Path(p['path']).name for p in planned['pins']})
        self.assertIn('lessons.json',{Path(p['path']).name for p in planned['pins']})

    def test_route_claim_cannot_replace_template_domain(self):
        self.route.update(task='create',claim='job-created');self.write_route()
        with self.assertRaisesRegex(w.WorkflowError,'JOB_ROUTE_CLAIM_MISMATCH'):self.run_job()

    def test_all_adapter_passes_without_route_measurements_remain_not_tested(self):
        self.job['cases']=[self.case('first','no-route-measurement')];self.write_job()
        out=self.run_job()
        self.assertEqual(out['status'],'NOT_TESTED')
        result=w.read_json(self.root/'batch/first/result.json')
        self.assertEqual(result['assertions']['world.loaded']['status'],'PASS')
        self.assertEqual(result['assertions']['route.evidence']['status'],'NOT_TESTED')

    def test_setter_proof_or_empty_measurements_cannot_pass_native_load(self):
        for mode in ('setter-proof','empty-measurements'):
            self.job['cases']=[self.case('first',mode)];self.write_job()
            out=w.run(self.path,self.root/mode,True)
            self.assertEqual(out['status'],'NOT_TESTED')
            self.assertEqual(out['cases'][0]['infrastructure']['status'],'NOT_TESTED')

    def test_route_provenance_alone_cannot_pass_unmeasured_native_assertion(self):
        self.job['cases']=[self.case('first','missing-domain-measurement')];self.write_job()
        out=self.run_job()
        self.assertEqual(out['status'],'NOT_TESTED')
        result=w.read_json(self.root/'batch/first/result.json')
        self.assertEqual(result['assertions']['route.evidence']['status'],'PASS')
        self.assertEqual(result['assertions']['world.loaded']['status'],'NOT_TESTED')

    def test_existing_startup_healthy_recipe_can_choose_measured_action_route(self):
        self.route.update(task='playtest',claim='measured-behavior',assessments={'native-actions':{
            'state':'available','reason':'Synthetic action adapter code presence only',
            'evidence':[{'path':'adapter.py','sha256':w.sha(self.root/'adapter.py')}]}})
        self.write_route()
        planned=w.plan(self.path)
        self.assertEqual(planned['routePreflight']['admission'],'READY')
        self.assertEqual(planned['routePreflight']['selected']['id'],'native-actions')

    def test_stock_zero_events_censor_vehicle_failure_and_stop_next_case(self):
        self.job['cases'][0]=self.case('first','stock-zero');self.write_job()
        out=self.run_job()
        self.assertEqual(out['status'],'NOT_TESTED')
        self.assertEqual(out['notStarted'],['second'])
        result=w.read_json(self.root/'batch/first/result.json')
        self.assertEqual(result['inputAssessment']['classification'],'INPUT_DELIVERY_OR_FIXTURE_UNQUALIFIED')
        self.assertFalse(result['inputAssessment']['vehicleDefectEstablished'])

    def test_same_run_wrong_or_missing_source_control_stops_before_next_case(self):
        for mode,classification in [('wrong-stock-source','SOURCE_IDENTITY_MISMATCH'),
                                    ('wrong-candidate-source','SOURCE_IDENTITY_MISMATCH'),
                                    ('missing-control-source','SOURCE_IDENTITY_MISSING')]:
            with self.subTest(mode=mode):
                self.job['cases'][0]=self.case('first',mode);self.write_job()
                out=w.run(self.path,self.root/mode,True)
                self.assertEqual(out['status'],'NOT_TESTED');self.assertEqual(out['notStarted'],['second'])
                detail=w.read_json(self.root/mode/'first/result.json')
                self.assertEqual(detail['inputAssessment']['classification'],classification)
                self.assertEqual(detail['infrastructure']['status'],'NOT_TESTED')

    def test_correct_source_pair_is_carried_from_pinned_context_into_request(self):
        self.job['cases']=[self.case('first','matched-control-source')];self.write_job()
        out=self.run_job();self.assertEqual(out['status'],'PASS')
        request=w.read_json(self.root/'batch/first/request.json')
        expected={name:pin['sha256'] for name,pin in self.route['inputControlSources'].items()}
        self.assertEqual(request['inputControlIdentity'],expected)
        detail=w.read_json(self.root/'batch/first/result.json')
        self.assertTrue(detail['inputAssessment']['sourceIdentityMatched'])
        self.assertTrue(detail['inputAssessment']['controlQualified'])
        planned=w.plan(self.path)
        self.assertTrue({'stock-source.json','candidate-source.json'} <= {Path(p['path']).name for p in planned['pins']})
        (self.root/'candidate-source.json').write_text('changed fixture')
        with self.assertRaisesRegex(w.WorkflowError,'Input control source manifest changed'):w.plan(self.path)

    def test_missing_expected_source_identity_censors_supplied_control(self):
        self.route.pop('inputControlSources');self.write_route()
        self.job['cases'][0]=self.case('first','matched-control-source');self.write_job()
        out=self.run_job();self.assertEqual(out['status'],'NOT_TESTED');self.assertEqual(out['notStarted'],['second'])
        detail=w.read_json(self.root/'batch/first/result.json')
        self.assertEqual(detail['inputAssessment']['classification'],'SOURCE_IDENTITY_UNBOUND')


class CandidatePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'addon.gproj').write_text('GameProject { GUID "0123456789ABCDEF" }')
        (self.root/'Scene.ent').write_text('GenericEntity {}')
        self.manifest = {'schema': 1, 'files': [
            {'path': 'addon.gproj', 'sha256': w.sha(self.root/'addon.gproj'), 'resourceId': '0123456789ABCDEF'},
            {'path': 'Scene.ent', 'sha256': w.sha(self.root/'Scene.ent')}]}
        self.facts = {'schema': 1, 'candidateId': 'vehicle-r2', 'manifestSha256': '',
                      'resources': [{'path': 'addon.gproj', 'resourceId': '0123456789ABCDEF'}],
                      'contexts': [{'name': 'cargo', 'frame': 'entity', 'position': [0, 1, -2]}],
                      'fuelNodes': [{'nodeId': 'inherited-tank', 'capacity': 50}],
                      'input': {'capability': True, 'foreground': True, 'occupied': True,
                                'reservationsReleased': True, 'transitionTags': [], 'requestedEvents': 0, 'deliveredEvents': 0}}
        self.ledger = {'schema': 1, 'candidateId': 'vehicle-r2', 'supersedes': ['vehicle-r1'],
                       'contracts': {'contexts': [{'name': 'cargo', 'frame': 'entity', 'position': [0, 1, -2], 'tolerance': .001}],
                                     'fuelNodes': [{'nodeId': 'inherited-tank', 'capacity': 50}]}, 'libraryPins': []}
        self.path = self.root/'candidate-ledger.json'
        self.write()

    def write(self, link_manifest=True):
        (self.root/'source-manifest.json').write_text(json.dumps(self.manifest))
        if link_manifest:
            self.facts['manifestSha256'] = w.sha(self.root/'source-manifest.json')
        (self.root/'facts.json').write_text(json.dumps(self.facts))
        for key, name in (('manifest', 'source-manifest.json'), ('facts', 'facts.json')):
            self.ledger[key] = {'path': name, 'sha256': w.sha(self.root/name)}
        self.path.write_text(json.dumps(self.ledger))

    def check(self):
        with patch('workflow.subprocess.Popen', side_effect=AssertionError('preflight must never launch')):
            return w.candidate_preflight(self.path)

    def job(self):
        (self.root/'adapter.py').write_text('# Offline test placeholder; never executed')
        job = {'schema': 1, 'template': 'startup', 'project': 'addon.gproj', 'world': 'Scene.ent',
               'sourceRoots': ['.'], 'addonRoots': ['.'], 'requiredFiles': [], 'requiredClasses': [],
               'capabilities': ['isolated-reset', 'owned-lifecycle', 'native-load'],
               'adapter': {'executable': sys.executable, 'script': 'adapter.py',
                           'args': ['{script}', '{request}', '{result}', '{cancel}']},
               'cases': [{'id': 'integrated', 'parameters': {}, 'assertions': ['fixture.ready', 'world.loaded']}],
               'timeoutSeconds': 3, 'closeGraceSeconds': 2, 'candidateLedger': self.path.name}
        path = self.root/'job.json';path.write_text(json.dumps(job));return path

    def library_pin(self):
        (self.root/'restored-export.bin').write_bytes(b'Pinned artifact bytes')
        self.ledger['libraryPins'] = [{'path': 'restored-export.bin', 'sha256': w.sha(self.root/'restored-export.bin'),
                                      'fileId': 'durable-file-123', 'version': 'version-7'}]

    def test_consistent_candidate_is_static_not_tested_and_capability_is_not_input(self):
        out = self.check()
        self.assertEqual(out['status'], 'NOT_TESTED')
        self.assertEqual(out['candidateId'], 'vehicle-r2')
        self.assertTrue(out['input']['readyForProbe'])
        self.assertFalse(out['input']['inputDelivered'])
        self.assertFalse(out['input']['behaviorQualified'])

    def test_wrong_bone_frame_blocks_before_any_launch(self):
        self.facts['contexts'][0]['frame'] = 'bone:v_body';self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'CONTEXT_FRAME_MISMATCH'):self.check()

    def test_context_position_mismatch_and_missing_observation(self):
        self.facts['contexts'][0]['position'][1] = 4;self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'CONTEXT_POSITION_MISMATCH'):self.check()
        self.facts['contexts'] = [];self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'CONTEXT_FRAME_MISMATCH'):self.check()

    def test_context_position_rejects_boolean_and_invalid_tolerance(self):
        self.facts['contexts'][0]['position'][0] = True;self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'Finite XYZ'):self.check()
        self.facts['contexts'][0]['position'][0] = 0
        self.ledger['contracts']['contexts'][0]['tolerance'] = -1;self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'tolerance'):self.check()

    def test_additional_inherited_fuel_node_blocks(self):
        self.facts['fuelNodes'].append({'nodeId': 'accidental-second-tank', 'capacity': 40});self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'FUEL_NODE_TOPOLOGY_MISMATCH'):self.check()

    def test_duplicate_effective_fuel_identity_and_capacity_mismatch(self):
        self.facts['fuelNodes'].append(dict(self.facts['fuelNodes'][0]));self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'Unique nonempty nodeId'):self.check()
        self.facts['fuelNodes'].pop();self.facts['fuelNodes'][0]['capacity'] = 90;self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'FUEL_CAPACITY_MISMATCH'):self.check()

    def test_vehicle_specific_multiple_fuel_nodes_are_supported(self):
        node = {'nodeId': 'legitimate-auxiliary-tank', 'capacity': 20}
        self.ledger['contracts']['fuelNodes'].append(node)
        self.facts['fuelNodes'].append(node);self.write()
        self.assertEqual(self.check()['status'], 'NOT_TESTED')

    def test_changed_source_or_resource_identity_blocks(self):
        (self.root/'Scene.ent').write_text('ChangedEntity {}')
        with self.assertRaisesRegex(w.WorkflowError, 'CANDIDATE_IDENTITY_MISMATCH'):self.check()
        (self.root/'Scene.ent').write_text('GenericEntity {}')
        self.facts['resources'][0]['resourceId'] = 'FEDCBA9876543210';self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'RESOURCE_IDENTITY_MISMATCH'):self.check()

    def test_old_candidate_handoff_and_old_source_snapshot_are_rejected(self):
        self.facts['candidateId'] = 'vehicle-r1';self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'STALE_CANDIDATE_FACTS'):self.check()
        self.facts['candidateId'] = 'vehicle-r2';self.facts['manifestSha256'] = '0'*64;self.write(False)
        with self.assertRaisesRegex(w.WorkflowError, 'STALE_CANDIDATE_FACTS'):self.check()

    def test_duplicate_resource_or_source_records_are_rejected(self):
        self.manifest['files'].append(dict(self.manifest['files'][0]));self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'Duplicate candidate source'):self.check()
        self.manifest['files'].pop();self.facts['resources'].append(dict(self.facts['resources'][0]));self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'Duplicate resource fact'):self.check()

    def test_durable_library_pin_survives_restore_and_rejects_changed_bytes(self):
        self.library_pin();self.write();self.check()
        (self.root/'restored-export.bin').unlink()
        with self.assertRaisesRegex(w.WorkflowError, 'CANDIDATE_ARTIFACT_UNAVAILABLE'):self.check()
        (self.root/'restored-export.bin').write_bytes(b'Pinned artifact bytes');self.check()
        (self.root/'restored-export.bin').write_bytes(b'Wrong download')
        with self.assertRaisesRegex(w.WorkflowError, 'CANDIDATE_IDENTITY_MISMATCH'):self.check()

    def test_library_pin_requires_durable_version(self):
        self.library_pin();self.ledger['libraryPins'][0]['version'] = '';self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'fileId/version'):self.check()

    def test_windows_metadata_capability_error_is_not_empty_transfer_success(self):
        self.facts['transfer'] = {'metadataSupported': False, 'expectedFiles': 1, 'completedFiles': 0,
                                  'error': "AttributeError: module os has no attribute setxattr"};self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'TRANSFER_CAPABILITY_ERROR.*setxattr'):self.check()

    def test_zero_file_transfer_and_wrong_count_are_incomplete(self):
        self.facts['transfer'] = {'metadataSupported': True, 'expectedFiles': 1, 'completedFiles': 0, 'error': None};self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'TRANSFER_INCOMPLETE'):self.check()
        self.facts['transfer']['completedFiles'] = 1;self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'TRANSFER_INCOMPLETE'):self.check()

    def test_transfer_receipt_requires_matching_local_hash_pins(self):
        self.library_pin()
        self.facts['transfer'] = {'metadataSupported': True, 'expectedFiles': 1, 'completedFiles': 1, 'error': None};self.write()
        self.assertEqual(self.check()['status'], 'NOT_TESTED')

    def test_sendinput_zero_or_partial_delivery_is_not_input_success(self):
        for delivered in (0, 1):
            self.facts['input'].update(requestedEvents=2, deliveredEvents=delivered);self.write()
            with self.assertRaisesRegex(w.WorkflowError, 'INPUT_NOT_DELIVERED'):self.check()

    def test_capability_and_graph_readiness_are_separate(self):
        self.facts['input']['capability'] = False;self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'INPUT_CAPABILITY_UNAVAILABLE'):self.check()
        self.facts['input']['capability'] = True
        for key, value, original in [('transitionTags', ['TagVehicleClosingDoor'], []),
                                      ('reservationsReleased', False, True), ('foreground', False, True), ('occupied', False, True)]:
            self.facts['input'][key] = value;self.write()
            with self.assertRaisesRegex(w.WorkflowError, 'INPUT_NOT_READY'):self.check()
            self.facts['input'][key] = original

    def test_reported_complete_delivery_still_cannot_qualify_behavior(self):
        self.facts['input'].update(requestedEvents=2, deliveredEvents=2);self.write()
        out = self.check()['input']
        self.assertTrue(out['inputDelivered']);self.assertFalse(out['behaviorQualified'])
        self.assertEqual(out['status'], 'NOT_TESTED')

    def test_shutdown_hang_pending_or_denied_never_becomes_permission_to_retry(self):
        previous = {'state': 'EXITED_VERIFIED', 'operationId': 'retained-operation', 'reason': 'fixture observation',
                    'verifiedExited': True, 'leaseReleased': True}
        self.facts['previousAttempt'] = previous
        for state in ('PENDING', 'UNCERTAIN', 'DENIED'):
            previous['state'] = state;self.write()
            with self.assertRaisesRegex(w.WorkflowError, 'PREVIOUS_ATTEMPT_UNRESOLVED'):self.check()
        previous['state'] = 'EXITED_VERIFIED';previous['verifiedExited'] = False;self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'PREVIOUS_ATTEMPT_UNRESOLVED'):self.check()
        previous['verifiedExited'] = True;self.write();self.check()

    def test_candidate_plan_pins_ledger_facts_source_and_library_without_launch(self):
        self.library_pin();self.write()
        with patch('workflow.subprocess.Popen', side_effect=AssertionError('launch')):
            planned = w.run(self.job(), self.root/'unused')
        self.assertEqual(planned['candidate']['candidateId'], 'vehicle-r2')
        pins = {p['path'] for p in planned['pins']}
        for name in ('candidate-ledger.json', 'facts.json', 'source-manifest.json', 'restored-export.bin'):
            self.assertIn(str(self.root/name), pins)
        (self.root/'facts.json').write_text('{}')
        with self.assertRaisesRegex(w.WorkflowError, 'Input changed'):w.verify_pins(planned)
        self.assertFalse((self.root/'unused').exists())

    def test_candidate_and_route_preflights_coexist_and_invalid_candidate_stops_execute(self):
        path=self.job();job=w.read_json(path)
        context=self.root/'route.json'
        context.write_text(json.dumps({'schema':1,'task':'validate','claim':'native-load',
            'permission':'allowed','ownership':'clear','previousAttempt':'none'}))
        job['routeContext']=context.name;path.write_text(json.dumps(job))
        with patch('workflow.subprocess.Popen',side_effect=AssertionError('launch')):
            planned=w.plan(path)
            self.assertEqual(planned['candidate']['candidateId'],'vehicle-r2')
            self.assertEqual(planned['routePreflight']['admission'],'READY')
            pins={row['path'] for row in planned['pins']}
            self.assertIn(str(context),pins);self.assertIn(str(self.path),pins)
            self.facts['fuelNodes'].append({'nodeId':'unintended-added-tank','capacity':10});self.write()
            with self.assertRaisesRegex(w.WorkflowError,'FUEL_NODE_TOPOLOGY_MISMATCH'):
                w.run(path,self.root/'must-not-launch',execute=True)
        self.assertFalse((self.root/'must-not-launch').exists())

    def test_manifest_must_bind_actual_planned_project_and_world(self):
        self.manifest['files'] = self.manifest['files'][:1];self.write()
        with self.assertRaisesRegex(w.WorkflowError, 'must include project and world'):w.plan(self.job())

    def test_preflight_cli_is_read_only_and_returns_not_tested(self):
        before = w.sha(self.path)
        with patch('workflow.subprocess.Popen', side_effect=AssertionError('launch')), contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(w.main(['preflight', '--ledger', str(self.path)]), 0)
        self.assertEqual(json.loads(stream.getvalue())['status'], 'NOT_TESTED')
        self.assertEqual(w.sha(self.path), before)


if __name__=='__main__':unittest.main()
