"""A closed, typed instruction grammar; genomes are data, never Python code."""
from dataclasses import dataclass
from enum import IntEnum
import hashlib
import random

import numpy as np


class Op(IntEnum):
    COPY = 0
    CONST = 1
    ADD = 2
    SUB = 3
    MIN_POS = 4
    ARGMIN_POS = 5
    NEIGHBOR = 6
    MATCH_NEIGHBOR = 7
    EQ = 8
    AND = 9
    OR = 10
    NOT = 11
    MUX = 12
    STORE = 13


# Registers 0..3: frozen state; 4: open; 5: source; 6: goal; 7: one.
# Registers 8..23: transient scratch. Four state channels, output = channel 2.
SPECS = {
    Op.COPY: ((8, 23), (0, 23)),
    Op.CONST: ((8, 23), (0, 255)),
    Op.ADD: ((8, 23), (0, 23), (0, 23)),
    Op.SUB: ((8, 23), (0, 23), (0, 23)),
    Op.MIN_POS: ((8, 23), (0, 3)),
    Op.ARGMIN_POS: ((8, 23), (0, 3)),
    Op.NEIGHBOR: ((8, 23), (0, 3), (0, 3)),
    Op.MATCH_NEIGHBOR: ((8, 23), (0, 3), (0, 255), (0, 3)),
    Op.EQ: ((8, 23), (0, 23), (0, 23)),
    Op.AND: ((8, 23), (0, 23), (0, 23)),
    Op.OR: ((8, 23), (0, 23), (0, 23)),
    Op.NOT: ((8, 23), (0, 23)),
    Op.MUX: ((8, 23), (0, 23), (0, 23), (0, 23)),
    Op.STORE: ((0, 3), (0, 23)),
}


@dataclass(frozen=True)
class Gene:
    op: int
    dst: int
    a: int = 0
    b: int = 0
    c: int = 0

    def __post_init__(self):
        if type(self.op) not in (int, Op) or self.op not in SPECS:
            raise ValueError('Unknown instruction')
        args = (self.dst, self.a, self.b, self.c)
        spec = SPECS[self.op]
        for i, value in enumerate(args):
            low, high = spec[i] if i < len(spec) else (0, 0)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'Invalid operand {i}: {value!r}')

    def row(self):
        return [int(self.op), self.dst, self.a, self.b, self.c]


@dataclass(frozen=True)
class Genome:
    genes: tuple[Gene, ...]

    def __post_init__(self):
        if not isinstance(self.genes, tuple) or not 1 <= len(self.genes) <= 32:
            raise ValueError('Genome must contain 1..32 immutable genes')
        if any(not isinstance(g, Gene) for g in self.genes):
            raise ValueError('Expected typed genes')

    def array(self):
        return np.array([g.row() for g in self.genes], dtype=np.int32)

    @property
    def digest(self):
        # Explicit little endian representation for portable identities.
        data = self.array().astype('<i4', copy=False).tobytes()
        return hashlib.sha256(data).hexdigest()[:20]

    def to_dict(self):
        return {'version': 1, 'genes': [g.row() for g in self.genes]}

    @classmethod
    def from_dict(cls, value):
        if set(value) != {'version', 'genes'} or value['version'] != 1:
            raise ValueError('Unsupported genome schema')
        return cls(tuple(Gene(*row) for row in value['genes']))


def wavefront_genome():
    """29 primitive instructions: first-arrival memory + parent-linked tracing.

    Directions W/E/N/S have codes 1/2/3/4. All spatial reads are frozen.
    No global distance map, search routine or oracle is available to this code.
    """
    genes = [
        Gene(Op.MIN_POS, 8, 0),
        Gene(Op.ADD, 9, 8, 7),
        Gene(Op.AND, 10, 8, 4),
        Gene(Op.NOT, 12, 0),
        Gene(Op.AND, 10, 10, 12),
        Gene(Op.MUX, 11, 10, 9, 0),
        Gene(Op.STORE, 0, 11),
        Gene(Op.ARGMIN_POS, 13, 0),
        Gene(Op.MUX, 14, 10, 13, 1),
        Gene(Op.STORE, 1, 14),
        Gene(Op.AND, 15, 6, 0),
        Gene(Op.OR, 15, 15, 2),
    ]
    for direction, opposite in enumerate((2, 1, 4, 3)):
        genes.extend([
            Gene(Op.MATCH_NEIGHBOR, 16, 1, opposite, direction),
            Gene(Op.NEIGHBOR, 17, 2, direction),
            Gene(Op.AND, 16, 16, 17),
            Gene(Op.OR, 15, 15, 16),
        ])
    genes.append(Gene(Op.STORE, 2, 15))
    return Genome(tuple(genes))


def random_gene(rng):
    op = rng.choice(tuple(Op))
    args = [rng.randint(low, high) for low, high in SPECS[op]]
    if op == Op.CONST:
        args[1] = rng.randrange(5)
    args += [0] * (4 - len(args))
    return Gene(op, *args)


def random_genome(rng):
    # No wavefront scaffold. Guaranteed channel writes avoid inert missing stores.
    genes = [random_gene(rng) for _ in range(rng.randint(12, 28))]
    genes.extend(Gene(Op.STORE, channel, rng.randrange(24)) for channel in range(4))
    return Genome(tuple(genes))


def mutate(genome, rng, edits=1):
    genes = list(genome.genes)
    for _ in range(edits):
        index = rng.randrange(len(genes))
        mode = rng.randrange(5)
        if mode == 0 and len(genes) < 32:
            genes.insert(index, random_gene(rng))
        elif mode == 1 and len(genes) > 1:
            genes.pop(index)
        elif mode == 2:
            genes[index] = random_gene(rng)
        elif mode == 3:
            other = rng.randrange(len(genes))
            genes[index], genes[other] = genes[other], genes[index]
        else:
            row = genes[index].row()
            operand = rng.randrange(len(SPECS[row[0]]))
            low, high = SPECS[row[0]][operand]
            row[operand + 1] = rng.randint(low, high)
            genes[index] = Gene(*row)
    return Genome(tuple(genes))
