# LLM Module

This directory contains implementations of various Large Language Model (LLM) APIs used in the application.

## Files

- `llama3_8b_api.py` - Implementation of the Meta-Llama-3-8B-Instruct model API
- `llama_guard_api.py` - Implementation of the Llama-Guard-3-8B model API for content moderation

## Usage

Import the appropriate API class based on your needs:

```python
from src.llm.llama3_8b_api import Llama3_8B_API
from src.llm.llama_guard_api import LlamaGuardAPI
```

Use a provided dictionary format to store conversation messages and call generate_response to use the model:

```python
conversation_messages = [
    {"role": "user", "content": "Hello, how can I reset my password?"},
    {"role": "assistant", "content": "To reset your password, please visit the IT portal and follow the instructions."}
]
response = generate_response(conversation_messages)
```
Use `tui1.py` as a basis for your implementation.