from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# Simple in-memory cache (important for cost + speed)
# -----------------------------
_embedding_cache = {}


# -----------------------------
# Embedding function
# -----------------------------
def embed(text: str) -> np.ndarray:
    """
    Convert text into embedding vector using OpenAI.
    Includes caching to avoid repeated API calls.
    """
    if not text:
        return np.zeros(1536)

    if text in _embedding_cache:
        return _embedding_cache[text]

    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    vector = np.array(res.data[0].embedding, dtype=np.float32)
    _embedding_cache[text] = vector

    return vector


# -----------------------------
# Cosine similarity (numerically stable)
# -----------------------------
def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    Returns value in range [-1, 1], typically [0, 1] for embeddings.
    """

    # safety checks
    if a is None or b is None:
        return 0.0

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


# -----------------------------
# High-level helper 
# -----------------------------
def embedding_score(text_a: str, text_b: str) -> float:
    """
    End-to-end semantic similarity score between two texts.
    """
    vec_a = embed(text_a)
    vec_b = embed(text_b)

    return cosine_sim(vec_a, vec_b)