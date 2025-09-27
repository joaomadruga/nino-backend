# 🚀 Deployment no Railway - Nino

## Variáveis de Ambiente Necessárias

Configure as seguintes variáveis no Railway:

### ✅ Obrigatórias
```
DATABASE_URL=postgresql://user:password@host:port/database
HUGGINGFACE_HUB_TOKEN=seu_token_aqui
```

### ⚙️ Opcionais (já têm valores padrão)
```
MODEL_NAME=Jurema-br/Jurema-7B
MAX_NEW_TOKENS=1024
DEBUG=false
```

## 📝 Passos para Deploy

### 1. Conectar Repositório
- Conecte este repositório no Railway
- O Railway detectará automaticamente o `Dockerfile`

### 2. Configurar PostgreSQL
- Adicione o plugin PostgreSQL no Railway
- A variável `DATABASE_URL` será criada automaticamente

### 3. Configurar Variáveis
No painel do Railway, adicione:
- `HUGGINGFACE_HUB_TOKEN`: Seu token do Hugging Face

### 4. Deploy
- O Railway fará o build automaticamente
- A aplicação estará disponível na URL fornecida

## 🔧 Recursos Necessários

**Importante**: Este modelo precisa de recursos significativos:
- **GPU**: Recomendado para boa performance
- **RAM**: Mínimo 8GB, recomendado 16GB+
- **CPU**: Multi-core recomendado

## 📱 Frontend Streamlit

Para o frontend Streamlit em separado:

1. Crie um novo projeto no Railway
2. Use o repositório com apenas a pasta `frontend/`
3. Configure a variável:
   ```
   API_BASE_URL=https://sua-api-url-do-railway.up.railway.app
   ```

## ⚠️ Limitações do Railway

- **Tier Gratuito**: Limitado em recursos (pode não suportar o Jurema-7B)
- **Tier Pro**: Recomendado para modelos grandes
- **Timeout**: Pode precisar ajustar timeouts para primeiras requisições

## 🔍 Troubleshooting

### Erro de Memória
- Upgrade para tier com mais RAM
- Considere modelos menores para testes

### Timeout no Health Check
- Primeira inicialização pode demorar (download do modelo)
- Health check timeout está configurado para 300s

### Frontend não conecta
- Verifique se `API_BASE_URL` está correto
- Certifique-se que a API está funcionando: `https://sua-url/health`