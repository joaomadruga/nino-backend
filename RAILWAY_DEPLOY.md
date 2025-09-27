# 🚀 Deploy do Nino na Railway

## 📋 Pré-requisitos

1. **Conta Railway**: [railway.app](https://railway.app)
2. **GitHub Repository**: Código commitado no GitHub
3. **Hugging Face Token**: Acesso ao modelo Jurema-7B

## 🛠️ Configuração do Deploy

### 1. **Criar Projeto na Railway**

```bash
# Instalar Railway CLI (opcional)
npm install -g @railway/cli

# Ou usar interface web em railway.app
```

### 2. **Configurar Variáveis de Ambiente**

Na Railway dashboard, adicione as seguintes variáveis:

```env
# Essenciais
HUGGINGFACE_HUB_TOKEN=seu_token_aqui
MODEL_NAME=Jurema-br/Jurema-7B
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-gerado pela Railway

# Opcionais (otimizadas para Railway)
MAX_NEW_TOKENS=256
API_HOST=0.0.0.0
API_PORT=$PORT
DEBUG=false

# Otimizações de produção
RAILWAY_ENVIRONMENT=true
PYTHONPATH=/app
```

### 3. **Configurar Banco PostgreSQL**

1. Na Railway: **Add Service** → **PostgreSQL**
2. Conectar ao projeto principal
3. A `DATABASE_URL` será gerada automaticamente

### 4. **Configurar GPU (Importante!)**

⚠️ **Para usar GPU (necessário para Jurema-7B):**

1. No projeto Railway: **Settings** → **Environment**
2. Alterar de **Shared CPU** para **GPU**
3. Confirmar upgrade (~$0.50/hora)

## 🚀 Deploy Steps

### **Opção A: Via GitHub (Recomendado)**

1. **Conectar Repository**:
   - Railway Dashboard → **New Project**
   - **Deploy from GitHub repo**
   - Selecionar repositório do Nino

2. **Configurar Build**:
   - Railway detecta automaticamente Python
   - Usa `requirements-railway.txt` se disponível
   - Build command: automático
   - Start command: definido no `Procfile`

### **Opção B: Via Railway CLI**

```bash
# Login
railway login

# Conectar projeto
railway link

# Deploy
railway up
```

## ⚙️ Arquivos de Configuração

### **Procfile** (já criado)
```
web: uvicorn src.chatbot_api.api.main:app --host 0.0.0.0 --port $PORT
```

### **railway.json** (já criado)
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "never"
  }
}
```

## 🎯 Deploy do Frontend Separado

### **Opção 1: Streamlit Cloud (Gratuito)**

1. **streamlit.io/cloud**
2. Conectar GitHub repo
3. Arquivo principal: `frontend/streamlit_app.py`
4. Configurar secrets:
   ```toml
   # .streamlit/secrets.toml
   API_BASE_URL = "https://seu-app.railway.app"
   ```

### **Opção 2: Segunda Railway App**

1. Criar novo projeto Railway
2. Mesmo repositório, mas diferentes configs
3. **Procfile-frontend**:
   ```
   web: streamlit run frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0
   ```

## 💰 Estimativa de Custos

### **GPU Plan (Necessário para Jurema-7B)**
- **Custo**: ~$0.50-1.00/hora
- **$5 = 5-10 horas** de uso
- **Estratégia**: Liga apenas quando necessário

### **Otimizações de Custo**
```python
# 1. Sleep/Wake automático
# 2. Quantização 4-bit (já implementado)
# 3. Context caching
# 4. Lazy model loading
```

## 🔧 Monitoramento

### **Logs da Railway**
```bash
railway logs
```

### **Métricas**
- CPU/GPU usage
- Memory consumption
- Request latency
- Database connections

## 🐛 Troubleshooting

### **Erro de Memória GPU**
```python
# Já implementado: quantização 4-bit
# Reduzir MAX_NEW_TOKENS se necessário
```

### **Timeout na Inicialização**
```python
# Model lazy loading já implementado
# Primeira requisição será mais lenta
```

### **Erro de Conectividade**
```bash
# Verificar variáveis de ambiente
# Confirmar DATABASE_URL
# Testar health endpoint
```

## ✅ Checklist de Deploy

- [ ] ✅ Repository no GitHub
- [ ] ✅ Conta Railway criada
- [ ] ✅ Token Hugging Face válido
- [ ] ✅ Projeto Railway criado
- [ ] ✅ PostgreSQL adicionado
- [ ] ✅ GPU plan ativado
- [ ] ✅ Variáveis de ambiente configuradas
- [ ] ✅ Deploy realizado
- [ ] ✅ Health check passando
- [ ] ✅ Teste de consulta jurídica

## 🎉 Após Deploy

### **URLs Importantes**
- **API**: `https://seu-app.railway.app`
- **Docs**: `https://seu-app.railway.app/docs`
- **Health**: `https://seu-app.railway.app/health`

### **Teste Rápido**
```bash
curl -X POST "https://seu-app.railway.app/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Teste do Nino", "consultation_type": "consultation"}'
```

---

🇧🇷 **Nino pronto para auxiliar advogados brasileiros na nuvem!** ⚖️