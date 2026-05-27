from sqlalchemy import Column, Integer, String
from database import Base

class URLTable(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, unique=True, nullable=False)
    short_code = Column(String, unique=True, nullable=False)
    
    def __repr__(self):
        return f"<URLTable(id={self.id}, short_code='{self.short_code}')>"