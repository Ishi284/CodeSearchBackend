import os
import numpy as np
import torch
import pickle
import faiss
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from app.core.config import settings
from app.services.embeddings import load_model_tokenizer

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

class CodeSearchService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.language_data = {}
        self.initialized = False
        
    async def initialize(self):
        """Initialize the model and load embeddings for all languages"""
        if self.initialized:
            return
            
        # Load model and tokenizer
        self.model, self.tokenizer = await load_model_tokenizer()
        
        # Load embeddings for all supported languages
        for language in settings.SUPPORTED_LANGUAGES:
            await self.load_language_data(language)
            
        self.initialized = True
        
    async def load_language_data(self, language: str):
        """Load embeddings, metadata and index for a specific language"""
        embedding_dir = os.path.join(settings.MODEL_DIR, language)
        
        # Define file paths
        embedding_file = os.path.join(embedding_dir, "code_embeddings.npy")
        metadata_file = os.path.join(embedding_dir, "metadata.pkl")
        index_file = os.path.join(embedding_dir, "faiss_index.index")
        
        # Check if files exist
        if not all(os.path.exists(f) for f in [embedding_file, metadata_file, index_file]):
            print(f"Warning: Missing data files for {language} in {embedding_dir}")
            return False
        
        # Load embeddings
        embeddings = np.load(embedding_file)
        
        # Load metadata
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        # Load FAISS index
        index = faiss.read_index(index_file)
        
        # Store data
        self.language_data[language] = {
            "embeddings": embeddings,
            "code_list": metadata["code_list"],
            "docstring_list": metadata.get("docstring_list", []),
            "index": index
        }
        
        print(f"Loaded data for {language}: {len(metadata['code_list'])} code samples")
        return True
        
    async def search(self, query: str, language: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for code snippets matching the query"""
        if not self.initialized:
            await self.initialize()
            
        if language not in self.language_data:
            await self.load_language_data(language)
            if language not in self.language_data:
                raise ValueError(f"Language {language} not supported or data not available")
        
        # Create query embedding
        query_embedding = self.get_embeddings([query], prefix="Query", max_length=512)
        
        # Get index and code list
        index = self.language_data[language]["index"]
        code_list = self.language_data[language]["code_list"]
        
        # Search with FAISS
        D, I = index.search(query_embedding.astype(np.float32), top_k)
        
        # Format results
        results = []
        for i, idx in enumerate(I[0]):
            if idx < len(code_list) and idx >= 0:
                similarity_score = 1 / (1 + float(D[0][i]))
                results.append({
                    "code": code_list[idx],
                    "similarity": float(similarity_score),
                    "distance": float(D[0][i])
                })
        
        return results
    
    def get_embeddings(self, texts: List[str], prefix: str = "", max_length: int = 512, batch_size: int = 16):
        """Generate embeddings for text"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            inputs = self.tokenizer(
                batch_texts, 
                padding="max_length", 
                truncation=True, 
                max_length=max_length,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.cpu().numpy()
                
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)

# Create singleton instance
code_search_service = CodeSearchService()