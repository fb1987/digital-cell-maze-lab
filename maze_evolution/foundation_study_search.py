"""V12C ordinary-output search with validation-only elementary skill archives."""
import json

from .foundation_repair_search import MutationSearch


def level_rows(rows, level):
    return [r for r in rows if f'/level{level}/' in r['case']]


def skill_rank(rows):
    work = sum(r['dispatches'] + r['reads'] for r in rows)
    return (sum(r['valid'] for r in rows), sum(r['optimal'] for r in rows),
            sum(r['pair_optimal'] for r in rows) // 2,
            round(sum(r['partial'] + r['paired_partial'] for r in rows), 8),
            -work if all(r['optimal'] for r in rows) else 0)


def certified_levels(rates):
    return [level for level in range(4) if rates.get(str(level), 0) >= .9
            and all(rates.get(str(j), 0) >= .8 for j in range(level))]


class SkillSearch(MutationSearch):
    def __init__(self, *args, **kwargs):
        self.skills, self.frozen_skills, self.competence = {}, {}, {}
        super().__init__(*args, **kwargs)
        if kwargs.get('resume', False):
            state = json.loads(self.checkpoint.read_text())
            for key in ('skills', 'frozen_skills', 'competence'):
                setattr(self, key, state[key])

    def evaluate(self, item, pairs, split, generation):
        ev = super().evaluate(item, pairs, split, generation)
        if split.startswith('validation'):
            rates = {}
            for level in range(4):
                rows = level_rows(ev.rows, level)
                if not rows:
                    continue
                rank = skill_rank(rows)
                key = str(level)
                if key not in self.skills or rank > tuple(self.skills[key]['rank']):
                    self.skills[key] = dict(item=item.save(), rank=rank, rows=rows, generation=generation)
                rates[key] = sum(r['pair_optimal'] for r in rows) / len(rows)
            # All retention thresholds must be met by this same candidate.
            for level in certified_levels(rates):
                key = str(level)
                self.competence.setdefault(key, dict(id=item.identity, generation=generation, rates=rates))
        return ev

    def initialize(self, validation):
        if self.champion is not None:
            return
        super().initialize(validation)
        self.frozen_skills = json.loads(json.dumps(self.skills))
        self.force_save()

    def state(self):
        return dict(**super().state(), skills=self.skills, frozen_skills=self.frozen_skills,
                    competence=self.competence)

    def save(self):
        # Full RNG/population checkpoints at each completed orchestration round.
        # The orchestrator forces all saves before its atomic round marker.
        if not self.config.get('round_checkpoint', False):
            super().save()

    def force_save(self):
        super().save()

    def selection(self):
        return dict(config=self.config, next_generation=self.next_generation,
            champion=self.champion.save(), frozen=self.frozen.save(),
            champion_rank=self.champion_rank, frozen_rank=self.frozen_rank,
            skills=self.skills, frozen_skills=self.frozen_skills, competence=self.competence,
            initial_digests=self.initial_digests, responses=self.responses, work=self.work)
