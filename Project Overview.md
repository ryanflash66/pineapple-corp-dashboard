# Project Overview

## Full Title
**AI-Driven Incident Response: Dynamic Playbook Adaptation with RAG**

## Goal
Fine-tune a Llama 3.1 8B model on incident response data to dynamically generate and adapt IR playbooks. The system uses RAG (Retrieval-Augmented Generation) to inject live threat intel context into playbook generation at inference time.

## Presentation
- RCAW Poster (36x48) 
- Google Doc research paper in progress

---

## Development Environment Setup
> **Note:** You are NOT running in a standard Colab browser environment. 

- **Code editor / agent host:** VS Code running locally on Windows
- **Compute:** Google Colab Pro GPU, connected to VS Code via the Colab remote kernel (Jupyter extension or colabcode/jupyter tunnel)
- **File system:** Local machine — files live persistently on disk. No re-uploading to Colab session storage each run.

---

## Current Notebook State

- Notebook saved to Drive: [Colab Notebook](https://colab.research.google.com/drive/1GT9SHVCIzgHgwOuI9B_K_N_ag0zfHKUS)
- All cells have already been edited. Current state of key cells:

### Model Load Cell
```python
from unsloth import FastLanguageModel
import torch

max_seq_length = 2048
dtype = None          # auto-detect (Float16 for T4)
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Llama-3.1-8B",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
```

### LoRA Config Cell
```python
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)
```

### Data Prep Cell (current — needs path update per above)
```python
alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

EOS_TOKEN = tokenizer.eos_token

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }

from datasets import load_dataset
dataset = load_dataset("json", data_files="/content/ir_playbooks_alpaca.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched=True,)
```

### Training Config Cell
```python
from trl import SFTConfig, SFTTrainer

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    packing = False,
    args = SFTConfig(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        num_train_epochs = 1,          # Full training run
        # max_steps = 60,              # Commented out
        learning_rate = 2e-4,
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.001,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
        report_to = "none",
    ),
)

trainer_stats = trainer.train()
```

### Inference Test Cell
```python
FastLanguageModel.for_inference(model)
inputs = tokenizer([
    alpaca_prompt.format(
        "Generate an incident response playbook for the following security incident.",
        "Ransomware detected on multiple Windows servers in the finance department. Lateral movement suspected via SMB. Several workstations have encrypted files.",
        "",  # leave blank for generation
    )
], return_tensors="pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens=256, use_cache=True)
tokenizer.batch_decode(outputs)
```

### Save Cell
```python
model.save_pretrained("ir_assistant_lora")      # saves LoRA adapters locally
tokenizer.save_pretrained("ir_assistant_lora")
```

---

## Dataset Reference

| Dataset | Source | Status | Purpose |
|---------|--------|--------|---------|
| `ir_playbooks_alpaca.jsonl` | Local file on your machine | Primary — in use | Core training data in Alpaca format |
| `Ryanflash/incident_response` | HuggingFace | Supplementary | Additional IR coverage |
| `cyberprince/incident-response-playbook-dataset` | Kaggle | Supplementary | High-level IR playbook steps |
| MITRE ATT&CK STIX 2.1 JSON | github.com/mitre-attack/attack-stix-data | Planned | Techniques, mitigations, detection notes |
| LOTL APT dataset | Kaggle | Planned | Attack command + ATT&CK label pairs |

---

## Future Roadmap (not yet implemented)

- **RAG Layer** — Vector store (Chroma or FAISS) to inject live MITRE ATT&CK / threat intel context at inference time
- **GRPO Training** — Upgrade from SFT to Group Relative Policy Optimization (`GRPOTrainer` in Unsloth) for RL-style IR planning
- **Dataset Merging** — Combine `ir_playbooks_alpaca.jsonl` + Ryanflash/incident_response + MITRE STIX into one unified Alpaca dataset
- **Local GPU Migration** — Move training/inference to RTX 4090 or RTX 5070 when available (Unsloth supports local installs)
- **API Wrapping** — FastAPI service exposing the fine-tuned model for an IR dashboard
- **Asset Visibility Layer (Future)** — Integrate read-only connectors to CMDB/EDR/SIEM/cloud inventory to maintain near-real-time asset context (hosts, users, services, network segments, criticality, owner, exposure) for incident-specific playbook adaptation.

  **Planned scope:**
  - Ingest from sources like AD/Entra, EDR, vulnerability scanners, cloud inventory APIs.
  - Normalize to a unified asset schema and refresh on a scheduled + event-driven basis.
  - Expose asset context to the RAG pipeline for grounded response generation.
  - Enforce least-privilege, RBAC, and audit logging (read-only by default).

---

## Key Links

| Resource | URL |
|----------|-----|
| Training notebook (Drive) | [Link](https://colab.research.google.com/drive/1GT9SHVCIzgHgwOuI9B_K_N_ag0zfHKUS) |
| Research doc (Google Docs) | [Link](https://docs.google.com/document/d/197bvVxCDAhXds60BTqcHrG7CRxzimpStCnhCWa1PCAQ) |
| RCAW Poster (Slides) | [Link](https://docs.google.com/presentation/d/1wcgoBRg4HSjGuzObfIhrhwfGDx3_dOfUaifFQbReisg) |
| NotebookLM project | [Link](https://notebooklm.google.com/notebook/3d3789a0-0dfb-49c1-a06b-2b90d72494e7) |
| HF Dataset (IR) | [Link](https://huggingface.co/datasets/Ryanflash/incident_response) |
| Kaggle IR Playbooks | [Link](https://www.kaggle.com/datasets/cyberprince/incident-response-playbook-dataset) |
| Unsloth Docs | [Link](https://unsloth.ai/docs) |

---

## Immediate First Actions for Agent

1. **Locate `ir_playbooks_alpaca.jsonl`** on the local filesystem and note the full path.
2. **Choose mount strategy** — Google Drive mount (recommended) or direct local path via VS Code tunnel.
3. **Update the Data Prep cell** `data_files=` argument with the correct path.
4. **Verify VS Code ↔ Colab connection** is live (T4 GPU available, runtime connected).
5. **Run all cells top to bottom** — watch for dataset load errors first before training starts.
6. **Inspect 5 sample rows** from the dataset before training to confirm `instruction/input/output` keys are present.
7. **Monitor training loss** — should trend from ~1.8 → ~0.85 over the full epoch.
8. **Run inference test cell** with the ransomware prompt after training to validate output quality.
9. **Save adapter** to `ir_assistant_lora/` — this persists locally on your machine automatically.
