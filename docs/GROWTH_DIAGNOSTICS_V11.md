# V11 diagnostic details fixed during training

These clarify the preregistered growth/cost audit before final maze generation. They do not change genomes,breeding,fitness,gate,primary model selection or inference.

Every mutated child is reconstructed independently from packed parent instructions and its concrete trace. The auditor checks the old seven-mode insertion/duplication/deletion eligibility and fallback,operand-only field changes,copy bounds,typed rows and arm ceiling,then compares full instruction bytes. An independent400-trace fuzz check across both ceilings passes. Packed arrays are released before raster audits; audit RSS is reported separately from inference/main RSS.

For newly born children whose parent is evaluated on the SAME rotating training batch,record gene growth,old128-boundary crossing,observed behavior equality,fitness excluding cost,work change and completed-tick change. This is a conditional matched-parent subset,not an unbiased neutrality estimate or randomized grown-versus-small comparison. Full hidden trajectories and per-gene causal influence are not identified by binary raster/aggregate score equality.

An extra exact-work regression at256 genes executes identity scratch copies on a3×3 open fixture. It verifies normal quiescence,all8-channel probe states,readonly production programs,exact dispatches,program-memory increment,zero completed ticks after instruction/read interruption,and charged attempted nonlocal reads under ablation. This is a runtime bound test,not a maze experiment. Source/test output are preserved in `limits_verification.json`;no production seed or final test input is used.
