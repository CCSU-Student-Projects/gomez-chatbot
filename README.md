This is a prototype Retrieval-Augmented Generation (RAG) application developed for Central Connecticut State University IT. It is intended for internal use only. All responses are AI-generated and do not represent the views of any group, department, individual, or organization.

![Screenshot of CCSU RAG Application Running](sample/Screenshot%202025-07-08%20132307.png)

## Hardware Requirements

- **GPU:** Minimum 24GB VRAM (NVIDIA RTX 3090, A5000, or better recommended)
- **CPU:** 8-core modern processor recommended
- **RAM:** At least 32GB system memory
- **Storage:** SSD strongly recommended

## Installation

First, install the required dependencies listed in `requirements.txt`. The following example uses Anaconda to set up the Python environment:

```bash
conda create -n ccsu_rag_env python=3.10
conda activate ccsu_rag_env
pip install -r requirements.txt
```

Next, sign in to your HuggingFace account with access to the required language models. You may need to request access on the HuggingFace model pages. The models used are open source but gated to prevent unauthorized access.

**Models:**
- [Meta-Llama 3-8B](https://huggingface.co/meta-llama/Meta-Llama-3-8B)
- [Llama Guard-3-8B](https://huggingface.co/meta-llama/Llama-Guard-3-8B)

## Data Sources

A sample data source is included in the `data` folder. To add a new data source, place your files in a new folder inside the `data` directory.

**Supported file types:** `.docx`, `.pdf`, `.txt`

To process your data, run the chunker/embedd script:

```bash
python src/chunker/embedder.py --input_folder "data/input/new_data_source" --output_store "data/vector_db/new_data_source_vector_store"
```

This app utilizes sentence-transformers model all-MiniLM-L6-v2
More information here: [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

**Note:** FAISS-CPU is used for chunking. Please ensure your processor is capable.

## Usage

This application allows you to customize the AI assistant's personality. To do this, edit the `llm/personality_config.py` file.

```python
DEFAULT_SYSTEM_PROMPT = (
    f"You are a helpful assistant named {AGENT_NAME} representing ...\n"
    "Answer questions about ... "
    "Be respectful, kind, ..."
)
# ...
```

Adjust the prompt as needed to change the assistant's tone or behavior.

**Application entry point:** `tui1.py`