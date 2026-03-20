"""
GPU Configuration for RAG Pipeline

This module contains GPU-specific settings and utilities for optimal performance
in the RAG pipeline with FAISS-GPU and HuggingFace embeddings.
"""

import os
from typing import Dict, Any, Optional


class GPUConfig:
    """Configuration class for GPU settings in RAG pipeline."""
    
    # FAISS GPU Settings
    FAISS_GPU_ENABLED = True
    FAISS_GPU_DEVICE = 0  # Use first GPU
    FAISS_USE_FLOAT16 = True  # Use half precision for memory efficiency
    
    # Embedding Model Settings
    EMBEDDING_DEVICE = "cuda"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Memory Management
    TORCH_CUDA_MEMORY_FRACTION = 0.8  # Use 80% of GPU memory
    FAISS_GPU_MEMORY_FRACTION = 0.5   # Reserve 50% of remaining for FAISS
    
    # Performance Settings
    BATCH_SIZE = 32  # Adjust based on GPU memory
    MAX_SEQUENCE_LENGTH = 512
    
    # Environment Variables (can override class variables)
    @classmethod
    def get_faiss_gpu_enabled(cls) -> bool:
        """Get FAISS GPU enabled setting from environment or class default."""
        return os.getenv('FAISS_GPU_ENABLED', str(cls.FAISS_GPU_ENABLED)).lower() == 'true'
    
    @classmethod
    def get_embedding_device(cls) -> str:
        """Get embedding device from environment or class default."""
        return os.getenv('EMBEDDING_DEVICE', cls.EMBEDDING_DEVICE)
    
    @classmethod
    def get_faiss_gpu_device(cls) -> int:
        """Get FAISS GPU device ID from environment or class default."""
        return int(os.getenv('FAISS_GPU_DEVICE', str(cls.FAISS_GPU_DEVICE)))
    
    @classmethod
    def get_batch_size(cls) -> int:
        """Get batch size from environment or class default."""
        return int(os.getenv('BATCH_SIZE', str(cls.BATCH_SIZE)))
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'faiss_gpu_enabled': cls.get_faiss_gpu_enabled(),
            'faiss_gpu_device': cls.get_faiss_gpu_device(),
            'faiss_use_float16': cls.FAISS_USE_FLOAT16,
            'embedding_device': cls.get_embedding_device(),
            'embedding_model': cls.EMBEDDING_MODEL,
            'torch_cuda_memory_fraction': cls.TORCH_CUDA_MEMORY_FRACTION,
            'faiss_gpu_memory_fraction': cls.FAISS_GPU_MEMORY_FRACTION,
            'batch_size': cls.get_batch_size(),
            'max_sequence_length': cls.MAX_SEQUENCE_LENGTH
        }


def check_gpu_compatibility() -> Dict[str, Any]:
    """
    Check GPU compatibility for both PyTorch and FAISS.
    
    Returns:
        Dict[str, Any]: Compatibility information
    """
    result = {
        'torch_available': False,
        'torch_cuda_available': False,
        'faiss_available': False,
        'faiss_gpu_available': False,
        'gpu_count': 0,
        'gpu_name': None,
        'cuda_version': None,
        'recommendations': []
    }
    
    # Check PyTorch
    try:
        import torch
        result['torch_available'] = True
        result['torch_cuda_available'] = torch.cuda.is_available()
        
        if result['torch_cuda_available']:
            result['gpu_count'] = torch.cuda.device_count()
            result['gpu_name'] = torch.cuda.get_device_name(0)
            result['cuda_version'] = torch.version.cuda
    except ImportError:
        result['recommendations'].append("Install PyTorch with CUDA support")
    
    # Check FAISS
    try:
        import faiss
        result['faiss_available'] = True
        result['faiss_gpu_available'] = faiss.get_num_gpus() > 0
        
        if not result['faiss_gpu_available']:
            result['recommendations'].append("Install faiss-gpu instead of faiss-cpu")
    except ImportError:
        result['recommendations'].append("Install FAISS-GPU")
    
    # Generate recommendations
    if not result['torch_cuda_available']:
        result['recommendations'].append("Ensure NVIDIA drivers and CUDA are installed")
    
    if result['torch_cuda_available'] and not result['faiss_gpu_available']:
        result['recommendations'].append("Check FAISS-GPU installation and CUDA compatibility")
    
    return result


def optimize_gpu_memory():
    """Optimize GPU memory settings for RAG pipeline."""
    try:
        import torch
        
        if torch.cuda.is_available():
            # Set memory fraction
            torch.cuda.set_per_process_memory_fraction(
                GPUConfig.TORCH_CUDA_MEMORY_FRACTION
            )
            
            # Enable memory efficiency
            torch.backends.cudnn.benchmark = True
            
            print(f"GPU memory optimized:")
            print(f"  Memory fraction: {GPUConfig.TORCH_CUDA_MEMORY_FRACTION}")
            print(f"  CuDNN benchmark: enabled")
            
            return True
    except ImportError:
        pass
    
    return False


def print_gpu_status():
    """Print detailed GPU status information."""
    print("\n" + "="*50)
    print("GPU STATUS REPORT")
    print("="*50)
    
    compatibility = check_gpu_compatibility()
    
    print(f"PyTorch Available: {'✓' if compatibility['torch_available'] else '✗'}")
    print(f"PyTorch CUDA: {'✓' if compatibility['torch_cuda_available'] else '✗'}")
    print(f"FAISS Available: {'✓' if compatibility['faiss_available'] else '✗'}")
    print(f"FAISS GPU: {'✓' if compatibility['faiss_gpu_available'] else '✗'}")
    
    if compatibility['gpu_count'] > 0:
        print(f"GPU Count: {compatibility['gpu_count']}")
        print(f"GPU Name: {compatibility['gpu_name']}")
        print(f"CUDA Version: {compatibility['cuda_version']}")
    
    if compatibility['recommendations']:
        print("\nRecommendations:")
        for rec in compatibility['recommendations']:
            print(f"  • {rec}")
    
    print("\nConfiguration:")
    config = GPUConfig.to_dict()
    for key, value in config.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    print_gpu_status()
    optimize_gpu_memory()
