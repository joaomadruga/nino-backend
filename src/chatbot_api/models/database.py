from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Document-related fields
    is_document = Column(Boolean, default=False, nullable=False)
    document_filename = Column(String, nullable=True)
    document_type = Column(String, nullable=True)  # 'pdf', 'txt', etc.

    # Composite index for efficient session history queries
    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_session_documents', 'session_id', 'is_document'),
    )