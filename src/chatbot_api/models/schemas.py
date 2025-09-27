from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., description="A consulta ou mensagem do usuário")
    session_id: Optional[str] = Field(None, description="ID da sessão para contexto da conversa")
    consultation_type: Optional[Literal["general", "consultation", "case_analysis", "legal_research", "document_draft", "legislation_search"]] = Field(
        "consultation",
        description="Tipo de consulta jurídica"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="A resposta do assistente jurídico")
    session_id: str = Field(..., description="ID da sessão para contexto da conversa")
    consultation_type: str = Field(..., description="Tipo de consulta processada")


class ConversationHistoryCreate(BaseModel):
    session_id: str
    user_message: str
    bot_response: str


class ConversationHistoryResponse(BaseModel):
    id: int
    session_id: str
    user_message: str
    bot_response: str
    timestamp: datetime

    class Config:
        from_attributes = True