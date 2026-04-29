# 📂 Utils - Módulos Auxiliares

Pasta contendo módulos auxiliares que dão suporte ao backend do **Neural News**. Estes módulos centralizam funcionalidades reutilizáveis e mantêm o código principal limpo e organizado.

## 📋 Estrutura dos Módulos

### 🤖 `ai_utils.py` - Funcionalidades Inteligentes
**Funcionalidade:** Integração com APIs de IA para resumos automáticos e recomendações personalizadas.

**Principais recursos:**
- 📝 **Resumos automáticos** de artigos usando OpenAI, Claude ou Gemini
- 🎯 **Recomendações personalizadas** baseadas em preferências do usuário
- 📊 **Análise de padrões** de leitura 
- 🗂️ **Cache inteligente** para otimizar chamadas de API

**Exemplo de uso:**
```python
from utils import summarize_article, get_recommendations

# Gerar resumo de artigo
summary, source = summarize_article(
    text="Texto completo do artigo...",
    title="Título do Artigo",
    max_length=150
)

# Obter recomendações para usuário
recommendations = get_recommendations(
    user_id=123,
    preferences=["tecnologia", "ciência"],
    recent_articles=recent_read,
    available_articles=all_articles
)
```

### ✅ `validation.py` - Validação de Dados
**Funcionalidade:** Validação robusta de dados recebidos do frontend e APIs externas.

**Principais recursos:**
- 🔍 **Validação de artigos** da API de notícias
- 📝 **Validação de entrada** do usuário (queries, formulários)
- 🌐 **Validação de URLs** e formatos
- 🧹 **Sanitização automática** de dados

**Exemplo de uso:**
```python
from utils import validate_article_data, sanitize_user_input

# Validar dados de artigo
validation = validate_article_data({
    "title": "Título do artigo",
    "url": "https://site.com/artigo",
    "publishedAt": "2024-04-29T10:00:00Z"
})

if validation['valid']:
    print("Artigo válido!")
else:
    print(f"Erros: {validation['errors']}")

# Sanitizar entrada do usuário
clean_input = sanitize_user_input(user_text)
```

### ⚠️ `error_handler.py` - Tratamento de Erros
**Funcionalidade:** Sistema padronizado de tratamento e logging de erros.

**Principais recursos:**
- 🏷️ **Categorização de erros** (validação, rede, API, DB, etc.)
- 📊 **Níveis de severidade** (low, medium, high, critical)
- 📝 **Logging estruturado** com contexto
- 🛡️ **Decorators** para tratamento automático

**Exemplo de uso:**
```python
from utils import api_error_handler, create_validation_error, format_success_response

# Decorator para APIs
@api_error_handler
def buscar_noticias(query):
    if not query:
        raise create_validation_error("Query não pode estar vazia")
    
    # Lógica da busca...
    return format_success_response(data=results)

# Uso direto do handler
try:
    resultado = operacao_perigosa()
except Exception as e:
    return error_handler.handle_error(e)
```

### 🛠️ `helpers.py` - Utilitários Gerais
**Funcionalidade:** Funções auxiliares para formatação, normalização e manipulação de dados.

**Principais recursos:**
- 📅 **Formatação de datas** em português
- 🔤 **Normalização de texto** (remoção de acentos, HTML)
- 🔐 **Utilitários de segurança** (tokens, hashing)
- 🌐 **Manipulação de URLs**
- 📊 **Helpers para dados** (paginação, agrupamento)

**Exemplo de uso:**
```python
from utils import format_date, clean_text, generate_token, get_nested_value

# Formatação de data
data_formatada = format_date(datetime.now(), "relative")  # "há 2 horas"

# Limpeza de HTML
texto_limpo = clean_text("<p>Texto com <b>HTML</b></p>")

# Token seguro
token = generate_token(32)

# Acesso aninhado seguro
nome = get_nested_value(dados, "user.profile.name", "Padrão")
```

## 🚀 Como Usar

### Instalação de Dependências
```bash
# Instalar dependências específicas dos utils
pip install -r utils/requirements.txt
```

### Importação nos Módulos Backend
```python
# Importação específica
from utils.ai_utils import summarize_article, get_recommendations
from utils.validation import validate_article_data
from utils.error_handler import api_error_handler, create_api_error
from utils.helpers import format_date, clean_text

# Importação geral (recomendado)
from utils import (
    summarize_article,
    validate_article_data,
    api_error_handler,
    format_success_response,
    clean_text
)
```

## 🔗 Integração com Backend

### No `news_api.py`:
```python
from utils import validate_api_response, summarize_article, create_api_error

def processar_artigos(articles_data):
    # Validar resposta da API
    validation = validate_api_response(articles_data, "news_api")
    if not validation['valid']:
        raise create_api_error("Dados inválidos da API")
    
    # Processar artigos
    for article in articles_data['articles']:
        summary, _ = summarize_article(article['content'], article['title'])
        article['summary'] = summary
    
    return articles_data
```

### No `preferences.py`:
```python
from utils import validate_user_preferences, analyze_user_patterns

def salvar_preferencias(user_id, preferences_data):
    # Validar dados
    validation = validate_user_preferences(preferences_data)
    if not validation['valid']:
        return {'error': validation['errors']}
    
    # Analisar padrões
    patterns = analyze_user_patterns(user_id, reading_history)
    
    # Salvar...
```

### No `favorites.py`:
```python
from utils import api_error_handler, format_success_response

@api_error_handler
def adicionar_favorito(user_id, article_id):
    # Lógica para adicionar favorito
    result = database.add_favorite(user_id, article_id)
    
    return format_success_response(
        data=result,
        message="Artigo adicionado aos favoritos"
    )
```

## 🧪 Testes

Execute o teste completo dos utils:
```bash
python test_utils.py
```

O teste verifica:
- ✅ Funcionalidades de IA (resumos, recomendações)
- ✅ Validação de dados
- ✅ Tratamento de erros
- ✅ Utilitários diversos
- ✅ Integração entre módulos

## ⚙️ Configuração

### Variáveis de Ambiente (para IA)
```bash
# Para funcionalidades de IA (opcionais)
export OPENAI_API_KEY="sua_chave_openai"
export CLAUDE_API_KEY="sua_chave_claude"
export GEMINI_API_KEY="sua_chave_gemini"
```

**Nota:** Se nenhuma API key for configurada, o sistema usa fallback automático para resumos básicos.

## 📈 Benefícios da Arquitetura

### ✨ **Reutilização**
- Funções centralizadas evitam duplicação de código
- Padrões consistentes em todo o backend

### 🛡️ **Robustez**
- Tratamento padronizado de erros
- Validação consistente de dados
- Logging estruturado

### 🚀 **Performance**
- Cache inteligente para APIs de IA
- Funções otimizadas para texto e data

### 📚 **Manutenibilidade**
- Código backend mais limpo
- Lógica auxiliar separada
- Fácil para testes unitários

### 🔮 **Extensibilidade**
- Fácil adição de novas funcionalidades de IA
- Validadores modulares
- Sistema de erros flexível

## 📊 Estatísticas

- **4 módulos** principais
- **50+ funções** auxiliares
- **Compatível** com Python 3.8+
- **Suporte** a múltiplas APIs de IA
- **Validação** robusta para 15+ tipos de dados
- **Tratamento** de 10+ tipos de erro
- **25+ utilitários** para texto, data e segurança

---

*Os módulos utils formam a fundação robusta do Neural News, garantindo código limpo, seguro e extensível.* 🏗️✨