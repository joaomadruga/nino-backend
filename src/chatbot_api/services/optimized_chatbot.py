"""
Versão otimizada do chatbot para Railway/GPU deployment
"""

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
from typing import Optional, List, Any
import asyncio
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os

from ..core.config import settings
from ..prompts.legal_prompts import SYSTEM_PROMPT, get_prompt_by_type
from ..database.database import AsyncSessionLocal
from ..models.database import ConversationHistory


class OptimizedJuremaLLM:
    """LLM otimizado para deployment em GPU com quantização"""

    def __init__(self):
        self.hf_model = None
        self.tokenizer = None
        self.model_name = settings.model_name
        self.max_new_tokens = settings.max_new_tokens
        self.device = self._get_optimal_device()
        self._load_model()

    def _get_optimal_device(self) -> str:
        """Determina o melhor device disponível"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_model(self):
        """Carrega modelo com otimizações para GPU"""
        print(f"🚀 Carregando Jurema-7B em {self.device}...")

        # Configuração de quantização para economia de memória
        quantization_config = None
        if self.device == "cuda":
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                print("✅ Quantização 4-bit ativada para economia de VRAM")
            except ImportError:
                print("⚠️ BitsAndBytes não disponível, carregando sem quantização")

        # Token de autenticação
        token = settings.huggingface_hub_token

        # Carregar tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            token=token,
            padding_side='left'
        )

        # Definir pad token se não existir
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Configurações do modelo baseadas no device
        model_kwargs = {
            "token": token,
            "torch_dtype": torch.float16 if self.device != "cpu" else torch.float32,
            "low_cpu_mem_usage": True,
            "trust_remote_code": True
        }

        # Adicionar quantização se disponível
        if quantization_config:
            model_kwargs["quantization_config"] = quantization_config
        elif self.device != "cpu":
            model_kwargs["device_map"] = "auto"

        # Carregar modelo
        self.hf_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            **model_kwargs
        )

        # Mover para device se não usando device_map
        if "device_map" not in model_kwargs:
            self.hf_model = self.hf_model.to(self.device)

        # Otimizações de performance
        if hasattr(self.hf_model, 'half') and self.device != "cpu":
            self.hf_model = self.hf_model.half()

        print(f"✅ Modelo carregado com sucesso em {self.device}")

    def generate(self, prompt: str) -> str:
        """Gera resposta otimizada"""
        try:
            # Tokenizar input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048  # Limitar tamanho do contexto
            )

            input_ids = inputs.input_ids.to(self.hf_model.device)
            attention_mask = inputs.attention_mask.to(self.hf_model.device)

            # Parâmetros de geração otimizados
            generation_config = {
                "max_new_tokens": min(self.max_new_tokens, 256),  # Limitar para performance
                "do_sample": True,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "use_cache": True
            }

            # Gerar com context manager para otimização de memória
            with torch.inference_mode():
                output = self.hf_model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    **generation_config
                )

            # Decodificar apenas a parte nova
            new_tokens = output[0][input_ids.shape[-1]:]
            response = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

            # Limpar cache se necessário
            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                torch.cuda.empty_cache()

            return response.strip()

        except Exception as e:
            print(f"Erro na geração: {e}")
            return "Desculpe, ocorreu um erro ao processar sua consulta. Tente novamente."


class OptimizedChatbotService:
    """Serviço de chatbot otimizado para Railway"""

    def __init__(self):
        self.llm = None  # Lazy loading
        self._model_loading = False

    async def _ensure_model_loaded(self):
        """Carrega modelo apenas quando necessário (lazy loading)"""
        if self.llm is None and not self._model_loading:
            self._model_loading = True
            try:
                print("🔄 Inicializando modelo Jurema-7B...")
                # Carregar em thread separada para não bloquear
                loop = asyncio.get_event_loop()
                self.llm = await loop.run_in_executor(None, OptimizedJuremaLLM)
                print("✅ Modelo pronto para uso!")
            except Exception as e:
                print(f"❌ Erro ao carregar modelo: {e}")
                raise
            finally:
                self._model_loading = False

    async def _get_conversation_history(self, session_id: str) -> List[dict]:
        """Retrieve conversation history from database"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ConversationHistory)
                    .filter(ConversationHistory.session_id == session_id)
                    .order_by(ConversationHistory.timestamp.desc())
                    .limit(3)  # Reduzido para 3 para performance
                )

                conversations = result.scalars().all()
                history = []
                for conv in reversed(conversations):
                    history.append({
                        "user": conv.user_message,
                        "bot": conv.bot_response
                    })

                return history
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    async def _save_conversation_entry(self, session_id: str, user_message: str, bot_response: str):
        """Save conversation entry to database"""
        try:
            async with AsyncSessionLocal() as session:
                conversation = ConversationHistory(
                    session_id=session_id,
                    user_message=user_message,
                    bot_response=bot_response
                )
                session.add(conversation)
                await session.commit()
        except Exception as e:
            print(f"Error saving conversation: {e}")

    async def generate_response(self, message: str, session_id: Optional[str] = None, consultation_type: str = "consultation") -> str:
        """Gera resposta otimizada"""
        # Garantir que o modelo está carregado
        await self._ensure_model_loaded()

        if not session_id:
            session_id = str(uuid.uuid4())

        # Get conversation history (reduzido)
        history = await self._get_conversation_history(session_id)

        # Build context (mais conciso)
        system_context = SYSTEM_PROMPT
        conversation_context = ""

        # Limitar contexto para performance
        for entry in history[-2:]:  # Apenas últimas 2 trocas
            conversation_context += f"Usuário: {entry['user'][:200]}...\nNino: {entry['bot'][:200]}...\n\n"

        # Get structured prompt
        if consultation_type != "consultation":
            if consultation_type == "case_analysis":
                structured_prompt = get_prompt_by_type("case_analysis", case_description=message)
            elif consultation_type == "legal_research":
                structured_prompt = get_prompt_by_type("legal_research", research_topic=message)
            elif consultation_type == "document_draft":
                structured_prompt = get_prompt_by_type("document_draft", document_type="documento legal", document_info=message)
            elif consultation_type == "legislation_search":
                structured_prompt = get_prompt_by_type("legislation_search", legislation_query=message)
            else:
                structured_prompt = get_prompt_by_type("consultation", query=message)

            full_prompt = f"{system_context}\n\n{conversation_context}{structured_prompt}"
        else:
            consultation_prompt = get_prompt_by_type("consultation", query=message)
            full_prompt = f"{system_context}\n\n{conversation_context}{consultation_prompt}"

        # Limitar tamanho total do prompt
        if len(full_prompt) > 4000:
            full_prompt = full_prompt[-4000:]  # Manter apenas os últimos 4000 chars

        # Generate response
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.llm.generate,
            full_prompt
        )

        # Save conversation
        await self._save_conversation_entry(session_id, message, response)

        return response


# Usar a versão otimizada se estivermos em produção
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("HEROKU"):
    ChatbotService = OptimizedChatbotService
    print("🚀 Usando versão otimizada para produção")
else:
    from .chatbot import ChatbotService
    print("🔧 Usando versão de desenvolvimento")