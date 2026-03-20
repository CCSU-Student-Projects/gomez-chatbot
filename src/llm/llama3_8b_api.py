'''
Llama3_8B_API

This module provides an interface for generating responses using 
Llama 3 8B Instruct model. It handles prompt formatting in the correct 
chat template format and processes responses to extract only the assistant's
reply.

Stefan Louis
CCSU InfoServ AI Support Team
st_sl6361@ccsu.edu
Date: 6/24/2025
'''
from transformers import pipeline, AutoTokenizer
import torch

class Llama3_8B_API:
    def __init__(self, model_name="meta-llama/Meta-Llama-3-8B-Instruct"):
        self.device = 0 if torch.cuda.is_available() else -1
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.pipe = pipeline(
            "text-generation",
            model=model_name,
            tokenizer=self.tokenizer,
            device_map="auto",
            torch_dtype=torch.float16,
            pad_token_id=self.tokenizer.eos_token_id
        )

    def format_prompt(self, messages):
        system_prompt = "You are a helpful assistant." # Default system prompt
        for msg in messages:
            if msg.get('role') == 'system':
                system_prompt = msg.get('content')
                break
                
        prompt = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
        prompt += system_prompt + "<|eot_id|>\n"
        
        # Add all non-system messages
        for m in messages:
            if m.get('role') != 'system':
                role = m['role']
                prompt += f"<|start_header_id|>{role}<|end_header_id|>\n{m['content']}<|eot_id|>\n"
                
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n"
        return prompt
        
    def generate_response(self, messages):
        formatted_prompt = self.format_prompt(messages)
        
        outputs = self.pipe(formatted_prompt, max_new_tokens=400, do_sample=True, temperature=0.45)
        response = outputs[0]['generated_text']
        assistant_prefix = "<|start_header_id|>assistant<|end_header_id|>\n"
        if assistant_prefix in response:
            response = response.split(assistant_prefix)[-1].strip()
        return response

    def unload_model(self):
        self.pipe = None
        self.model = None
        self.tokenizer = None
