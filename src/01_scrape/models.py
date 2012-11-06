from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    uri = Column(String, index=True, unique=True)
    text = Column(String, nullable=True)
    favorites_text = Column(String, nullable=True)

    def __init__(self, uri = None, text = None, favorites_text = None):
        self.uri = uri
        self.text = text
        self.favorites_text = favorites_text

