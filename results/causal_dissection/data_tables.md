# V12V saved-result tables

Synthetic variants are diagnostic probes, not evolutionary discoveries. Poses and graph/prefix variants within a context are correlated.

| Model | Kind | Genes | All pairs | Positive pairs | Corridors | Ordinary shortest | Explicit no-path |
|---|---|---:|---:|---:|---:|---:|---:|
| d00 | historical_random_origin | 254 | 20/1728 | 0/1440 | 58/1152 | 51/384 | 0/1088 |
| d01 | historical_random_origin | 253 | 20/1728 | 0/1440 | 58/1152 | 51/384 | 0/1088 |
| d02 | historical_random_origin | 253 | 608/1728 | 344/1440 | 1152/1152 | 82/384 | 0/1088 |
| d07 | historical_random_origin | 256 | 608/1728 | 344/1440 | 1152/1152 | 82/384 | 0/1088 |
| d08 | historical_random_origin | 256 | 560/1728 | 320/1440 | 1056/1152 | 82/384 | 0/1088 |
| d12 | historical_random_origin | 255 | 560/1728 | 320/1440 | 1056/1152 | 82/384 | 0/1088 |
| fresh2 | historical_random_origin | 160 | 192/1728 | 96/1440 | 1152/1152 | 16/384 | 8/1088 |
| fresh2_root | historical_random_origin | 119 | 0/1728 | 0/1440 | 0/1152 | 0/384 | 8/1088 |
| carry1 | historical_random_origin | 255 | 365/1728 | 198/1440 | 1029/1152 | 17/384 | 8/1088 |
| broad_root | historical_random_origin | 256 | 0/1728 | 0/1440 | 76/1152 | 72/384 | 0/1088 |
| random68 | historical_random_origin | 68 | 192/1728 | 96/1440 | 1152/1152 | 0/384 | 8/1088 |
| intact | known_control | 30 | 1728/1728 | 1440/1440 | 1152/1152 | 384/384 | 1088/1088 |
| dest_only | synthetic_mechanistic_probe | 254 | 608/1728 | 344/1440 | 1152/1152 | 82/384 | 0/1088 |
| d07_no_store | synthetic_mechanistic_probe | 256 | 560/1728 | 320/1440 | 1056/1152 | 82/384 | 0/1088 |
| d12_restore_store | synthetic_mechanistic_probe | 255 | 32/1728 | 8/1440 | 72/1152 | 76/384 | 0/1088 |
| d12_no_store | synthetic_mechanistic_probe | 255 | 560/1728 | 320/1440 | 1056/1152 | 82/384 | 0/1088 |

| Contrast (before→after) | Positive pairs gained/lost | All pairs gained/lost | Masks changed | Stops changed |
|---|---:|---:|---:|---:|
| d00->d01 | +0/−0 | +0/−0 | 0 | 0 |
| d00->dest_only | +344/−0 | +589/−1 | 5788 | 4779 |
| d01->d02 | +344/−0 | +589/−1 | 5788 | 4779 |
| dest_only->d02 | +0/−0 | +0/−0 | 0 | 0 |
| d07->d07_no_store | +0/−24 | +0/−48 | 1502 | 596 |
| d07_no_store->d08 | +0/−0 | +0/−0 | 0 | 0 |
| d07->d08 | +0/−24 | +0/−48 | 1502 | 596 |
| d12->d12_no_store | +0/−0 | +0/−0 | 0 | 0 |
| d12_no_store->d12_restore_store | +0/−312 | +0/−528 | 5680 | 4586 |
| d12->d12_restore_store | +0/−312 | +0/−528 | 5680 | 4586 |
| d07->d12_restore_store | +0/−336 | +0/−576 | 5678 | 4374 |
| fresh2_root->fresh2 | +96/−0 | +192/−0 | 6072 | 5872 |
| broad_root->carry1 | +198/−0 | +365/−0 | 5820 | 5933 |

| Signal intervention | Predicted native reference | Exact full records | Matching masks/status/ticks |
|---|---|---:|---:|
| d00 / channel4_zero | dest_only | 2368/2368 | 2368/2368 |
| d01 / channel4_zero | d02 | 2368/2368 | 2368/2368 |
| dest_only / channel4_zero | dest_only | 2368/2368 | 2368/2368 |
| d02 / channel4_zero | d02 | 2368/2368 | 2368/2368 |
| d00 / channel4_restore | d00 | 2368/2368 | 2368/2368 |
| d01 / channel4_restore | d01 | 2368/2368 | 2368/2368 |
| dest_only / channel4_restore | d00 | 2368/2368 | 2368/2368 |
| d02 / channel4_restore | d01 | 2368/2368 | 2368/2368 |

All exceptions, including counter-only differences, are preserved in analysis.json.gz. No normalization removes work or memory differences from the full-record test.
