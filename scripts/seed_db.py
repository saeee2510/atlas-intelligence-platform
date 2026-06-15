from src.db.postgres import SessionLocal
from src.db.models import Company

def seed():
    session = SessionLocal()

    session.add_all([
        Company(name="Microsoft Corp", website="microsoft.com"),
        Company(name="MSFT", website="microsoft.com"),
        Company(name="Google LLC", website="google.com"),
        Company(name="Alphabet Inc", website="abc.xyz"),
        Company(name="OpenAI", website="openai.com"),
        Company(name="Open AI", website="openai.com"),
    ])

    session.commit()
    print("Database seeded!")

if __name__ == "__main__":
    seed()