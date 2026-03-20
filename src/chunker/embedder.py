"""
Embedder for RAG Application

This module provides functionality for creating embeddings from document chunks
and storing them in a vector database for efficient similarity search.

Created by: Stefan Louis
Date: 6/27/2025
"""

import os
import sys
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
import argparse

# Add the project root to the Python path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

# Try relative imports first, fall back to absolute imports
try:
    from .document_chunker import DocumentChunker
    from .gpu_config import GPUConfig, check_gpu_compatibility, optimize_gpu_memory
except ImportError:
    # Fallback for when running as standalone script
    from src.chunker.document_chunker import DocumentChunker
    from src.chunker.gpu_config import GPUConfig, check_gpu_compatibility, optimize_gpu_memory


class DocumentEmbedder:
    """
    Handles embedding creation and vector storage for RAG applications.
    """
    
    def __init__(
        self,
        embedding_model: str = None,
        vector_store_path: Optional[str] = None,
        use_gpu_config: bool = True
    ):
        """
        Initialize the document embedder.
        
        Args:
            embedding_model (str): HuggingFace embedding model name
            vector_store_path (str, optional): Path to save/load vector store
            use_gpu_config (bool): Whether to use GPU configuration settings
        """
        # Use GPU config if enabled and available
        if use_gpu_config:
            try:
                self.config = GPUConfig()
                self.embedding_model_name = embedding_model or self.config.EMBEDDING_MODEL
                device = self.config.get_embedding_device()
                
                # Try to optimize GPU memory
                optimize_gpu_memory()
            except Exception as e:
                print(f"GPU config not available: {e}")
                print("Falling back to CPU configuration...")
                self.config = None
                self.embedding_model_name = embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
                device = "cpu"
        else:
            self.config = None
            self.embedding_model_name = embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
            device = "cpu"
        
        # Check if CUDA is actually available
        try:
            import torch
            if device == "cuda" and not torch.cuda.is_available():
                print("CUDA requested but not available. Falling back to CPU.")
                device = "cpu"
        except ImportError:
            print("PyTorch not available. Using CPU.")
            device = "cpu"
        
        self.vector_store_path = vector_store_path or "vector_store"
        
        # Initialize embedding model
        print(f"Initializing embedding model: {self.embedding_model_name}")
        print(f"Device: {device}")
        
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True}
            )
        except Exception as e:
            print(f"Error initializing embeddings with device {device}: {e}")
            print("Trying CPU device...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        
        # Initialize vector store
        self.vector_store = None
        self.chunker = DocumentChunker()
        self.gpu_available = self._check_gpu_availability()
        
    def _check_gpu_availability(self) -> bool:
        """
        Check if GPU is available for both embeddings and FAISS.
        
        Returns:
            bool: True if GPU is available for both components
        """
        import torch
        
        torch_gpu = torch.cuda.is_available()
        faiss_gpu = False
        
        try:
            import faiss
            faiss_gpu = faiss.get_num_gpus() > 0
        except ImportError:
            pass
        except Exception:
            pass
            
        print(f"GPU Status:")
        print(f"  PyTorch CUDA: {'✓' if torch_gpu else '✗'}")
        print(f"  FAISS GPU: {'✓' if faiss_gpu else '✗'}")
        
        return torch_gpu and faiss_gpu
        
    def embed_documents(self, documents: List[Document]) -> FAISS:
        """
        Create embeddings for a list of documents and store in FAISS vector store.
        
        Args:
            documents (List[Document]): List of LangChain Document objects
            
        Returns:
            FAISS: Vector store containing embeddings
        """
        if not documents:
            raise ValueError("No documents provided for embedding")
            
        print(f"Creating embeddings for {len(documents)} documents using GPU...")
        
        # Create FAISS vector store from documents
        self.vector_store = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        
        # Move FAISS index to GPU for faster search
        self._move_index_to_gpu()
        
        print("Embeddings created successfully!")
        return self.vector_store
    
    def _move_index_to_gpu(self) -> None:
        """
        Move FAISS index to GPU for faster search operations.
        """
        # Check if GPU config allows FAISS GPU
        if self.config and not self.config.get_faiss_gpu_enabled():
            print("FAISS GPU disabled in configuration")
            return
            
        try:
            import faiss
            
            # Check if GPU is available
            if faiss.get_num_gpus() == 0:
                print("No GPUs available for FAISS. Using CPU index.")
                return
                
            # Check if vector store and index exist
            if self.vector_store is None or not hasattr(self.vector_store, 'index'):
                print("No vector store or index found to move to GPU")
                return
                
            # Move to GPU if not already there
            if not hasattr(self.vector_store.index, 'device') or self.vector_store.index.device < 0:
                print(f"Moving FAISS index to GPU (index size: {self.vector_store.index.ntotal} vectors)...")
                
                # Create GPU resources
                gpu_resources = faiss.StandardGpuResources()
                
                # Configure GPU index parameters for better performance
                gpu_config = faiss.GpuIndexFlatConfig()
                
                # Use configuration settings
                if self.config:
                    gpu_config.useFloat16 = self.config.FAISS_USE_FLOAT16
                    gpu_config.device = self.config.get_faiss_gpu_device()
                else:
                    gpu_config.useFloat16 = True
                    gpu_config.device = 0
                
                # Move index to GPU (using correct API signature)
                gpu_index = faiss.index_cpu_to_gpu(gpu_resources, gpu_config.device, 
                                                 self.vector_store.index)
                self.vector_store.index = gpu_index
                
                print(f"✓ FAISS index successfully moved to GPU {gpu_config.device}")
                print(f"  Using Float16: {gpu_config.useFloat16}")
            else:
                print("FAISS index is already on GPU")
                
        except ImportError:
            print("faiss-gpu not installed. Install with: pip install faiss-gpu")
        except Exception as e:
            print(f"Could not move FAISS to GPU: {e}")
            print("Continuing with CPU index...")
    
    def embed_document_chunks(self, file_path: str) -> FAISS:
        """
        Process a single document: chunk it and create embeddings.
        
        Args:
            file_path (str): Path to the document file
            
        Returns:
            FAISS: Vector store containing embeddings
        """
        print(f"Processing document: {os.path.basename(file_path)}")
        
        # Load and chunk the document
        chunks = self.chunker.load_and_split_document(file_path)
        print(f"Created {len(chunks)} chunks")
        
        # Create embeddings
        return self.embed_documents(chunks)
    
    def embed_directory(self, directory_path: str, patterns: List[str] = None) -> FAISS:
        """
        Process all documents in a directory and create embeddings.
        
        Args:
            directory_path (str): Path to directory containing documents
            patterns (List[str]): File patterns to match (default: ["*.pdf", "*.docx", "*.doc"])
            
        Returns:
            FAISS: Vector store containing embeddings from all documents
        """
        if patterns is None:
            patterns = ["*.pdf", "*.docx", "*.doc"]
            
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Find all matching files
        files = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))
            
        if not files:
            raise ValueError(f"No documents found in {directory_path}")
            
        print(f"Found {len(files)} documents to process")
        
        all_chunks = []
        for file_path in files:
            try:
                print(f"\nProcessing: {file_path.name}")
                chunks = self.chunker.load_and_split_document(str(file_path))
                print(f"  Created {len(chunks)} chunks")
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"  Error processing {file_path.name}: {e}")
                
        print(f"\nTotal chunks from all documents: {len(all_chunks)}")
        return self.embed_documents(all_chunks)
    
    def save_vector_store(self, path: Optional[str] = None) -> None:
        """
        Save the vector store to disk.
        
        Args:
            path (str, optional): Path to save the vector store
        """
        if self.vector_store is None:
            raise ValueError("No vector store to save. Create embeddings first.")
            
        save_path = path or self.vector_store_path
        self.vector_store.save_local(save_path)
        print(f"Vector store saved to: {save_path}")
    
    def load_vector_store(self, path: Optional[str] = None) -> FAISS:
        """
        Load a vector store from disk and move to GPU if available.
        
        Args:
            path (str, optional): Path to load the vector store from
            
        Returns:
            FAISS: Loaded vector store
        """
        load_path = path or self.vector_store_path
        
        if not os.path.exists(load_path):
            print(f"Fatal error: Vector store not found at: {load_path}", file=sys.stderr)
            sys.exit(1)
            
        print(f"Loading vector store from: {load_path}")
        self.vector_store = FAISS.load_local(
            load_path, 
            self.embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # Move to GPU after loading
        # self._move_index_to_gpu()
        
        print(f"Vector store loaded successfully!")
        return self.vector_store
    
    def search_similar(self, query: str, k: int = 5) -> List[Document]:
        """
        Search for similar documents using a text query.
        
        Args:
            query (str): Search query
            k (int): Number of similar documents to return
            
        Returns:
            List[Document]: Most similar documents
        """
        if self.vector_store is None:
            raise ValueError("No vector store loaded. Create or load embeddings first.")
            
        return self.vector_store.similarity_search(query, k=k)
    
    def search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """
        Search for similar documents with similarity scores.
        
        Args:
            query (str): Search query
            k (int): Number of similar documents to return
            
        Returns:
            List[tuple]: (Document, score) pairs
        """
        if self.vector_store is None:
            raise ValueError("No vector store loaded. Create or load embeddings first.")
            
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def embed_rag_chunks(self, rag_chunks: List[Dict[str, Any]]) -> FAISS:
        """
        Create embeddings from RAG-formatted chunks (from DocumentChunker.process_document_for_rag).
        
        Args:
            rag_chunks (List[Dict]): List of chunks from process_document_for_rag()
            
        Returns:
            FAISS: Vector store containing embeddings
        """
        if not rag_chunks:
            raise ValueError("No RAG chunks provided for embedding")
            
        # Convert RAG chunks to LangChain Documents
        documents = []
        for chunk in rag_chunks:
            doc = Document(
                page_content=chunk['text'],
                metadata=chunk['metadata']
            )
            documents.append(doc)
            
        return self.embed_documents(documents)

def main():
    """
    Example usage of the DocumentEmbedder.
    """
    import sys
    
    # Initialize embedder
    embedder = DocumentEmbedder()
    
    # Get project root and unitree_research directory
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data" / "unitree_research"
    
    if not data_dir.exists():
        print(f"Unitree research directory not found: {data_dir}")
        return
    
    try:
        # Load the existing vector store
        print("Loading existing vector store...")
        embedder.load_vector_store("unitree_vector_store")
        print(f"Vector store loaded successfully!")
        
        # # Embed all documents in the unitree_research directory (only if needed)
        # print("Creating embeddings for all Unitree research documents...")
        # vector_store = embedder.embed_directory(str(data_dir))
        
        # # Save the vector store (only if creating new embeddings)
        # embedder.save_vector_store("unitree_vector_store")
        
        # Test search functionality
        test_query = "How do I teleoperate a humanoid robot."
        print(f"\nTesting search with query: '{test_query}'")
        results = embedder.search_with_scores(test_query, k=3)
        
        for i, (doc, score) in enumerate(results):
            print(f"\nResult {i+1} (Score: {score:.4f}):")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"Text: {doc.page_content[:200]}...")
            
    except Exception as e:
        print(f"Error: {e}")

