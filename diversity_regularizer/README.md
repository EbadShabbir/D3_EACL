# Task 11 - Diversity regularizer

This module plugs into Task 10 and can also be imported inside future training
scripts.

Pure Python report:

```python
from task11_diversity_regularizer import DiversityRegularizer
score = DiversityRegularizer(weight=0.05, min_js_divergence=0.03).score_record(record)
```

Torch training loss:

```python
from task11_diversity_regularizer import torch_diversity_loss

loss = task_loss + torch_diversity_loss(
    {"R": r_choice_logits, "D": d_choice_logits, "C": c_choice_logits},
    weight=0.05,
    min_js_divergence=0.03,
)
```

The loss is zero when agents are already sufficiently different. It becomes
positive when their choice distributions collapse below the configured mean
Jensen-Shannon divergence floor.
