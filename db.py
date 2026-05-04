from sqlalchemy import create_engine, Column, Integer, String, Float, Numeric, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///listings.db"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("platform", "listing_id", name="uq_platform_listing"),
    )

    id = Column(Integer, primary_key=True)

    # Identity
    platform = Column(String, nullable=False)
    listing_id = Column(String, nullable=False)
    url = Column(String)

    # Content (for keyword/NLP extraction)
    title = Column(String)
    description = Column(Text)      # full listing text (where available)
    brand = Column(String)          # designer / brand name
    category = Column(String)       # hierarchical category path (ex. "menswear.tops.t_shirts")
    department = Column(String)     # ex. "menswear" | "womenswear" | etc.
    condition = Column(String)
    size = Column(String)
    color = Column(String)

    # Price signals
    price = Column(Numeric)
    currency = Column(String)

    # Engagement signals (important for momentum scoring)
    likes = Column(Integer)         # favorite / like count
    heat = Column(Float)            # platform-specific engagement score (Grailed: heat_f)

    # Timestamps
    listing_created_at = Column(DateTime(timezone=True))   # when posted
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Geography
    location = Column(String)

    def __repr__(self):
        return f"<Listing {self.platform}:{self.listing_id} - {self.title}>"


def init_db():
    Base.metadata.create_all(engine)
