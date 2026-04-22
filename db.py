from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///listings.db"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True)
    platform = Column(String, nullable=False)
    listing_id = Column(String, nullable=False)
    title = Column(String)
    price = Column(Numeric)
    currency = Column(String)
    category = Column(String)
    condition = Column(String)
    url = Column(String)
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Listing {self.platform}:{self.listing_id} - {self.title}>"


def init_db():
    Base.metadata.create_all(engine)
