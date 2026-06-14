from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM

model_name = "distilgpt2"

tokenizer = AutoTokenizer.from_pretrained(
    model_name
)

model = AutoModelForCausalLM.from_pretrained(
    model_name
)

print("Model Loaded")
print(model.config.hidden_size)