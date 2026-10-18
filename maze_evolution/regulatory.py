"""Version 2 data grammar: eight channels, conditional expression and ranges.

V1 and its first experiment remain untouched. These larger bounds are a new
experimental condition, not evidence that more capacity necessarily helps.
"""
from dataclasses import dataclass
import hashlib

import numpy as np

from .genome import Op, wavefront_genome


REMOTE = 14
REMOTE_MIN = 15
XOR = 16
NEIGHBOR_COUNT = 17
NAMES = {**{int(op): op.name for op in Op}, REMOTE: 'REMOTE', REMOTE_MIN: 'REMOTE_MIN',
         XOR: 'XOR', NEIGHBOR_COUNT: 'NEIGHBOR_COUNT'}
ALWAYS = 64
# 0..7 frozen channels; 8=open, 9=source, 10=goal, 11=one; 12..63 scratch.
SPECS = {
    0: ((12, 63), (0, 63)), 1: ((12, 63), (0, 255)),
    2: ((12, 63), (0, 63), (0, 63)), 3: ((12, 63), (0, 63), (0, 63)),
    4: ((12, 63), (0, 7)), 5: ((12, 63), (0, 7)),
    6: ((12, 63), (0, 7), (0, 3)),
    7: ((12, 63), (0, 7), (0, 255), (0, 3)),
    8: ((12, 63), (0, 63), (0, 63)), 9: ((12, 63), (0, 63), (0, 63)),
    10: ((12, 63), (0, 63), (0, 63)), 11: ((12, 63), (0, 63)),
    12: ((12, 63), (0, 63), (0, 63), (0, 63)), 13: ((0, 7), (0, 63)),
    REMOTE: ((12, 63), (0, 7), (0, 3)), REMOTE_MIN: ((12, 63), (0, 7)),
    XOR: ((12, 63), (0, 63), (0, 63)), NEIGHBOR_COUNT: ((12, 63), (0, 7)),
}


@dataclass(frozen=True)
class Gene:
    op: int
    dst: int
    a: int = 0
    b: int = 0
    c: int = 0
    radius: int = 0
    gate: int = ALWAYS

    def __post_init__(self):
        if type(self.op) is not int or self.op not in SPECS:
            raise ValueError('Unknown V2 opcode')
        spec = SPECS[self.op]
        for i, value in enumerate((self.dst, self.a, self.b, self.c)):
            low, high = spec[i] if i < len(spec) else (0, 0)
            if type(value) is not int or not low <= value <= high:
                raise ValueError('Invalid V2 operand')
        if type(self.radius) is not int or not 0 <= self.radius <= 3:
            raise ValueError('Invalid radius')
        if self.op not in (REMOTE, REMOTE_MIN) and self.radius != 0:
            raise ValueError('Local primitives cannot acquire remote edges')
        if type(self.gate) is not int or not 0 <= self.gate <= ALWAYS:
            raise ValueError('Invalid expression gate')

    def row(self):
        return [self.op, self.dst, self.a, self.b, self.c, self.radius, self.gate]


@dataclass(frozen=True)
class Genome:
    genes: tuple[Gene, ...]

    def __post_init__(self):
        if not isinstance(self.genes, tuple) or not 1 <= len(self.genes) <= 128:
            raise ValueError('Expected 1..128 immutable V2 genes')
        if any(not isinstance(g, Gene) for g in self.genes):
            raise ValueError('Expected typed V2 genes')

    def array(self):
        return np.array([g.row() for g in self.genes], dtype=np.int32)

    @property
    def digest(self):
        return hashlib.sha256(self.array().astype('<i4', copy=False).tobytes()).hexdigest()[:20]

    def to_dict(self):
        return dict(version=2, genes=[g.row() for g in self.genes])

    @classmethod
    def from_dict(cls, value):
        if set(value) != {'version', 'genes'} or value['version'] != 2:
            raise ValueError('Expected V2 genome schema')
        return cls(tuple(Gene(*row) for row in value['genes']))


def seeded_genome():
    def register(old):
        return old if old < 4 else old + 4
    register_operands = {0: (1,), 1: (), 2: (1, 2), 3: (1, 2), 4: (), 5: (),
                        6: (), 7: (), 8: (1, 2), 9: (1, 2), 10: (1, 2),
                        11: (1,), 12: (1, 2, 3), 13: (1,)}
    result = []
    for gene in wavefront_genome().genes:
        args = gene.row()[1:]
        if gene.op != Op.STORE:
            args[0] = register(args[0])
        for i in register_operands[gene.op]:
            args[i] = register(args[i])
        result.append(Gene(int(gene.op), *args))
    # A heritable regulatory stop request, rather than stopping every broad mask.
    result.append(Gene(13, 7, register(15)))
    return Genome(tuple(result))


def random_gene(rng):
    op = rng.randrange(18)
    args = [rng.randint(low, high) for low, high in SPECS[op]]
    if op in (1, 7):
        args[1 if op == 1 else 2] = rng.randrange(9) if rng.random() < .9 else rng.randrange(256)
    args += [0] * (4 - len(args))
    radius = rng.randrange(4) if op in (REMOTE, REMOTE_MIN) else 0
    gate = ALWAYS if rng.random() < .75 else rng.randrange(64)
    return Gene(op, *args, radius, gate)


def random_genome(rng, rich=False):
    length = rng.randint(64, 128) if rich else rng.randint(24, 64)
    genes = [random_gene(rng) for _ in range(length - 8)]
    genes.extend(Gene(13, channel, rng.randrange(64), gate=ALWAYS if rng.random() < .75
                      else rng.randrange(64)) for channel in range(8))
    return Genome(tuple(genes))


def mutate(genome, rng, edits=1):
    genes = list(genome.genes)
    for _ in range(edits):
        index = rng.randrange(len(genes))
        mode = rng.randrange(7)
        if mode == 0 and len(genes) < 128:
            genes.insert(index, random_gene(rng))
        elif mode == 1 and len(genes) > 1:
            genes.pop(index)
        elif mode == 2:
            genes[index] = random_gene(rng)
        elif mode == 3:
            other = rng.randrange(len(genes))
            genes[index], genes[other] = genes[other], genes[index]
        elif mode == 4 and len(genes) < 128:
            block = genes[index:index + rng.randint(1, 8)][:128-len(genes)]
            genes[index:index] = block
        else:
            row = genes[index].row()
            options = list(range(1, 1 + len(SPECS[row[0]]))) + [6]
            if row[0] in (REMOTE, REMOTE_MIN):
                options.append(5)
            field = rng.choice(options)
            if field == 6:
                row[field] = ALWAYS if rng.random() < .5 else rng.randrange(64)
            elif field == 5:
                row[field] = rng.randrange(4)
            else:
                low, high = SPECS[row[0]][field - 1]
                row[field] = rng.randint(low, high)
            genes[index] = Gene(*row)
    return Genome(tuple(genes))
