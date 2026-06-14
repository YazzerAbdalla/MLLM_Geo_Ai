import os
import torch
import torch.nn as nn
import torch.optim as optim

from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, TaskType


class MllmTrainer:

    def __init__(
        self,
        model_name="sshleifer/tiny-gpt2",
        lr=2e-4,
        device=None
    ):

        self.device = device or (
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # -----------------------
        # Tokenizer
        # -----------------------
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        # -----------------------
        # Base LLM (memory-safe)
        # -----------------------
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        )

        # -----------------------
        # LoRA config (AI-15)
        # -----------------------
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.1,
            task_type=TaskType.CAUSAL_LM
        )

        self.model = get_peft_model(
            self.model,
            lora_config
        )

        self.model.to(self.device)

        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=lr
        )

        print("✔ MllmTrainer initialized")

    # -----------------------
    # TRAIN STEP
    # -----------------------
    def train_step(self, input_ids, attention_mask, labels):

        input_ids = input_ids.to(self.device)
        attention_mask = attention_mask.to(self.device)
        labels = labels.to(self.device)

        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss

        loss.backward()
        self.optimizer.step()
        self.optimizer.zero_grad()

        return loss.item()

    # -----------------------
    # SAVE CHECKPOINT
    # -----------------------
    def save_checkpoint(self, path, epoch):

        os.makedirs(path, exist_ok=True)

        save_path = os.path.join(
            path,
            f"checkpoint_epoch_{epoch}.pt"
        )

        torch.save(
            self.model.state_dict(),
            save_path
        )

        print(f"✔ Saved checkpoint: {save_path}")