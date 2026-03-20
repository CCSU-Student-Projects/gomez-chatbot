"""
Document Chunker for RAG Application

This module provides functionality for loading and chunking documents (PDF, DOCX)
into smaller pieces suitable for processing with LLMs and vector databases.
Uses LangChain for document loading and semantic text splitting.

Created by: Stefan Louis
Date: 6/24/2025
"""

import os
from typing import List, Dict, Any
from pathlib import Path

from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredWordDocumentLoader,
    DirectoryLoader
)
from langchain.schema import Document

class DocumentChunker:
    def __init__(
        self,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        emb = HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": False} # Set true for cosine similarity
        )
        # Using semantic chunking. TODO test on larger datasets.
        self.text_splitter = SemanticChunker(
            embeddings=emb,
            buffer_size=1,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95.0
        )

    def _get_loader_for_file(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return PyPDFLoader(file_path)
        elif ext == ".docx":
            return Docx2txtLoader(file_path)
        elif ext == ".doc":
            return UnstructuredWordDocumentLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def load_and_split_document(self, file_path: str) -> List[Document]:
        loader = self._get_loader_for_file(file_path)
        documents = loader.load()
        return self.text_splitter.split_documents(documents)

    def load_and_split_directory(self, directory_path: str, glob_pattern: str = "**/*.*") -> List[Document]:
        loader = DirectoryLoader(
            directory_path,
            glob=glob_pattern,
            loader_cls=lambda fp: self._get_loader_for_file(fp)
        )
        documents = loader.load()
        return self.text_splitter.split_documents(documents)

    def get_document_metadata(self, file_path: str) -> Dict[str, Any]:
        stats = os.stat(file_path)
        return {
            "source": file_path,
            "filename": os.path.basename(file_path),
            "file_type": os.path.splitext(file_path)[1].lower(),
            "file_size": stats.st_size,
            "creation_date": stats.st_ctime,
            "modification_date": stats.st_mtime
        }

    def process_document_for_rag(self, file_path: str) -> List[Dict[str, Any]]:
        metadata = self.get_document_metadata(file_path)
        chunks = self.load_and_split_document(file_path)

        rag_chunks = []
        for i, chunk in enumerate(chunks):
            rag_chunks.append({
                "text": chunk.page_content,
                "metadata": {
                    **metadata,
                    **chunk.metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })
        return rag_chunks

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python document_chunker.py <path_to_document>")
        return

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    chunker = DocumentChunker()
    try:
        chunks = chunker.process_document_for_rag(file_path)
        print(f"Successfully processed document: {os.path.basename(file_path)}")
        print(f"Total chunks created: {len(chunks)}")
        if chunks:
            sample = chunks[0]
            print("\nSample chunk:")
            print(sample["text"][:150] + "...")
            print("Metadata:", sample["metadata"])
    except Exception as e:
        print("Error processing document:", str(e))

def test_chunker_on_data_folder():
    import glob
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data/unitree_research"

    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return

    patterns = ["*.pdf", "*.doc", "*.docx"]
    files = []
    for p in patterns:
        files.extend(data_dir.glob(p))

    if not files:
        print("No supported files found in the data directory.")
        return

    chunker = DocumentChunker()
    for file_path in files:
        print(f"\nProcessing: {file_path.name}")
        try:
            chunks = chunker.process_document_for_rag(str(file_path))
            print(f"  Chunks created: {len(chunks)}")
            
            for i, chunk in enumerate(chunks[:10]):
                print(f"\n--- Chunk {i+1} ---")
                print(f"Text ({len(chunk['text'])} chars):")
                print(chunk['text'])
                if i < len(chunks) - 1:
                    print("-" * 50)
                
        except Exception as e:
            print("  Error:", e)

def display_chunks_detailed(file_path, max_chunks=10):
    """
    Display chunks from a document in detail for inspection.
    
    Args:
        file_path (str): Path to the document file
        max_chunks (int): Maximum number of chunks to display
    """
    chunker = DocumentChunker()
    
    try:
        chunks = chunker.process_document_for_rag(file_path)
        print(f"\nDocument: {Path(file_path).name}")
        print(f"Total chunks: {len(chunks)}")
        print("=" * 80)
        
        for i, chunk in enumerate(chunks[:max_chunks]):
            print(f"\nCHUNK {i+1}/{len(chunks)}:")
            print(f"Length: {len(chunk['text'])} characters")
            print(f"Metadata: {chunk['metadata']}")
            print(f"Text:")
            print("-" * 40)
            print(chunk['text'])
            print("-" * 40)
            
            if i < min(max_chunks, len(chunks)) - 1:
                input("\nPress Enter to see next chunk...")
                
        if len(chunks) > max_chunks:
            print(f"\n... {len(chunks) - max_chunks} more chunks not shown")
            
    except Exception as e:
        print(f"Error processing document: {e}")

if __name__ == "__main__":
    test_chunker_on_data_folder()
