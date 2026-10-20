"""Seal the approved and successfully rehearsed A1 protocol before continuation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maze_evolution.deep_campaign import ROOT, check_setup, source_manifest
from maze_evolution.deep_campaign_amendment import SETUP_A1
from maze_evolution.routing_transfer import sha


def main():
    config = check_setup()
    target = SETUP_A1 / 'registration.json'
    if target.exists():
        raise RuntimeError('Never overwrite the A1 registration')
    preflight = json.loads((SETUP_A1 / 'preflight.json').read_text())
    assert preflight['passed'] and preflight['scientific_state_unchanged']
    assert preflight['discarded_rounds'] == 16
    assert preflight['replay']['births_replayed'] == 2496
    assert preflight['added_usage']['candidate_seconds'] < 600
    assert preflight['wall_seconds'] < 900
    current = source_manifest()
    for k in ('files', 'python', 'dependencies'):
        assert current[k] == preflight['environment'][k], k
    validation = json.loads((SETUP_A1 / 'validation.json').read_text())
    assert validation['passed'] and validation['tests_passed'] == 24
    failure = ROOT / 'results/deep_campaign_run/failure_08268/manifest.json'
    failure_files = json.loads(failure.read_text())['files']
    for name, value in failure_files.items():
        assert sha(ROOT / name) == value['sha256'], name
    files = [
        ROOT / 'docs/DEEP_CAMPAIGN_AMENDMENT_A1.md',
        ROOT / 'tests/test_deep_amendment_a1.py',
        ROOT / 'tools/prepare_deep_amendment_a1.py',
        ROOT / 'tools/register_deep_amendment_a1.py',
        ROOT / 'tools/inspect_deep_campaign.py',
        ROOT / 'results/deep_campaign_setup/registration.json', failure,
        *(ROOT / p for p in failure_files),
        *(ROOT / p for p in current['files'] if p.startswith('maze_evolution/deep_campaign_')),
        *sorted(p for p in SETUP_A1.iterdir() if p.is_file())]
    packet = dict(
        amendment='perfect11_a1', registered_at=datetime.now(timezone.utc).isoformat(),
        authorization='User approved the documented 11x11 continuation proposal.',
        original_frozen_commit='7854ada78b70b445e52816ed1e0869265bb5c6f2',
        failure_packet_commit='a6de4e9',
        boundary=json.loads((SETUP_A1 / 'boundary.json').read_text()),
        original_config=config,
        changed_domain='ordinary perfect 9x9 to 11x11; training and development assessments',
        unchanged='selection, reproduction, populations/RNG, runtime, counts, cumulative bounds, milestone',
        storage_guard='Original 20 GiB bound now includes nested local backups',
        milestone=10000, confirmation_not_generated=True,
        python=current['python'], dependencies=current['dependencies'],
        files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))})
    target.write_text(json.dumps(packet, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(registration_sha256=sha(target), sealed_files=len(packet['files']))))


if __name__ == '__main__':
    main()
