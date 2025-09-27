from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
import time
from typing import Optional

from ..models.schemas import ChatRequest, ChatResponse
from ..services.chatbot import ChatbotService
from ..services.document_service import DocumentService
from ..database.database import init_db, AsyncSessionLocal
from ..models.database import ConversationHistory
from ..core.config import settings
from sqlalchemy import select

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    start_time = time.time()

    # Log da requisição recebida
    logger.info(f"🔵 CHAT REQUEST | Session: {request.session_id[:8]}... | Type: {request.consultation_type} | Message: {request.message[:100]}{'...' if len(request.message) > 100 else ''}")

    try:
        service = get_chatbot_service()

        # Log antes de gerar resposta
        logger.info(f"🔄 GENERATING RESPONSE | Session: {request.session_id[:8]}...")

        response = await service.generate_response(
            message=request.message,
            session_id=request.session_id,
            consultation_type=request.consultation_type
        )

        # Log da resposta gerada
        processing_time = time.time() - start_time
        response_preview = response[:150] + "..." if len(response) > 150 else response
        logger.info(f"✅ RESPONSE SENT | Session: {request.session_id[:8]}... | Time: {processing_time:.2f}s | Length: {len(response)} chars | Preview: {response_preview}")

        return ChatResponse(
            response=response,
            session_id=request.session_id,
            consultation_type=request.consultation_type
        )
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"❌ CHAT ERROR | Session: {request.session_id[:8]}... | Time: {error_time:.2f}s | Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-document", response_model=ChatResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    consultation_type: str = Form("consultation")
):
    """
    Upload e processa documento PDF, extraindo texto e gerando análise jurídica
    """
    start_time = time.time()

    # Log da requisição de upload
    logging.info(f"📄 UPLOAD REQUEST | Session: {session_id[:8] if session_id else 'NEW'}... | File: {file.filename} | Type: {consultation_type}")

    try:
        # Validar arquivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nome do arquivo é obrigatório")

        # Ler conteúdo do arquivo
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        logging.info(f"📊 FILE DETAILS | Size: {file_size_mb:.2f}MB | Processing...")

        # Validar PDF
        validation = DocumentService.validate_pdf_file(file_content, file.filename)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["error"])

        # Extrair texto do PDF
        extraction_result = DocumentService.extract_text_from_pdf(file_content, file.filename)
        if not extraction_result["success"]:
            raise HTTPException(status_code=500, detail=extraction_result["error"])

        extracted_text = extraction_result["text"]
        metadata = extraction_result["metadata"]

        # Verificar se foi extraído algum texto
        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Não foi possível extrair texto do PDF. Verifique se o documento contém texto legível."
            )

        # Formatar texto para consulta jurídica
        formatted_message = DocumentService.format_document_for_chat(
            extracted_text, file.filename, consultation_type
        )

        # Gerar session_id se não fornecido
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())

        # Salvar documento no banco como conversa
        async with AsyncSessionLocal() as db_session:
            # Salvar entrada do documento
            document_entry = ConversationHistory(
                session_id=session_id,
                user_message=extracted_text,
                bot_response="",  # Será preenchido após a resposta
                is_document=True,
                document_filename=file.filename,
                document_type="pdf"
            )
            db_session.add(document_entry)
            await db_session.commit()

        # Gerar resposta do Nino
        logging.info(f"🤖 GENERATING AI RESPONSE | Session: {session_id[:8]}... | Text extracted: {len(extracted_text)} chars")

        service = get_chatbot_service()
        response = await service.generate_response(
            message=formatted_message,
            session_id=session_id,
            consultation_type=consultation_type
        )

        # Log da resposta final
        processing_time = time.time() - start_time
        final_response = f"📄 **Documento Analisado**: {file.filename}\n\n" \
                        f"📊 **Metadados**: {metadata['num_pages']} páginas, {metadata['word_count']} palavras\n\n" \
                        f"---\n\n{response}"

        logging.info(f"✅ DOCUMENT RESPONSE SENT | Session: {session_id[:8]}... | File: {file.filename} | Time: {processing_time:.2f}s | AI Response: {len(response)} chars | Total: {len(final_response)} chars")

        return ChatResponse(
            response=final_response,
            session_id=session_id,
            consultation_type=consultation_type
        )

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time
        logging.error(f"❌ UPLOAD ERROR | Session: {session_id[:8] if session_id else 'NEW'}... | File: {file.filename} | Time: {error_time:.2f}s | Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.get("/history/{session_id}")
async def get_conversation_history(session_id: str):
    """
    Recupera histórico de conversas para uma sessão específica
    """
    try:
        async with AsyncSessionLocal() as db_session:
            # Buscar histórico da sessão
            query = select(ConversationHistory).where(
                ConversationHistory.session_id == session_id
            ).order_by(ConversationHistory.timestamp.asc())

            result = await db_session.execute(query)
            conversations = result.scalars().all()

            # Formatar resposta
            history = []
            for conv in conversations:
                history.append({
                    "session_id": conv.session_id,
                    "user_message": conv.user_message,
                    "bot_response": conv.bot_response,
                    "timestamp": conv.timestamp.isoformat(),
                    "is_document": conv.is_document,
                    "document_filename": conv.document_filename,
                    "document_type": conv.document_type
                })

            return {
                "session_id": session_id,
                "history": history,
                "total_messages": len(history)
            }

    except Exception as e:
        logger.error(f"❌ HISTORY ERROR | Session: {session_id[:8]}... | Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar histórico: {str(e)}")


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