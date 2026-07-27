# Agent-C: Calibrated Qwen

Agent-C is the uncertainty/calibration agent in the R/D/C setup.

It uses the same Qwen base as Agent-R and Agent-D, but trains a LoRA adapter as a calibrated multiple-choice scorer:

```text
loss = CE(answer letter) + ece_weight * ECE(confidence, correctness)
```

After training, it fits one scalar temperature on held-out validation questions and saves it as `temperature.json`.

## Kaggle Inputs

Add these Kaggle datasets:

1. Your Qwen2.5-3B-Instruct base model folder.
2. Your `mmlu_pro_hard_subset.json` from `data_preparation`.

If Qwen is not auto-detected, pass `--model_path`.

## Run

```python
!CUDA_VISIBLE_DEVICES=0 python /kaggle/working/agent_c_calibration_fast.py \
  --model_path /kaggle/input/YOUR_QWEN_DATASET/qwen2-5-3b-instruct \
  --mmlu_json /kaggle/input/YOUR_MMLU_DATASET/mmlu_pro_hard_subset.json \
  --profile deadline
```

For a stronger run:

```python
!CUDA_VISIBLE_DEVICES=0 python /kaggle/working/agent_c_calibration_fast.py \
  --model_path /kaggle/input/YOUR_QWEN_DATASET/qwen2-5-3b-instruct \
  --mmlu_json /kaggle/input/YOUR_MMLU_DATASET/mmlu_pro_hard_subset.json \
  --profile balanced
```

## Outputs

```text
/kaggle/working/agent_c_v0/
  adapter_config.json
  adapter_model.safetensors
  tokenizer files
  temperature.json
  agent_c_meta.json
```

## Inference Rule

For each question:

1. Build the same chat prompt.
2. Get next-token logits for answer letters `A-J`.
3. Load `temperature.json`.
4. Compute `softmax(choice_logits / temperature)`.
5. Return:

```json
{"answer": "<argmax letter>", "confidence": <max probability>}
```

That output plugs directly into the disagreement scorer as Agent `C`.
