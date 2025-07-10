from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import logging
from datetime import datetime
import redis
from elasticsearch import Elasticsearch
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import pinecone
from sentence_transformers import SentenceTransformer
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Voice AI RAG System",
    description="Retrieval-Augmented Generation system for Voice AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
elasticsearch_client = Elasticsearch([os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")])

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Pinecone
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENVIRONMENT")
)

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    context: Optional[List[Dict[str, Any]]] = None
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query_time: float

class DocumentIngestRequest(BaseModel):
    file_path: str
    metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = None

class DocumentIngestResponse(BaseModel):
    document_id: str
    chunks_created: int
    status: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {}
    
    # Check Redis
    try:
        redis_client.ping()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"
    
    # Check Elasticsearch
    try:
        elasticsearch_client.ping()
        services["elasticsearch"] = "healthy"
    except Exception as e:
        services["elasticsearch"] = f"unhealthy: {str(e)}"
    
    # Check Pinecone
    try:
        pinecone.describe_index("voice-ai-knowledge")
        services["pinecone"] = "healthy"
    except Exception as e:
        services["pinecone"] = f"unhealthy: {str(e)}"
    
    # Check OpenAI
    try:
        openai.Model.list()
        services["openai"] = "healthy"
    except Exception as e:
        services["openai"] = f"unhealthy: {str(e)}"
    
    return HealthResponse(
        status="healthy" if all("healthy" in status for status in services.values()) else "unhealthy",
        timestamp=datetime.now().isoformat(),
        services=services
    )

# Query endpoint
@app.post("/rag/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base for relevant information"""
    start_time = datetime.now()
    
    try:
        # Get user context from memory if available
        user_context = ""
        if request.user_id:
            try:
                memory_data = redis_client.get(f"user_memory:{request.user_id}")
                if memory_data:
                    memory = json.loads(memory_data)
                    user_context = " ".join([msg.get("content", "") for msg in memory.get("conversation_history", [])[-5:]])
            except Exception as e:
                logger.warning(f"Failed to get user memory: {e}")
        
        # Combine query with context
        enhanced_query = f"{request.query} {user_context}".strip()
        
        # Search in Pinecone
        index = pinecone.Index("voice-ai-knowledge")
        
        # Generate query embedding
        query_embedding = embeddings.embed_query(enhanced_query)
        
        # Search for similar documents
        search_results = index.query(
            vector=query_embedding,
            top_k=request.max_results or 5,
            include_metadata=True
        )
        
        # Extract relevant documents
        relevant_docs = []
        for match in search_results.matches:
            relevant_docs.append({
                "content": match.metadata.get("text", ""),
                "source": match.metadata.get("source", ""),
                "score": match.score
            })
        
        # Prepare context for OpenAI
        context = "\n\n".join([doc["content"] for doc in relevant_docs])
        
        # Generate response using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately. If the context doesn't contain relevant information, say so politely."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {request.query}\n\nPlease provide a helpful answer based on the context."}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        # Calculate confidence based on document scores
        avg_score = np.mean([doc["score"] for doc in relevant_docs]) if relevant_docs else 0
        confidence = min(avg_score * 2, 1.0)  # Scale to 0-1 range
        
        query_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            answer=answer,
            sources=relevant_docs,
            confidence=confidence,
            query_time=query_time
        )
        
    except Exception as e:
        logger.error(f"Error in RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

# Document ingestion endpoint
@app.post("/rag/ingest", response_model=DocumentIngestResponse)
async def ingest_document(request: DocumentIngestRequest):
    """Ingest a document into the knowledge base"""
    try:
        # Read document content
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        with open(request.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        chunks = text_splitter.split_text(content)
        
        # Generate embeddings for chunks
        embeddings_list = embeddings.embed_documents(chunks)
        
        # Prepare data for Pinecone
        index = pinecone.Index("voice-ai-knowledge")
        
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
            vector_data = {
                "id": f"{request.file_path}_{i}",
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "source": request.file_path,
                    "category": request.category or "general",
                    "chunk_index": i,
                    "ingested_at": datetime.now().isoformat(),
                    **request.metadata or {}
                }
            }
            vectors.append(vector_data)
        
        # Upsert vectors to Pinecone
        index.upsert(vectors=vectors)
        
        # Store document metadata in Elasticsearch
        doc_metadata = {
            "file_path": request.file_path,
            "category": request.category or "general",
            "chunks_count": len(chunks),
            "ingested_at": datetime.now().isoformat(),
            "metadata": request.metadata or {}
        }
        
        elasticsearch_client.index(
            index="voice-ai-documents",
            document=doc_metadata,
            id=request.file_path
        )
        
        return DocumentIngestResponse(
            document_id=request.file_path,
            chunks_created=len(chunks),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error in document ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")

# List documents endpoint
@app.get("/rag/documents")
async def list_documents():
    """List all ingested documents"""
    try:
        response = elasticsearch_client.search(
            index="voice-ai-documents",
            body={"query": {"match_all": {}}}
        )
        
        documents = []
        for hit in response["hits"]["hits"]:
            documents.append({
                "id": hit["_id"],
                "source": hit["_source"],
                "score": hit["_score"]
            })
        
        return {"documents": documents, "total": len(documents)}
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

# Delete document endpoint
@app.delete("/rag/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the knowledge base"""
    try:
        # Delete from Pinecone
        index = pinecone.Index("voice-ai-knowledge")
        
        # Get all vectors for this document
        response = index.query(
            vector=[0] * 1536,  # Dummy vector for metadata search
            filter={"source": {"$eq": document_id}},
            top_k=1000,
            include_metadata=False
        )
        
        # Delete vectors
        if response.matches:
            vector_ids = [match.id for match in response.matches]
            index.delete(ids=vector_ids)
        
        # Delete from Elasticsearch
        elasticsearch_client.delete(
            index="voice-ai-documents",
            id=document_id
        )
        
        return {"status": "success", "message": f"Document {document_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# Search documents endpoint
@app.post("/rag/search")
async def search_documents(query: str, category: Optional[str] = None, limit: int = 10):
    """Search documents by content"""
    try:
        # Generate query embedding
        query_embedding = embeddings.embed_query(query)
        
        # Search in Pinecone
        index = pinecone.Index("voice-ai-knowledge")
        
        filter_dict = {}
        if category:
            filter_dict["category"] = {"$eq": category}
        
        search_results = index.query(
            vector=query_embedding,
            top_k=limit,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        results = []
        for match in search_results.matches:
            results.append({
                "id": match.id,
                "content": match.metadata.get("text", ""),
                "source": match.metadata.get("source", ""),
                "category": match.metadata.get("category", ""),
                "score": match.score
            })
        
        return {"results": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 