"""Fail-closed provenance boundary for the approved perfect-maze A1 amendment."""
import json

from .foundation_calibration import ROOT
from .foundation_study import read_compressed
from .routing_transfer import sha
from .deep_campaign_store import hashed, packed, unpacked

SETUP_A1 = ROOT / 'results/deep_campaign_amendment_a1'
KEY = 'perfect11_amendment_a1'


def check_amendment():
    path = SETUP_A1 / 'registration.json'
    registration = json.loads(path.read_text())
    for name, digest in registration['files'].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f'A1 sealed file changed: {name}')
    registration['registration_sha256'] = sha(path)
    return registration


def boundary_check(j, registration, initial=False):
    b = registration['boundary']
    row = j.db.execute(
        'SELECT chain_hash,state_hash,complete FROM stages WHERE n=?',
        (b['latest_stage'],)).fetchone()
    if row != (b['chain'], b['state_sha256'], 1):
        raise ValueError('A1 requires the exact saved history boundary')
    if j.get('config') != registration['original_config']:
        raise ValueError('A1 cannot change the original configuration')
    usage = j.get('usage')
    if initial:
        if (j.get('latest') != b['latest_stage'] or j.pending() is not None
                or usage != b['usage']
                or hashed(packed(j.state())) != b['state_sha256']
                or hashed(packed(sorted(j.layouts()))) != b['layouts_sha256']):
            raise ValueError('A1 requires the exact stopped checkpoint, usage and layouts')
    elif any(usage[k] < v for k, v in b['usage'].items()):
        raise ValueError('A1 cumulative usage went backwards')


def binding(registration):
    return dict(registration_sha256=registration['registration_sha256'],
                boundary=registration['boundary'],
                exclusions_sha256=registration['files'][
                    'results/deep_campaign_amendment_a1/additional_exclusions.json.gz'])


def bind_amendment(j, registration):
    """Add exclusions and phase metadata atomically; never replace saved history."""
    if j.get(KEY) is not None:
        verify_amendment(j, registration)
        return
    boundary_check(j, registration, initial=True)
    extra = read_compressed(SETUP_A1 / 'additional_exclusions.json.gz')['hashes']
    if len(extra) != len(set(extra)) or set(extra) & j.layouts():
        raise ValueError('Additional exclusions must be distinct from journal layouts')
    with j.db:
        j.db.executemany('INSERT INTO layouts VALUES (?)', ((h,) for h in extra))
        j.put(KEY, binding(registration))
    verify_amendment(j, registration)


def verify_amendment(j, registration):
    boundary_check(j, registration)
    if j.get(KEY) != binding(registration):
        raise ValueError('A1 registration binding differs or is missing')
    extra = set(read_compressed(SETUP_A1 / 'additional_exclusions.json.gz')['hashes'])
    if not extra <= j.layouts():
        raise ValueError('A1 excluded layouts are missing')
    for raw, in j.db.execute('SELECT input FROM stages WHERE n>? ORDER BY n',
                            (registration['boundary']['latest_stage'],)):
        data = unpacked(raw)
        if (data.get('amendment') != registration['registration_sha256']
                or data['generation'] < registration['boundary']['generation']
                or data['generation'] > registration['original_config']['milestone']):
            raise ValueError('Post-boundary stage lacks the registered A1 provenance')
        for row in data['mazes']:
            family = data['metadata'][row['case_id']]['family']
            if family.startswith('ordinary_'):
                n = 11 if family == 'ordinary_perfect' else 9
                if (row['w'], row['h']) != (n, n):
                    raise ValueError('Post-boundary ordinary dimensions differ')
