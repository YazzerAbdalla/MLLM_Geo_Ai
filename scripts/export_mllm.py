import os
import json
import torch

from app.infrastructure.mllm_trainer import MllmTrainer


class MllmExporter:

    def __init__(self, export_dir="models/exported"):
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)

    # -------------------------
    # PT EXPORT
    # -------------------------
    def export_pt(self, model, filename="model.pt"):

        path = os.path.join(
            self.export_dir,
            filename
        )

        torch.save(
            model.state_dict(),
            path
        )

        print(f"✔ PT saved: {path}")

        return path

    # -------------------------
    # ONNX EXPORT
    # -------------------------
    def export_onnx(self, model, filename="model.onnx"):

        path = os.path.join(
            self.export_dir,
            filename
        )

        model.eval()

        dummy_input = torch.randint(
            0,
            100,
            (1, 16)
        )

        torch.onnx.export(
            model,
            (dummy_input,),
            path,
            opset_version=17,
            input_names=["input_ids"],
            output_names=["logits"],
            dynamic_axes={
                "input_ids": {
                    0: "batch",
                    1: "sequence"
                }
            }
        )

        print(f"✔ ONNX saved: {path}")

        return path

    # -------------------------
    # GGUF PLACEHOLDER
    # -------------------------
    def export_gguf(self, filename="model.gguf"):

        path = os.path.join(
            self.export_dir,
            filename
        )

        with open(path, "w") as f:
            f.write("GGUF export placeholder")

        print(f"✔ GGUF placeholder: {path}")

        return path

    # -------------------------
    # MODEL CARD
    # -------------------------
    def export_model_card(
        self,
        filename="model_card.json"
    ):

        card = {
            "architecture": "TinyGPT2 + LoRA",
            "dataset": "multimodal_embeddings",
            "metrics": {},
            "fusion_config": {
                "attention": True
            }
        }

        path = os.path.join(
            self.export_dir,
            filename
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                card,
                f,
                indent=4
            )

        print(f"✔ Model Card: {path}")

        return path


# -------------------------
# MAIN TEST
# -------------------------
if __name__ == "__main__":

    trainer = MllmTrainer()

    exporter = MllmExporter()

    exporter.export_pt(
        trainer.model,
        "mllm_lora.pt"
    )

    try:

        exporter.export_onnx(
            trainer.model,
            "mllm_lora.onnx"
        )

    except Exception as e:

        print(
            "ONNX export skipped:",
            e
        )

    exporter.export_gguf(
        "mllm_lora.gguf"
    )

    exporter.export_model_card()

    print("DONE")