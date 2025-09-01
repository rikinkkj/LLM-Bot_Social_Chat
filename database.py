
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Bot(Base):
    __tablename__ = 'bots'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    persona = Column(String)
    model = Column(String, default='gemini-1.5-flash')
    posts = relationship("Post", back_populates="bot")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    bot_id = Column(Integer, ForeignKey('bots.id'), nullable=True)
    bot = relationship("Bot", back_populates="posts")
    sender = Column(String)

engine = create_engine('sqlite:///bots.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
