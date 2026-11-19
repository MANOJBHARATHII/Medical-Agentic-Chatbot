from functools import lru_cache
import pinecone
from openai import OpenAI
from app.config import settings

@lru_cache()
def client():
    if not settings.OPENAI_API_KEY or not settings.PINECONE_API_KEY:
        raise ValueError("OPENAI_API_KEY and PINECONE_API_KEY must be set in the environment variables.")
    return {
        "pinecone": pinecone.PineconeClient(api_key=settings.PINECONE_API_KEY, serverless=pinecone.ServerlessSpec()),
        "openai": OpenAI(api_key=settings.OPENAI_API_KEY)
    }
def ensure_index():
    pinecone_client, _ = client()  
    if not pinecone_client.has_index(settings.PINECONE_INDEX):
        pinecone_client.create_index(settings.PINECONE_INDEX, dimension=1536, metric="cosine",spec=pinecone.ServerlessSpec(cloud ="aws", region = "us-east-1"))
    return pinecone_client.Index(settings.PINECONE_INDEX)

def embed(texts):
    ai,_ = client()
    return[x.embedding for x in ai.openai.embeddings.create(model=settings.OPENAI_EMBED_MODEL, input=texts).data]

def search_kb(query, top_k=5):
    index = ensure_index()
    vector = embed([query])[0]

    result = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )

    return [
        {
            'page': m.metadata.get('page'),
            'text': m.metadata.get('text', ''),
            'source': 'Gale Encyclopedia (2002)'
        }
        for m in result.matches
        if m.score >= 0.30
    ]