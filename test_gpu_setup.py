#!/usr/bin/env python3
"""
Test veloce per verificare configurazione GPU
"""

import torch

def test_gpu():
    print("=== TEST GPU ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        print(f"Current GPU: {torch.cuda.get_device_name()}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        
        # Test semplice
        x = torch.rand(100, 100).cuda()
        y = x @ x.T
        print(f"✅ GPU test successful - tensor on {y.device}")
    else:
        print("❌ CUDA not available")
    
    return torch.cuda.is_available()

if __name__ == "__main__":
    gpu_ok = test_gpu()
    exit(0 if gpu_ok else 1)