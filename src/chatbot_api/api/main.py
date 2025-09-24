from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from ..models.schemas import ChatRequest, ChatResponse
from ..services.chatbot import ChatbotService
from ..database.database import init_db
from ..core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Nino - Assistente Jurídico Brasileiro",
    description="API do Nino, assistente jurídico especializado em direito brasileiro usando modelo Jurema-7B. Oferece suporte para consultas jurídicas, análise de casos, pesquisa legal, elaboração de documentos e consulta de legislação.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot_service = None


def get_chatbot_service():
    global chatbot_service
    if chatbot_service is None:
        chatbot_service = ChatbotService()
    return chatbot_service


@app.get("/")
async def root():
    return {
        "message": "Olá! Eu sou Nino, seu assistente jurídico brasileiro",
        "description": "Especializado em direito brasileiro e leis institucionais usando modelo Jurema-7B",
        "consultation_types": [
            "consultation - Consulta jurídica geral",
            "case_analysis - Análise de caso jurídico",
            "legal_research - Pesquisa jurídica",
            "document_draft - Elaboração de documentos",
            "legislation_search - Busca em legislação"
        ]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        service = get_chatbot_service()
        response = await service.generate_response(
            message=request.message,
            session_id=request.session_id,
            consultation_type=request.consultation_type
        )
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            consultation_type=request.consultation_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "src.chatbot_api.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )