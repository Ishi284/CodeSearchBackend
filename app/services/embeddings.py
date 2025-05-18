import torch
from transformers import AutoTokenizer, AutoModel

async def load_model_tokenizer():
    """Load CodeT5p model and tokenizer"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_name = "Salesforce/codet5p-110m-embedding"
    
    print(f"Loading model {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir="D:/huggingface_cache",trust_remote_code=True)
    model = AutoModel.from_pretrained(model_name, cache_dir="D:/huggingface_cache",trust_remote_code=True)
    model = model.to(device)
    print(f"Model loaded successfully on {device}")
    
    return model, tokenizer