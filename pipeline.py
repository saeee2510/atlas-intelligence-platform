"""End-to-end run: canonicalize every loaded company (see README for setup)."""
from src.entity_resolution.canonicalization import canonicalize

if __name__ == "__main__":
    canonicalize()
