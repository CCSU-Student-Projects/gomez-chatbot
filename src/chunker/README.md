# Document Chunker Module

This directory contains utilities for chunking documents into smaller pieces suitable for processing with LLMs and vector databases.

## Files

- `document_chunker.py` - Implementation of document chunking algorithms

## Usage

Import the DocumentChunker class to split documents into smaller chunks:

```python
from src.chunker.document_chunker import DocumentChunker

chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
chunks = chunker.chunk_text("Your long document text here...")
```
