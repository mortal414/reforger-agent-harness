"""Offline route admission and retained lessons. Never launches or sends input."""
from pathlib import Path
import re

from workflow import exact_keys, file_identity, read_json, require, strings

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'examples/workflows/routes.json'
LESSONS = ROOT / 'examples/workflows/lessons.json'
STATES = {'available', 'validated', 'unsupported', 'unverified'}
HUMAN_ASSERTIONS = {'release.human-acceptance', 'human.acceptance', 'input.physical-acceptance'}
TASKS = {'research', 'create', 'configure', 'import', 'validate', 'package', 'playtest', 'capture', 'human-acceptance'}
DEFAULTS = {
    'startup': ('validate', 'native-load'), 'visual': ('capture', 'native-image'),
    'release': ('package', 'package-artifact'),
}


def catalog():
    data = read_json(CATALOG)
    exact_keys(data, ['schema', 'routes'], ['schema', 'routes'])
    require(data['schema'] == 1 and isinstance(data['routes'], list), 'Invalid route catalog')
    ids = set()
    for row in data['routes']:
        exact_keys(row, ['id', 'tasks', 'claims', 'mode', 'state', 'sources', 'commands', 'proves',
                         'doesNotProve', 'nextStep', 'method'],
                        ['id', 'tasks', 'claims', 'mode', 'state', 'sources', 'commands', 'proves',
                         'doesNotProve', 'nextStep', 'method'])
        require(isinstance(row['id'], str) and row['id'] not in ids, 'Unique route ID required')
        ids.add(row['id'])
        require(row['state'] in STATES and row['mode'] in ('offline', 'native', 'desktop', 'human'), 'Invalid route state/mode')
        require(set(strings(row['tasks'], 'route.tasks', 1)) <= TASKS, 'Unknown route task')
        for key in ('claims', 'sources', 'commands', 'proves', 'doesNotProve'):
            strings(row[key], 'route.' + key, 1)
        for key in ('nextStep', 'method'):
            require(isinstance(row[key], str) and row[key].strip(), 'Nonempty route ' + key + ' required')
    return data['routes']


def lessons(symptom=None):
    data = read_json(LESSONS)
    exact_keys(data, ['schema', 'lessons'], ['schema', 'lessons'])
    require(data['schema'] == 1 and isinstance(data['lessons'], list), 'Invalid lessons catalog')
    ids = set()
    for row in data['lessons']:
        exact_keys(row, ['id', 'symptoms', 'observation', 'cause', 'recovery', 'sources', 'nextSteps'],
                        ['id', 'symptoms', 'observation', 'cause', 'recovery', 'sources', 'nextSteps'])
        require(row['id'] not in ids, 'Duplicate lesson')
        ids.add(row['id'])
        for key in ('symptoms', 'sources', 'nextSteps'):
            strings(row[key], 'lesson.' + key, 1)
        require(isinstance(row['observation'], str) and row['observation'].strip(), 'Lesson observation required')
        # Unknown is deliberately null, never a guessed technical fix.
        for key in ('cause', 'recovery'):
            require(row[key] is None or isinstance(row[key], str) and row[key].strip(), 'Invalid lesson ' + key)
    return [row for row in data['lessons'] if symptom is None or symptom in row['symptoms']]


