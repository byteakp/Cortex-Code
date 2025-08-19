import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, PickleType
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    problem_statement = Column(Text, nullable=False)
    test_cases = Column(Text, nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String, default='running') # running, completed, failed
    final_code = Column(Text)
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.id}, status='{self.status}')>"

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    attempt = Column(Integer, nullable=False)
    thought = Column(Text)
    generated_code = Column(Text)
    execution_result = Column(PickleType) # Stores {'success', 'stdout', 'stderr'}
    image_path = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return f"<Message(session_id={self.session_id}, attempt={self.attempt})>"