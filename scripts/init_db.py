from src.db.postgres import engine
from src.db.models import Base

def init():
    Base.metadata.create_all(engine)
    print("All tables created!")

if __name__ == "__main__":
    init()