def generate_go2_robot_vector_store():
    """
    Generate a vector store for the go2_robot folder.
    """
    # Initialize embedder
    embedder = DocumentEmbedder()

    # Define the path to the go2_robot folder
    project_root = Path(__file__).resolve().parents[2]
    go2_robot_dir = project_root / "data" / "go2_robot"

    if not go2_robot_dir.exists():
        print(f"Error: Directory '{go2_robot_dir}' does not exist.")
        return

    try:
        # Process the go2_robot folder and create embeddings
        vector_store = embedder.embed_directory(str(go2_robot_dir))

        # Save the vector store
        vector_store_path = project_root / "unitree_vector_store" / "go2_robot_vector_store"
        embedder.save_vector_store(str(vector_store_path))
        print(f"Vector store for go2_robot saved to: {vector_store_path}")
    except Exception as e:
        print(f"Error generating vector store for go2_robot: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate vector database from documents.")
    parser.add_argument(
        "--input_folder",
        type=str,
        required=True,
        help="Path to the folder containing documents to process."
    )
    parser.add_argument(
        "--output_store",
        type=str,
        required=True,
        help="Path to save the generated vector store."
    )
    args = parser.parse_args()

    # Initialize the embedder
    embedder = DocumentEmbedder()

    # Process the input folder and save the vector store
    embedder.embed_directory(args.input_folder)
    embedder.save_vector_store(args.output_store)
    print(f"Vector store saved to: {args.output_store}")