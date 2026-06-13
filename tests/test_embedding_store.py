from src.entity_resolution.embedding_store import get_embedding


def test_embedding():
    embedding = get_embedding("Microsoft Corporation")

    print("Length:", len(embedding))
    print("First 5 values:", embedding[:5])

    assert isinstance(embedding, list)
    assert len(embedding) > 1000


if __name__ == "__main__":
    test_embedding()