def preflight(context, base=ROOT):
    """Capability recommendation, not permission, adapter qualification or gameplay."""
    exact_keys(context, ['schema', 'task', 'claim', 'permission', 'ownership', 'previousAttempt',
                         'route', 'assessments', 'desktopReason', 'inputControlSources'],
                        ['schema', 'task', 'claim', 'permission', 'ownership', 'previousAttempt'])
    require(type(context['schema']) is int and context['schema'] == 1, 'Unsupported route context')
    require(isinstance(context['task'], str) and context['task'] in TASKS, 'Unknown task')
    require(isinstance(context['claim'], str) and context['claim'].strip(), 'Explicit claim required')
    require(context['permission'] in ('allowed', 'denied', 'unknown'), 'Explicit permission state required')
    require(context['ownership'] in ('clear', 'occupied', 'unknown'), 'Explicit ownership state required')
    require(context['previousAttempt'] in ('none', 'closed', 'pending', 'denied', 'uncertain'), 'Explicit attempt state required')
    rows = catalog()
    by_id = {row['id']: row for row in rows}
    assessments = context.get('assessments', {})
    require(isinstance(assessments, dict) and set(assessments) <= set(by_id), 'Unknown route assessment')
    pins = [file_identity(CATALOG), file_identity(LESSONS), file_identity(Path(__file__))]
    control_identity, control_pins = input_source_identity(context, base)
    pins.extend(control_pins)
    candidates = []
    for original in rows:
        if context['task'] not in original['tasks']:
            continue
        row = dict(original)
        source_paths = [ROOT / source for source in row['sources']]
        row['sourcesPresent'] = all(p.is_file() for p in source_paths)
        for source in source_paths:
            if source.is_file():
                pins.append(file_identity(source))
        if not row['sourcesPresent']:
            row['state'] = 'unverified'
        if row['id'] in assessments:
            assessment = assessments[row['id']]
            exact_keys(assessment, ['state', 'reason', 'evidence'], ['state', 'reason', 'evidence'])
            require(isinstance(assessment['state'], str) and assessment['state'] in STATES, 'Invalid assessment state')
            require(isinstance(assessment['reason'], str) and assessment['reason'].strip(), 'Assessment reason required')
            require(isinstance(assessment['evidence'], list) and 1 <= len(assessment['evidence']) <= 32, 'Pinned assessment evidence required')
            evidence = []
            for pin in assessment['evidence']:
                exact_keys(pin, ['path', 'sha256'], ['path', 'sha256'])
                actual = file_identity(Path(base) / pin['path'])
                require(actual['sha256'] == pin['sha256'], 'Route evidence changed: ' + actual['path'])
                evidence.append(actual)
            pins.extend(evidence)
            row.update(assessment)
            # An assertion that tooling is installed cannot repair absent source.
            if not row['sourcesPresent']:
                row['state'] = 'unverified'
        row['supportsClaim'] = context['claim'] in row['claims']
        candidates.append(row)
    candidates.sort(key=lambda row: (row['mode'] in ('desktop', 'human'), row['state'] not in ('validated', 'available'), row['state'] != 'validated'))
    result = {'schema': 1, 'status': 'NOT_TESTED', 'admission': 'HOLD', 'selected': None,
              'task': context['task'], 'claim': context['claim'], 'candidates': candidates,
              'inputControlIdentity': control_identity,
              'pins': list({p['path']: p for p in pins}.values()),
              'humanAcceptance': 'PENDING: ordinary discovery, entry/exit, controls and restored use on the exact release candidate',
              'lessons': lessons('injected-input-zero-events') if context['task'] in ('playtest', 'human-acceptance') else [],
              'reason': '', 'desktopReason': context.get('desktopReason')}
    def hold(reason):
        result['reason'] = reason
        return result
    if context['permission'] != 'allowed' or context['previousAttempt'] == 'denied':
        return hold('PERMISSION_' + ('DENIED' if context['previousAttempt'] == 'denied' else context['permission'].upper()) + ': stop this goal; no alternative route bypass')
    if context['previousAttempt'] in ('pending', 'uncertain'):
        return hold('PREVIOUS_ATTEMPT_UNRESOLVED: inspect the existing outcome/owner before any route')
    eligible = [row for row in candidates if row['supportsClaim']]
    requested = context.get('route')
    require(requested is None or isinstance(requested, str) and requested in by_id, 'Unknown requested route')
    if requested:
        matches = [row for row in eligible if row['id'] == requested]
        if not matches:
            return hold('CLAIM_UNSUPPORTED: requested route cannot establish this task/claim')
        selected = matches[0]
    else:
        selected = next((row for row in eligible if row['state'] in ('available', 'validated')), None)
    if selected is None or selected['state'] not in ('available', 'validated'):
        return hold('ROUTE_UNVERIFIED: follow candidate nextStep; research/adapt supported APIs or file plans before desktop')
    if selected['mode'] in ('desktop', 'human'):
        alternatives = [row for row in eligible if row['mode'] not in ('desktop', 'human')]
        if any(row['state'] in ('available', 'validated') for row in alternatives):
            return hold('PROGRAMMATIC_ROUTE_AVAILABLE: use the supported non-desktop candidate')
        if any(row['state'] != 'unsupported' for row in alternatives):
            return hold('PROGRAMMATIC_ROUTE_UNVERIFIED: missing knowledge is not proof desktop is necessary')
        if not isinstance(context.get('desktopReason'), str) or not context['desktopReason'].strip():
            return hold('DESKTOP_REASON_REQUIRED: record the residual task and why direct input is necessary')
    if selected['mode'] != 'offline' and context['ownership'] != 'clear':
        return hold('OWNERSHIP_UNRESOLVED: preserve the occupied/unknown native or human session')
    if selected['id'] == 'desktop-input-probe' and control_identity is None:
        return hold('INPUT_CONTROL_IDENTITY_REQUIRED: pin stock and candidate source/build/fixture manifests before a delivery probe')
    result.update(admission='READY' if selected['mode'] != 'human' else 'HUMAN_REQUIRED', selected=selected,
                  reason='Route available for this claim only; current adapter admission, measurements and lifecycle remain required')
    return result


