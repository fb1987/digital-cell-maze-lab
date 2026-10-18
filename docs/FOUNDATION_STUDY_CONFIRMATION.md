# V12C confirmation implementation notes

The main protocol and search code were frozen in `74b2588` before training. The separately implemented confirmation/audit/report modules are prepared while the75-minute search runs; they cannot alter training or select against final layouts. Confirmation refuses to run before a hashed selection packet and completed search summary exist.

The elementary screening rule is operationalized as follows:within an origin/topology cohort, the primary evolved selection must have strictly more shortest outputs at distances≥2 than both matched resampling and its initial frozen selection. It must also have a complete shortest pair in at least two independent fresh base layouts. At least two of three replicates must meet both conditions. All group counts also report whether any versus every transformed pair succeeds. Secondary per-level archives stay secondary. This is an exploratory screen across four cohorts, with no p-value claim.

The independent grader implements raster connectivity/degrees, emission/no-path rules, shortest length and both partial scores separately from the selection evaluator. Differential tests cover empty/full/random/route rasters, all six stopping statuses, disconnected inputs and identical endpoints. It also matches41,472 saved V12B calibration rasters. Numba is used only to make this independent audit inexpensive; its code never enters candidate inference or training selection.

Eight rectangular transforms were constructed by cropping one wall row from an old V12A fixture for software geometry tests. These software-only9×8/8×9 layouts were created after search started, receive no candidate inference, and cannot overlap square training. Their manifest is saved under `results/foundation_confirmation_fixtures` and excluded before final generation. They add eight conservative exclusions beyond the search's17,748 prior layouts. This is a recorded software-fixture addition, not a training protocol change.

Optional post-hoc interventions reuse already selected successful non-adjacent final inputs. Remove the initial goal pulse, zero nonlocal read values, or both. Static goal flags remain when the pulse is removed; nonlocal reads keep their work charge when their values are zeroed. These tests characterize dependence on inputs, not new unseen accuracy or a search comparison. Save and independently grade every intervention raster, including an ordinary control replay. No retuning follows.

Figures use an optional isolated local Matplotlib environment, leaving the experiment environment untouched:

```bash
uv pip install --target output/plot-libs -r requirements-figures.txt
.venv/bin/python -m maze_evolution.foundation_study_confirm --out results/foundation_study
.venv/bin/python -m maze_evolution.foundation_study_audit --out results/foundation_study
.venv/bin/python -m maze_evolution.foundation_study_interventions --out results/foundation_study
.venv/bin/python -m maze_evolution.foundation_study_report --out results/foundation_study
PYTHONPATH=output/plot-libs .venv/bin/python tools/plot_foundation_study.py --out results/foundation_study
```
