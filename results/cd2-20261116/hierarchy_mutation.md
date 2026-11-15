# Hierarchy mutation report (R1)

Required operators M1-M7: 943/943 mutants detected.

A mutant counts as detected if any detector rejects it. `invariants` counts only violations absent from the unmutated AST, so known-defect violations do not count as detections. `needs expectation`: consistency variant on an input without a Golden expectation (detectable only by an expectation).

| Operator | Inputs | Mutants | Detected | invariants | trace | golden | needs expectation |
|---|---|---|---|---|---|---|---|
| M1 drop_all_jobs | carddemo | 46 | 46 | 46 | 0 | 0 | 0 |
| M1 drop_all_jobs | golden | 33 | 33 | 33 | 0 | 0 | 0 |
| M1 drop_all_jobs | pending | 5 | 5 | 5 | 0 | 5 | 0 |
| M2 drop_step | carddemo | 119 | 119 | 119 | 0 | 0 | 0 |
| M2 drop_step | golden | 34 | 34 | 34 | 0 | 0 | 0 |
| M2 drop_step | pending | 11 | 11 | 11 | 0 | 11 | 0 |
| M3 move_step_to_job | pending | 3 | 3 | 3 | 0 | 3 | 0 |
| M4 move_dd_to_step | carddemo | 353 | 353 | 353 | 0 | 0 | 0 |
| M4 move_dd_to_step | pending | 16 | 16 | 16 | 0 | 16 | 0 |
| M5 change_exec_target | carddemo | 119 | 119 | 119 | 0 | 0 | 0 |
| M5 change_exec_target | golden | 33 | 33 | 33 | 0 | 0 | 0 |
| M5 change_exec_target | pending | 11 | 11 | 11 | 0 | 11 | 0 |
| M5c change_exec_target_everywhere | carddemo | 116 | 116 | 0 | 116 | 0 | 0 |
| M5c change_exec_target_everywhere | golden | 29 | 29 | 0 | 29 | 6 | 0 |
| M5c change_exec_target_everywhere | pending | 9 | 9 | 0 | 9 | 9 | 0 |
| M6 shift_data_boundary | carddemo | 68 | 68 | 68 | 0 | 0 | 0 |
| M6 shift_data_boundary | golden | 5 | 5 | 5 | 0 | 5 | 0 |
| M6 shift_data_boundary | pending | 2 | 2 | 2 | 0 | 2 | 0 |
| M6c shift_data_boundary_everywhere | carddemo | 68 | 68 | 68 | 0 | 0 | 0 |
| M6c shift_data_boundary_everywhere | golden | 5 | 5 | 5 | 0 | 5 | 0 |
| M6c shift_data_boundary_everywhere | pending | 2 | 2 | 2 | 0 | 2 | 0 |
| M7 shrink_job_span | carddemo | 46 | 46 | 46 | 0 | 0 | 0 |
| M7 shrink_job_span | golden | 33 | 33 | 33 | 0 | 0 | 0 |
| M7 shrink_job_span | pending | 6 | 6 | 6 | 0 | 6 | 0 |

Escaped mutants: 0