def for_job(job, job_path):
    if 'routeContext' in job:
        require(isinstance(job['routeContext'], str) and job['routeContext'].strip(), 'Explicit routeContext path required')
        path = (Path(job_path).parent / job['routeContext']).resolve(strict=True)
        result = preflight(read_json(path), path.parent)
        result['pins'].append(file_identity(path))
        return result
    task, claim = DEFAULTS.get(job['template'], ('playtest', 'measured-behavior'))
    return preflight({'schema': 1, 'task': task, 'claim': claim, 'permission': 'unknown',
                      'ownership': 'unknown', 'previousAttempt': 'uncertain'})


def input_source_identity(context, base=ROOT):
    """Bind an explicit stock/candidate pair to reviewed manifest bytes, not labels."""
    require(isinstance(context, dict), 'Expected reviewed input source context object')
    sources = context.get('inputControlSources')
    if sources is None:
        return None, []
    exact_keys(sources, ['stock', 'candidate'], ['stock', 'candidate'])
    identity, pins = {}, []
    for name in ('stock', 'candidate'):
        pin = sources[name]
        exact_keys(pin, ['path', 'sha256'], ['path', 'sha256'])
        require(isinstance(pin['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', pin['sha256']),
                'Explicit source/fixture manifest SHA-256 required: ' + name)
        require(isinstance(pin['path'], str) and pin['path'].strip(), 'Explicit source/fixture manifest path required: ' + name)
        actual = file_identity(Path(base) / pin['path'])
        require(actual['sha256'] == pin['sha256'], 'Input control source manifest changed: ' + name)
        identity[name] = actual['sha256']
        pins.append(actual)
    return identity, pins


def identity_pair(value):
    return isinstance(value, dict) and set(value) == {'stock', 'candidate'} and all(
        isinstance(v, str) and re.fullmatch(r'[0-9a-f]{64}', v) for v in value.values())


def input_control(value, run_id=None, case_id=None, expected_identity=None):
    """Classify a same-attempt stock control, without inventing a technical cause."""
    exact_keys(value, ['schema', 'runId', 'caseId', 'sourceIdentity', 'stock', 'candidate', 'physicalStockObserved'],
                     ['schema', 'runId', 'caseId', 'stock', 'candidate', 'physicalStockObserved'])
    require(type(value['schema']) is int and value['schema'] == 1, 'Invalid input control schema')
    for key in ('runId', 'caseId'):
        require(isinstance(value[key], str) and value[key].strip(), 'Input identity required: ' + key)
    require(run_id is None or value['runId'] == run_id, 'Stale input run')
    require(case_id is None or value['caseId'] == case_id, 'Wrong input case')
    require(value['physicalStockObserved'] is None or type(value['physicalStockObserved']) is bool, 'Explicit physical stock observation or null required')
    for key in ('stock', 'candidate'):
        row = value[key]
        exact_keys(row, ['spawned', 'requestedEvents', 'deliveredEvents', 'behaviorObserved'],
                        ['spawned', 'requestedEvents', 'deliveredEvents', 'behaviorObserved'])
        for field in ('spawned', 'behaviorObserved'):
            require(row[field] is None or type(row[field]) is bool, 'Unknown observation must be null')
        for field in ('requestedEvents', 'deliveredEvents'):
            require(row[field] is None or type(row[field]) is int and 0 <= row[field] <= 10000, 'Invalid event count')
        if row['deliveredEvents'] is not None and row['requestedEvents'] is not None:
            require(row['deliveredEvents'] <= row['requestedEvents'], 'Delivered exceeds requested input')
    stock, candidate = value['stock'], value['candidate']
    qualified = False
    if stock['spawned'] is not True or stock['requestedEvents'] in (None, 0) or stock['deliveredEvents'] is None or stock['behaviorObserved'] is None:
        classification = 'STOCK_CONTROL_NOT_TESTED'
    elif stock['deliveredEvents'] == 0:
        classification = 'INPUT_DELIVERY_OR_FIXTURE_UNQUALIFIED'
    elif stock['deliveredEvents'] != stock['requestedEvents'] or stock['behaviorObserved'] is not True:
        classification = 'STOCK_CONTROL_FAILED'
    elif candidate['spawned'] is not True or candidate['requestedEvents'] in (None, 0) or candidate['deliveredEvents'] is None or candidate['behaviorObserved'] is None:
        classification = 'CANDIDATE_NOT_TESTED'
    elif candidate['deliveredEvents'] != candidate['requestedEvents']:
        classification = 'CANDIDATE_INPUT_PATH_UNQUALIFIED'
    else:
        classification = 'DELIVERY_CONTROL_QUALIFIED'
        qualified = True
    observation_classification = classification
    observed_identity = value.get('sourceIdentity')
    identity_failure = (
        'SOURCE_IDENTITY_MISSING' if observed_identity is None else
        'SOURCE_IDENTITY_INVALID' if not identity_pair(observed_identity) else
        'SOURCE_IDENTITY_UNBOUND' if expected_identity is None else
        'EXPECTED_SOURCE_IDENTITY_INVALID' if not identity_pair(expected_identity) else
        'SOURCE_IDENTITY_MISMATCH' if observed_identity != expected_identity else None)
    if identity_failure:
        classification, qualified = identity_failure, False
    return {'status': 'NOT_TESTED', 'classification': classification, 'controlQualified': qualified,
            'observationClassification': observation_classification,
            'runId': value['runId'], 'caseId': value['caseId'], 'sourceIdentity': observed_identity,
            'expectedSourceIdentity': expected_identity, 'sourceIdentityMatched': identity_failure is None,
            'vehicleDefectEstablished': False, 'cause': None, 'recovery': None,
            'reason': (identity_failure + '; ' if identity_failure else '') + 'Reported delivery control only; physical acceptance and functional assertions remain separate',
            'physicalStockObserved': value['physicalStockObserved'], 'lessons': lessons('injected-input-zero-events')}


def validate_evidence(result, request):
    """Add a required provenance/measurement check; never manufacture gameplay."""
    route = request['route']
    proof = result.get('routeEvidence')
    check = {'status': 'NOT_TESTED', 'reason': 'Adapter supplied no route-specific measurement/provenance'}
    if proof is not None:
        exact_keys(proof, ['routeId', 'method', 'measurements'], ['routeId', 'method', 'measurements'])
        require(proof['routeId'] == route['id'] and proof['method'] == route['method'], 'Route evidence mechanism/identity differs')
        require(isinstance(proof['measurements'], dict) and 1 <= len(proof['measurements']) <= 256, 'Route measurements required')
        # Empty/null/string labels are not actual measurements. Domain thresholds
        # remain the responsibility of the existing addon-owned assertions.
        import math
        require(all(isinstance(k, str) and k.strip() and
                    (type(v) is bool or type(v) in (int, float) and math.isfinite(v))
                    for k, v in proof['measurements'].items()), 'Finite numeric/boolean route measurements required')
        if result['evidence']:
            check = {'status': 'PASS', 'reason': 'Route identity, reported measurement presence and durable evidence only; not gameplay acceptance', 'actual': proof}
    result['assertions']['route.evidence'] = check
    if route['mode'] in ('native', 'desktop') or request.get('claim') == 'measured-behavior':
        import math
        def has_measurement(value):
            if type(value) is bool:
                return True
            if type(value) in (int, float):
                return math.isfinite(value)
            if isinstance(value, dict):
                return any(has_measurement(v) for v in value.values())
            if isinstance(value, list):
                return any(has_measurement(v) for v in value)
            return False
        for name in request['assertions']:
            if name in ('fixture.ready', 'route.evidence'):
                continue
            assertion = result['assertions'][name]
            if assertion['status'] == 'PASS' and not has_measurement(assertion.get('actual')):
                result['assertions'][name] = {'status': 'NOT_TESTED',
                    'reason': 'Functional assertion reported PASS without an actual numeric/boolean measurement; ' + assertion['reason']}
    for name in HUMAN_ASSERTIONS & set(result['assertions']):
        if result['assertions'][name]['status'] == 'PASS':
            result['assertions'][name] = {'status': 'NOT_TESTED',
                'reason': 'Exact-candidate physical human acceptance requires a separate owner receipt; automated route evidence cannot qualify it'}
    if route['id'] == 'desktop-input-probe':
        control = result.get('inputControl')
        assessment = input_control(control, request['runId'], request['caseId'], request.get('inputControlIdentity')) if control is not None else None
        if assessment is None or not assessment['controlQualified']:
            result['infrastructure'] = {'status': 'NOT_TESTED', 'reason': 'Stock input control unqualified: ' +
                                        (assessment['classification'] if assessment else 'STOCK_CONTROL_NOT_TESTED')}
        result['inputAssessment'] = assessment
    # A supplied stock failure also censors attribution on any other input route.
    elif result.get('inputControl') is not None:
        assessment = input_control(result['inputControl'], request['runId'], request['caseId'], request.get('inputControlIdentity'))
        result['inputAssessment'] = assessment
        if not assessment['controlQualified']:
            result['infrastructure'] = {'status': 'NOT_TESTED', 'reason': 'Stock input control unqualified: ' + assessment['classification']}
