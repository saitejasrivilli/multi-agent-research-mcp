"""
ChromaDB Vector Store for Semantic Search and RAG
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import hashlib

class ChromaVectorStore:
    """Vector store for research documents using ChromaDB."""
    
    def __init__(self, collection_name: str = "research_docs", persist_dir: str = "./chroma_db"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text content."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def add_documents(self, documents: List[Dict]) -> List[str]:
        """Add documents to the vector store."""
        ids = []
        texts = []
        metadatas = []
        
        for doc in documents:
            content = doc.get("content", doc.get("snippet", ""))
            if not content:
                continue
            
            doc_id = self._generate_id(content)
            ids.append(doc_id)
            texts.append(content[:2000])  # Limit text size
            metadatas.append({
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "source": doc.get("source", "web")
            })
        
        if texts:
            embeddings = self.embedder.encode(texts).tolist()
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
        
        return ids
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar documents."""
        query_embedding = self.embedder.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        docs = []
        for i in range(len(results["ids"][0])):
            docs.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
            })
        
        return docs
    
    def get_context(self, query: str, n_results: int = 3) -> str:
        """Get relevant context for RAG."""
        docs = self.search(query, n_results)
        context = "\n\n".join([
            f"Source: {d['metadata'].get('title', 'Unknown')}\n{d['content']}"
            for d in docs
        ])
        return context
