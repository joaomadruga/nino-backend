import streamlit as st
import requests
import json
from datetime import datetime
import uuid

# Configuração da página
st.set_page_config(
    page_title="Nino - Assistente Jurídico",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f4e79;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #6c757d;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f4e79;
    }
    .user-message {
        background-color: #1565c0;
        border-left-color: #0d47a1;
        color: white;
    }
    .assistant-message {
        background-color: #f8f9fa;
        border-left-color: #1f4e79;
        color: #333333;
    }
    .consultation-type-badge {
        background-color: #1f4e79;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuração da API
try:
    if hasattr(st, 'secrets') and st.secrets:
        API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")
    else:
        API_BASE_URL = "http://localhost:8000"
except Exception:
    API_BASE_URL = "http://localhost:8000"

def load_conversation_history(session_id: str) -> list:
    """Carrega histórico de conversas da API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/history/{session_id}",
            timeout=10
        )
        if response.status_code == 200:
            history_data = response.json()
            messages = []

            for item in history_data.get("history", []):
                # Adicionar mensagem do usuário
                if item.get("user_message"):
                    messages.append({
                        "role": "user",
                        "content": item["user_message"],
                        "timestamp": datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
                        "is_document": item.get("is_document", False)
                    })

                # Adicionar resposta do bot
                if item.get("bot_response"):
                    messages.append({
                        "role": "assistant",
                        "content": item["bot_response"],
                        "timestamp": datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                    })

            return messages
    except Exception as e:
        print(f"Erro ao carregar histórico: {e}")

    return []

# Inicializar session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

    # Tentar carregar histórico se temos session_id
    if st.session_state.session_id:
        history = load_conversation_history(st.session_state.session_id)
        if history:
            st.session_state.messages = history

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = True

def make_api_request(message: str, consultation_type: str) -> dict:
    """Faz requisição para a API do Nino"""
    try:
        payload = {
            "message": message,
            "consultation_type": consultation_type,
            "session_id": st.session_state.session_id
        }

        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=240  # 4 minutos timeout - modelo demora ~3 min
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Erro HTTP {response.status_code}: {response.text}"}

    except requests.exceptions.Timeout:
        return {"error": "Timeout: A consulta demorou muito para responder. Tente novamente."}
    except requests.exceptions.ConnectionError:
        return {"error": "Erro de conexão: Não foi possível conectar com a API."}
    except Exception as e:
        return {"error": f"Erro inesperado: {str(e)}"}

def upload_document_to_api(uploaded_file, consultation_type: str) -> dict:
    """Faz upload de documento PDF para a API"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        data = {
            "session_id": st.session_state.session_id,
            "consultation_type": consultation_type
        }

        response = requests.post(
            f"{API_BASE_URL}/upload-document",
            files=files,
            data=data,
            timeout=180  # 3 minutos timeout para upload e processamento
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Erro HTTP {response.status_code}: {response.text}"}

    except requests.exceptions.Timeout:
        return {"error": "Timeout: O processamento do documento demorou muito. Tente um arquivo menor."}
    except requests.exceptions.ConnectionError:
        return {"error": "Erro de conexão: Não foi possível conectar com a API."}
    except Exception as e:
        return {"error": f"Erro inesperado no upload: {str(e)}"}

# Header
st.markdown('<h1 class="main-header">⚖️ Nino</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Assistente Jurídico Brasileiro - Amigável, Competente e Sempre Pronto para Ajudar</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔧 Configurações")

    # Tipo de consulta
    consultation_type = st.selectbox(
        "Tipo de Conversa:",
        options=[
            ("general", "💬 Conversa Geral"),
            ("consultation", "📋 Consulta Jurídica"),
            ("case_analysis", "🔍 Análise de Caso"),
            ("legal_research", "📚 Pesquisa Jurídica"),
            ("document_draft", "📝 Elaboração de Documentos"),
            ("legislation_search", "📖 Busca em Legislação")
        ],
        format_func=lambda x: x[1],
        index=0
    )

    st.markdown("---")

    # Informações da sessão
    st.markdown("### 📊 Sessão Atual")
    st.write(f"**ID:** `{st.session_state.session_id[:8]}...`")
    st.write(f"**Mensagens:** {len(st.session_state.messages)}")

    # Botão para nova sessão
    if st.button("🔄 Nova Sessão"):
        # Gerar novo session_id
        new_session_id = str(uuid.uuid4())
        st.session_state.session_id = new_session_id
        st.session_state.messages = []
        st.session_state.history_loaded = False
        st.rerun()

    st.markdown("---")

    # Exemplos de consultas
    st.markdown("### 💡 Exemplos de Consultas")

    examples = {
        "consultation": [
            "Qual o prazo para impugnação de auto de infração?",
            "Como contestar uma multa administrativa?"
        ],
        "case_analysis": [
            "Servidor demitido sem processo disciplinar",
            "Empresa pública não pagou fornecedor"
        ],
        "legal_research": [
            "Responsabilidade civil do Estado",
            "Lei de Responsabilidade Fiscal"
        ],
        "document_draft": [
            "Petição inicial para ação de cobrança",
            "Recurso administrativo contra multa"
        ],
        "legislation_search": [
            "CF/88 artigo sobre devido processo legal",
            "Lei 8666 sobre licitações"
        ]
    }

    selected_examples = examples.get(consultation_type[0], [])
    for example in selected_examples:
        if st.button(f"💬 {example}", key=f"example_{example}"):
            st.session_state.current_message = example

# Área principal de chat
st.markdown("### 💬 Conversa com Nino")

# Container para o histórico
chat_container = st.container()

# Container para upload de documentos
upload_container = st.container()

# Container para input
input_container = st.container()

st.markdown("---")

# Exibir histórico de mensagens
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            # Verificar se é um documento
            icon = "📄" if message.get("is_document", False) else "👤"
            title = f"{icon} Você ({message.get('type', 'consultation')}):"

            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>{title}</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>⚖️ Nino:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)

# Input de mensagem e upload
with input_container:
    # Seção de Upload de PDF
    with st.expander("📄 Upload de PDF", expanded=False):
        col_upload1, col_upload2 = st.columns([3, 1])

        with col_upload1:
            uploaded_file = st.file_uploader(
                "Selecione um PDF para análise:",
                type=['pdf'],
                help="Máximo 10MB. O texto será extraído e analisado pelo Nino.",
                key="pdf_uploader"
            )

        with col_upload2:
            upload_consultation_type = st.selectbox(
                "Tipo:",
                options=[
                    ("consultation", "📋 Geral"),
                    ("case_analysis", "🔍 Análise"),
                    ("document_draft", "📝 Revisão"),
                    ("legal_research", "📚 Pesquisa")
                ],
                format_func=lambda x: x[1],
                index=0,
                key="upload_type"
            )

        if uploaded_file is not None:
            file_size = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.info(f"📄 **{uploaded_file.name}** ({file_size:.2f} MB)")

            if st.button("🚀 Analisar PDF", type="primary", use_container_width=True):
                if file_size > 10:
                    st.error("❌ Arquivo muito grande. Máximo: 10MB")
                else:
                    with st.spinner(f"📖 Analisando '{uploaded_file.name}'..."):
                        result = upload_document_to_api(uploaded_file, upload_consultation_type[0])

                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            st.session_state.messages.append({
                                "role": "user",
                                "content": f"📄 Documento: {uploaded_file.name}",
                                "type": upload_consultation_type[1],
                                "timestamp": datetime.now(),
                                "is_document": True
                            })

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result.get("response", "Erro ao processar"),
                                "timestamp": datetime.now()
                            })

                            st.success("✅ Documento analisado!")
                            st.rerun()

    # Seção de Chat
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            default_message = st.session_state.get("current_message", "")
            if default_message:
                st.session_state.current_message = ""

            user_input = st.text_area(
                "Digite sua consulta jurídica:",
                value=default_message,
                height=100,
                placeholder=f"Ex: {examples.get(consultation_type[0], ['Digite sua consulta aqui'])[0]}"
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button("📤 Enviar", use_container_width=True)

# Processar envio
if submit_button and user_input.strip():
    # Adicionar mensagem do usuário
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "type": consultation_type[1],
        "timestamp": datetime.now()
    })

    # Mostrar loading
    with st.spinner(f"🤔 Nino está analisando sua {consultation_type[1].lower()}..."):
        # Fazer requisição para API
        response = make_api_request(user_input, consultation_type[0])

        if "error" in response:
            st.error(f"❌ {response['error']}")
        else:
            # Adicionar resposta do assistente
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.get("response", "Desculpe, não consegui processar sua consulta."),
                "timestamp": datetime.now()
            })

    # Rerun para atualizar a interface
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
    <p>⚖️ <strong>Nino</strong> - Assistente Jurídico Brasileiro |
    Especializado em Direito Institucional com modelo Jurema-7B</p>
    <p><em>Desenvolvido para auxiliar advogados brasileiros com consultas especializadas</em></p>
</div>
""", unsafe_allow_html=True)

# Verificar status da API no startup
if len(st.session_state.messages) == 0:
    with st.expander("🔍 Status da API", expanded=False):
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("✅ API conectada e funcionando!")

                # Mostrar informações da API
                info_response = requests.get(f"{API_BASE_URL}/", timeout=5)
                if info_response.status_code == 200:
                    api_info = info_response.json()
                    st.info(f"📝 {api_info.get('description', 'API do Nino')}")
            else:
                st.error("❌ API não está respondendo corretamente")
        except:
            st.warning(f"⚠️ Não foi possível conectar com a API em: {API_BASE_URL}")
            st.info("💡 Certifique-se de que a API está rodando localmente ou configure a URL correta")