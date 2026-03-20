import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

class LlamaGuardAPI:
    def __init__(self, use_pipeline=True, use_gpu=True):
        self.model_name = "meta-llama/Llama-Guard-3-8B"
        self.use_pipeline = use_pipeline
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = 0 if self.use_gpu else -1

        if use_pipeline:
            self.pipe = pipeline("text-generation", model=self.model_name, device=self.device)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

    def generate_response(self, messages):
        if self.use_pipeline:
            return self.pipe(messages)
        else:
            # For direct model/tokenizer use, expects a string prompt
            prompt = messages if isinstance(messages, str) else messages[0]["content"]
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=128)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
