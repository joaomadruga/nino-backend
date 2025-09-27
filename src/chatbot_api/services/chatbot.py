from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional, List, Any
import asyncio
import json
import uuid
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc

from ..core.config import settings
from ..prompts.legal_prompts import SYSTEM_PROMPT, get_prompt_by_type
from ..database.database import AsyncSessionLocal
from ..models.database import ConversationHistory


class JuremaLLM:
    def __init__(self):
        self.hf_model = None
        self.tokenizer = None
        self.model_name = settings.model_name
        self.max_new_tokens = settings.max_new_tokens
        self._load_model()

    def _load_model(self):
        # Set up authentication if token is provided
        token = settings.huggingface_hub_token

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            token=token
        )

        # Determine the best device for macOS
        if torch.backends.mps.is_available():
            device = "mps"
            torch_dtype = torch.float16  # MPS works better with float16
        elif torch.cuda.is_available():
            device = "cuda"
            torch_dtype = torch.bfloat16
        else:
            device = "cpu"
            torch_dtype = torch.float32

        self.hf_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch_dtype,
            token=token,
            low_cpu_mem_usage=True
        ).to(device)

    def generate(self, prompt: str) -> str:
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.hf_model.device)

        with torch.no_grad():
            output = self.hf_model.generate(
                input_ids,
                max_new_tokens=self.max_new_tokens,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return response[len(prompt):].strip()


class ChatbotService:
    def __init__(self):
        self.llm = JuremaLLM()

    async def _get_conversation_history(self, session_id: str) -> List[dict]:
        """Get conversation history from PostgreSQL"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Get last 10 conversations for this session
                query = select(ConversationHistory).where(
                    ConversationHistory.session_id == session_id
                ).order_by(desc(ConversationHistory.timestamp)).limit(10)

                result = await db_session.execute(query)
                conversations = result.scalars().all()

                # Convert to list format (reverse to get chronological order)
                history = []
                for conv in reversed(conversations):
                    if conv.user_message:
                        history.append({
                            "role": "user",
                            "content": conv.user_message
                        })
                    if conv.bot_response:
                        history.append({
                            "role": "assistant",
                            "content": conv.bot_response
                        })

                return history[-20:]  # Keep last 20 messages to limit context

        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    async def _save_conversation_to_db(self, session_id: str, user_message: str, bot_response: str):
        """Save conversation to PostgreSQL"""
        try:
            async with AsyncSessionLocal() as db_session:
                conversation = ConversationHistory(
                    session_id=session_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    is_document=False
                )
                db_session.add(conversation)
                await db_session.commit()

        except Exception as e:
            print(f"❌ Error saving conversation to database: {e}")

    async def generate_response(self, message: str, session_id: Optional[str] = None, consultation_type: str = "consultation") -> str:
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get conversation history
        history = await self._get_conversation_history(session_id)

        # Build system prompt and context
        system_context = SYSTEM_PROMPT

        # Build conversation context from history
        conversation_context = ""
        for entry in history[-6:]:  # Keep last 6 messages (3 exchanges) for context
            if entry['role'] == 'user':
                conversation_context += f"Usuário: {entry['content']}\n"
            elif entry['role'] == 'assistant':
                conversation_context += f"Assistente: {entry['content']}\n\n"

        # Get the appropriate prompt based on consultation type
        if consultation_type != "consultation":
            # For specific consultation types, use structured prompts
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
            # For general consultation, use conversation format
            consultation_prompt = get_prompt_by_type("consultation", query=message)
            full_prompt = f"{system_context}\n\n{conversation_context}{consultation_prompt}"

        # Generate response using LLM in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.llm.generate,
            full_prompt
        )

        # Save conversation to database
        await self._save_conversation_to_db(session_id, message, response)

        return response