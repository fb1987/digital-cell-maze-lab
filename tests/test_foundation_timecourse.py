from maze_evolution.foundation_study_timecourse import boundary_aliases


def test_timecourse_uses_completed_generations_without_duplicating_final_boundary():
    state = dict(config=dict(study='unit', topology='local', origin='fresh', method='evolution', replicate=0),
                 frozen={'id': 'initial'}, history=[{'champion': f'after_{g + 1}_completed'} for g in range(300)])
    rows = boundary_aliases([state], 300)
    assert [(r['generation'], r['id']) for r in rows] == [(0, 'initial'), (48, 'after_48_completed'),
        (128, 'after_128_completed'), (256, 'after_256_completed'), (300, 'after_300_completed')]
    assert [r['generation'] for r in boundary_aliases([state], 256)] == [0, 48, 128, 256]
    assert [r['generation'] for r in boundary_aliases([state], 20)] == [0, 20]
