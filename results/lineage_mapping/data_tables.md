# V12U data tables

Generated from saved native emissions; no candidate calls. Poses/variants are correlated.

| Identity | Genes | All pairs /1152 | Positive pairs /960 | All-eight-pose groups | Corridors /768 | Ordinary trees /192 | Ordinary cyclic /192 | No-path /768 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| d00 | 254 | 10 | 0 | 0 | 38 | 12 | 9 | 0 |
| d01 | 253 | 10 | 0 | 0 | 38 | 12 | 9 | 0 |
| d02 | 253 | 420 | 238 | 42 | 768 | 36 | 20 | 0 |
| d03 | 256 | 420 | 238 | 42 | 768 | 36 | 20 | 0 |
| d04 | 256 | 420 | 238 | 42 | 768 | 36 | 20 | 0 |
| d05 | 256 | 420 | 238 | 42 | 768 | 36 | 20 | 0 |
| d06 | 256 | 420 | 238 | 42 | 768 | 36 | 20 | 0 |
| d07 | 256 | 420 | 238 | 42 | 768 | 36 | 20 | 0 |
| d08 | 256 | 392 | 224 | 28 | 720 | 36 | 20 | 0 |
| d09 | 256 | 392 | 224 | 28 | 720 | 36 | 20 | 0 |
| d10 | 255 | 392 | 224 | 28 | 720 | 36 | 20 | 0 |
| d11 | 255 | 392 | 224 | 28 | 720 | 36 | 20 | 0 |
| d12 | 255 | 392 | 224 | 28 | 720 | 36 | 20 | 0 |
| fresh2 | 160 | 128 | 64 | 16 | 768 | 0 | 8 | 0 |
| fresh2_root | 119 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| carry1 | 255 | 228 | 126 | 4 | 683 | 2 | 8 | 0 |
| broad_root | 256 | 0 | 0 | 0 | 56 | 34 | 20 | 0 |
| random68 | 68 | 128 | 64 | 16 | 768 | 0 | 0 | 0 |
| intact | 30 | 1152 | 960 | 144 | 768 | 192 | 192 | 768 |

All-eight-pose groups include prefix0; inspect metrics for prefix-specific success.

| Edit | Kind/index (zero-based) | Previous gene | New gene | Positive pairs gained/lost | Masks changed | Stops changed |
|---|---|---|---|---:|---:|---:|
| d01 | delete /251 | OR [10, 34, 38, 49, 0, 0, 64] | delete | +0/−0 | 0 | 0 |
| d02 | operand /103 | REMOTE_MIN [15, 44, 3, 0, 0, 3, 64] | REMOTE_MIN [15, 32, 3, 0, 0, 3, 64] | +238/−0 | 4044 | 3277 |
| d03 | duplicate /140 | CONST [1, 44, 4, 0, 0, 0, 64] | duplicate 3 genes | +0/−0 | 82 | 162 |
| d04 | operand /229 | OR [10, 63, 13, 15, 0, 0, 64] | OR [10, 63, 7, 15, 0, 0, 64] | +0/−0 | 0 | 0 |
| d05 | replace /88 | ADD [2, 13, 30, 45, 0, 0, 64] | COPY [0, 38, 58, 0, 0, 0, 64] | +0/−0 | 0 | 0 |
| d06 | replace /132 | ADD [2, 36, 63, 34, 0, 0, 64] | NOT [11, 56, 36, 0, 0, 0, 24] | +0/−0 | 0 | 0 |
| d07 | operand /161 | SUB [3, 41, 39, 27, 0, 0, 46] | SUB [3, 41, 39, 27, 0, 0, 64] | +0/−0 | 0 | 0 |
| d08 | replace /222 | STORE [13, 2, 58, 0, 0, 0, 18] | EQ [8, 34, 40, 39, 0, 0, 64] | +0/−14 | 1000 | 322 |
| d09 | replace /132 | NOT [11, 56, 36, 0, 0, 0, 24] | NEIGHBOR_COUNT [17, 45, 6, 0, 0, 0, 64] | +0/−0 | 224 | 224 |
| d10 | delete /106 | REMOTE_MIN [15, 62, 5, 0, 0, 2, 64] | delete | +0/−0 | 224 | 224 |
| d11 | replace /233 | STORE [13, 2, 26, 0, 0, 0, 59] | AND [9, 35, 28, 4, 0, 0, 64] | +0/−0 | 0 | 0 |
| d12 | replace /206 | COPY [0, 18, 25, 0, 0, 0, 12] | OR [10, 51, 63, 54, 0, 0, 39] | +0/−0 | 0 | 0 |

Gene fields: opcode, destination, operand a, operand b, operand c, radius, gate. Gate64 means always. Local topology remains fixed, including for REMOTE_MIN. Edits are interpreted in their historical parent, not transplanted into the root.

| Identity | Normal pairs /96 | Pulse-off retained | Flag-off retained | Output-read-off retained | Halt-request-off retained |
|---|---:|---:|---:|---:|---:|
| d00 | 0 | 0 | 0 | 0 | 0 |
| d01 | 0 | 0 | 0 | 0 | 0 |
| d02 | 48 | 48 | 0 | 0 | 0 |
| d03 | 48 | 48 | 0 | 0 | 0 |
| d04 | 48 | 48 | 0 | 0 | 0 |
| d05 | 48 | 48 | 0 | 0 | 0 |
| d06 | 48 | 48 | 0 | 0 | 0 |
| d07 | 48 | 48 | 0 | 0 | 0 |
| d08 | 48 | 48 | 0 | 0 | 0 |
| d09 | 48 | 48 | 0 | 0 | 0 |
| d10 | 48 | 48 | 0 | 0 | 0 |
| d11 | 48 | 48 | 0 | 0 | 0 |
| d12 | 48 | 48 | 0 | 0 | 0 |
| fresh2 | 16 | 16 | 0 | 16 | 0 |
| carry1 | 25 | 25 | 16 | 0 | 0 |
| intact | 96 | 96 | 0 | 0 | 96 |

Retention is conditional on normal successes in the fixed diagnostic subset. New diagnostic successes are separately preserved in analysis.json.gz. Interventions apply to all subset inputs, without success filtering.
