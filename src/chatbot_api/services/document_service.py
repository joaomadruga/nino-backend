"""
Serviço para processamento de documentos PDF
"""

import PyPDF2
import io
from typing import Optional, Dict, Any
import re


class DocumentService:
    """Serviço para extração de texto de documentos"""

    @staticmethod
    def extract_text_from_pdf(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extrai texto de um arquivo PDF

        Args:
            file_content: Conteúdo do arquivo em bytes
            filename: Nome do arquivo

        Returns:
            Dict com texto extraído e metadados
        """
        try:
            # Criar objeto de arquivo em memória
            pdf_file = io.BytesIO(file_content)

            # Ler PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Extrair texto de todas as páginas
            text_content = ""
            num_pages = len(pdf_reader.pages)

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text_content += f"\n--- Página {page_num + 1} ---\n{page_text}\n"

            # Limpar texto extraído
            clean_text = DocumentService._clean_extracted_text(text_content)

            # Metadados do PDF
            metadata = {}
            if pdf_reader.metadata:
                metadata = {
                    "title": pdf_reader.metadata.get("/Title", ""),
                    "author": pdf_reader.metadata.get("/Author", ""),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                    "creator": pdf_reader.metadata.get("/Creator", ""),
                }

            return {
                "success": True,
                "text": clean_text,
                "metadata": {
                    "filename": filename,
                    "num_pages": num_pages,
                    "char_count": len(clean_text),
                    "word_count": len(clean_text.split()),
                    **metadata
                },
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "text": "",
                "metadata": {"filename": filename},
                "error": f"Erro ao extrair texto do PDF: {str(e)}"
            }

    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """
        Limpa e normaliza o texto extraído

        Args:
            text: Texto bruto extraído

        Returns:
            Texto limpo e normalizado
        """
        # Remover linhas em branco excessivas
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

        # Normalizar espaços
        text = re.sub(r'[ \t]+', ' ', text)

        # Remover espaços no início e fim das linhas
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Remover linhas vazias no início e fim
        text = text.strip()

        return text

    @staticmethod
    def validate_pdf_file(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Valida se o arquivo é um PDF válido

        Args:
            file_content: Conteúdo do arquivo
            filename: Nome do arquivo

        Returns:
            Dict com resultado da validação
        """
        # Verificar extensão
        if not filename.lower().endswith('.pdf'):
            return {
                "valid": False,
                "error": "Arquivo deve ter extensão .pdf"
            }

        # Verificar tamanho (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            return {
                "valid": False,
                "error": f"Arquivo muito grande. Máximo permitido: {max_size // (1024*1024)}MB"
            }

        # Verificar se é um PDF válido
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Tentar acessar metadados básicos
            num_pages = len(pdf_reader.pages)

            if num_pages == 0:
                return {
                    "valid": False,
                    "error": "PDF não contém páginas válidas"
                }

            return {
                "valid": True,
                "error": None,
                "metadata": {
                    "num_pages": num_pages,
                    "size_mb": round(len(file_content) / (1024*1024), 2)
                }
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Arquivo PDF inválido ou corrompido: {str(e)}"
            }

    @staticmethod
    def format_document_for_chat(extracted_text: str, filename: str, consultation_type: str = "consultation") -> str:
        """
        Formata o texto extraído para ser enviado como mensagem no chat

        Args:
            extracted_text: Texto extraído do documento
            filename: Nome do arquivo
            consultation_type: Tipo de consulta jurídica

        Returns:
            Texto formatado para o chat
        """
        # Limitar tamanho do texto para evitar prompts muito longos
        max_chars = 8000  # Limite conservador
        if len(extracted_text) > max_chars:
            truncated_text = extracted_text[:max_chars] + "\n\n[... texto truncado para brevidade ...]"
        else:
            truncated_text = extracted_text

        # Formatar mensagem baseada no tipo de consulta
        if consultation_type == "case_analysis":
            formatted_message = f"""📄 ANÁLISE DE DOCUMENTO: {filename}

CONTEÚDO DO DOCUMENTO:
{truncated_text}

Por favor, analise este documento jurídico considerando:
1. Aspectos legais relevantes
2. Possíveis irregularidades ou questões jurídicas
3. Fundamentação legal aplicável
4. Recomendações e próximos passos

Forneça uma análise completa e estruturada."""

        elif consultation_type == "document_draft":
            formatted_message = f"""📄 REVISÃO/ELABORAÇÃO BASEADA EM: {filename}

DOCUMENTO BASE:
{truncated_text}

Com base neste documento, preciso de auxílio para:
1. Revisão jurídica do conteúdo
2. Sugestões de melhorias
3. Identificação de cláusulas problemáticas
4. Adequação à legislação vigente

Forneça orientações para aprimoramento do documento."""

        elif consultation_type == "legal_research":
            formatted_message = f"""📄 PESQUISA JURÍDICA BASEADA EM: {filename}

DOCUMENTO PARA ANÁLISE:
{truncated_text}

Solicito pesquisa jurídica relacionada aos temas e questões presentes neste documento:
1. Legislação aplicável aos casos mencionados
2. Jurisprudência relevante
3. Doutrina sobre os temas abordados
4. Precedentes dos tribunais superiores

Forneça fundamentação jurídica abrangente."""

        else:  # consultation geral
            formatted_message = f"""📄 CONSULTA SOBRE DOCUMENTO: {filename}

CONTEÚDO:
{truncated_text}

Preciso de orientação jurídica sobre este documento. Por favor, analise o conteúdo e forneça:
1. Principais questões jurídicas identificadas
2. Legislação aplicável
3. Riscos ou oportunidades jurídicas
4. Recomendações práticas

Aguardo sua análise especializada."""

        return formatted_message