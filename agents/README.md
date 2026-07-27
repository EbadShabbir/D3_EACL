# Agents

The system uses three deliberately different roles:

- `agent_r/`: reasoning-focused training and GRPO refinement.
- `agent_d/`: domain-adaptive training for specialist knowledge.
- `agent_c/`: calibrated multiple-choice prediction and uncertainty.

Model weights and adapter archives are local artifacts and are excluded from
Git. Each training script documents its expected Kaggle inputs and outputs.
