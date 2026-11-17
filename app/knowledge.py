from functools import lru_cache

from groq import Groq
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache()
def client():
    if not settings.GROQ_API_KEY or not settings.PINECONE_API_KEY:
        raise ValueError("GROQ_API_KEY and PINECONE_API_KEY must be set in the environment variables.")

    return Pinecone(api_key=settings.PINECONE_API_KEY), Groq(api_key=settings.GROQ_API_KEY)


@lru_cache()
def embedding_model():
    return SentenceTransformer(settings.LOCAL_EMBED_MODEL)


def ensure_index():
    pinecone_client, _ = client()
    if not pinecone_client.has_index(settings.PINECONE_INDEX):
        pinecone_client.create_index(
            name=settings.PINECONE_INDEX,
            dimension=embedding_model().get_sentence_embedding_dimension(),
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pinecone_client.Index(settings.PINECONE_INDEX)


def embed(texts):
    vectors = embedding_model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def search_kb(query, top_k=5):
    index = ensure_index()
    vector = embed([query])[0]

    result = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
    )

    return [
        {
            'page': m.metadata.get('page'),
            'text': m.metadata.get('text', ''),
            'source': 'Gale Encyclopedia (2002)',
        }
        for m in result.matches
        if m.score >= 0.30
    ]