# 🧠 Neural News

Sistema inteligente de notícias com autenticação, consumo de APIs e funcionalidades avançadas de IA para resumos automáticos e recomendações personalizadas.

## 🏗️ Arquitetura do Projeto

```
neural-news/
├── 📱 frontend/                 # Interface do usuário
│   ├── templates/               # Templates HTML
│   │   ├── home.html           # Página inicial
│   │   ├── login.html          # Login de usuário
│   │   ├── register.html       # Registro de usuário
│   │   └── panel/              # Páginas protegidas
│   │       ├── dashboard.html  # Dashboard principal
│   │       ├── article.html    # Visualização de artigos
│   │       ├── favorites.html  # Artigos favoritos
│   │       └── preferences.html # Preferências do usuário
│   └── static/                 # Arquivos estáticos
│       ├── css/               # Estilos CSS
│       └── js/                # Scripts JavaScript
├── 🔧 backend/                 # Lógica de negócio
│   ├── auth.py                # Sistema de autenticação
│   ├── register.py            # Sistema de registro
│   ├── main.py               # Módulo principal (planejado)
│   ├── news_api.py           # Consumo de APIs de notícias
│   ├── categories.py         # Organização por categorias
│   ├── preferences.py        # Gestão de preferências
│   └── favorites.py          # Sistema de favoritos
├── 🛠️ utils/                  # Módulos auxiliares (NOVO!)
│   ├── ai_utils.py           # 🤖 IA e resumos automáticos
│   ├── validation.py         # ✅ Validação de dados
│   ├── error_handler.py      # ⚠️ Tratamento de erros
│   ├── helpers.py            # 🔧 Utilitários gerais
│   ├── requirements.txt      # Dependências específicas
│   └── README.md            # Documentação detalhada
├── 🗄️ database/              # Camada de dados
│   ├── bd.py                # Conexão com banco
│   ├── function_sql.py      # Funções SQL
│   └── Explicacao_SQL.txt   # Documentação do BD
├── 📋 app.py                 # Aplicação Flask principal
├── 🧪 test_*.py             # Scripts de teste
└── 📖 README.md             # Este arquivo
```

## ✨ Principais Funcionalidades

### 🔐 **Sistema de Autenticação Completo**
- ✅ Login seguro com validação
- ✅ Registro de usuários com verificação
- ✅ Gestão de sessões com tokens seguros
- ✅ Proteção de rotas sensíveis
- ✅ Interface em português brasileiro

### 📰 **Consumo Inteligente de Notícias**
- 🔄 Integração com APIs de notícias
- 🏷️ Categorização automática
- 🔍 Sistema de busca avançado
- 📊 Filtros por data, categoria e fonte

### 🤖 **Inteligência Artificial**
- 📝 **Resumos automáticos** usando OpenAI, Claude ou Gemini
- 🎯 **Recomendações personalizadas** baseadas em preferências
- 📈 **Análise de padrões** de leitura do usuário
- 💡 **Insights inteligentes** sobre comportamento

### 👤 **Experiência Personalizada**
- ⭐ Sistema de favoritos
- ⚙️ Preferências customizáveis
- 📱 Interface responsiva
- 🎨 Design moderno e intuitivo

## 🚀 Configuração e Instalação

### 1️⃣ **Pré-requisitos**
```bash
# Python 3.8+ requerido
python --version

# Verificar pip
pip --version
```

### 2️⃣ **Instalação das Dependências**
```bash
# Dependências principais
pip install flask werkzeug

# Dependências dos módulos auxiliares (opcional, para IA)
pip install -r utils/requirements.txt
```

### 3️⃣ **Configuração do Banco de Dados**
```bash
# Inicializar banco SQLite
python database/bd.py

# Criar tabelas e dados de teste
python init_db.py
```

### 4️⃣ **Configuração de APIs (Opcional)**
Para funcionalidades de IA, configure as chaves:
```bash
# No Windows
set OPENAI_API_KEY=sua_chave_openai
set CLAUDE_API_KEY=sua_chave_claude
set GEMINI_API_KEY=sua_chave_gemini

# No Linux/Mac
export OPENAI_API_KEY="sua_chave_openai"
export CLAUDE_API_KEY="sua_chave_claude"
export GEMINI_API_KEY="sua_chave_gemini"
```

### 5️⃣ **Execução**
```bash
# Iniciar servidor Flask
python app.py

# Acesse: http://localhost:5000
```

## 🔧 Módulos Auxiliares (Utils)

A pasta **utils/** contém módulos especializados que apoiam todo o backend:

### 🤖 **ai_utils.py** - Inteligência Artificial
```python
from utils import summarize_article, get_recommendations

# Gerar resumo automático
summary, source = summarize_article(article_text, title)

# Obter recomendações personalizadas  
recommendations = get_recommendations(user_id, preferences, recent_articles, available)
```

### ✅ **validation.py** - Validação Robusta
```python
from utils import validate_article_data, sanitize_user_input

# Validar dados de artigos
validation = validate_article_data(article)

# Limpar entrada do usuário
clean_input = sanitize_user_input(user_text)
```

### ⚠️ **error_handler.py** - Tratamento de Erros
```python
from utils import api_error_handler, format_success_response

@api_error_handler
def minha_funcao():
    # Código com tratamento automático de erros
    return format_success_response(data=resultado)
```

### 🛠️ **helpers.py** - Utilitários Diversos
```python
from utils import format_date, clean_text, generate_token

# Formatação em português
data_pt = format_date(datetime.now(), "relative")  # "há 2 horas"

# Limpeza de HTML
texto_limpo = clean_text("<p>HTML aqui</p>")

# Token seguro
token = generate_token(32)
```

## 🧪 Testes e Validação

### **Testes do Sistema Principal**
```bash
# Testar autenticação
python test_auth_system.py

# Testar sistema completo
python test_complete_system.py
```

### **Testes dos Módulos Auxiliares**
```bash
# Testar todos os utils
python test_utils.py
```

### **Dados de Teste**
- 👤 **Usuário:** `teste_sistema@neuralnews.com`
- 🔒 **Senha:** `TesteSistema123`

## 📊 Status dos Módulos

| Módulo | Status | Funcionalidades |
|--------|--------|----------------|
| **auth.py** | ✅ Completo | Login, logout, sessões, proteção |
| **register.py** | ✅ Completo | Registro, validação, verificações |
| **app.py** | ✅ Completo | Rotas, APIs, integração frontend |
| **utils/** | ✅ Completo | IA, validação, erros, helpers |
| **news_api.py** | 🟡 Planejado | Consumo APIs, tratamento dados |
| **categories.py** | 🟡 Planejado | Organização, filtros categorias |
| **preferences.py** | 🟡 Planejado | Gestão preferências usuário |
| **favorites.py** | 🟡 Planejado | Sistema favoritos, gestão listas |

## 🎯 Próximos Passos

### 📰 **Módulos de Notícias**
1. **news_api.py** → Consumo e tratamento de APIs de notícias
2. **categories.py** → Lógica de categorização e filtragem
3. **preferences.py** → Gestão completa de preferências
4. **favorites.py** → Sistema robusto de favoritos

### 🚀 **Melhorias Futuras**
- 🌐 **Suporte a múltiplas linguagens**
- 📱 **App mobile (React Native)**
- 📈 **Analytics avançados**
- 🔔 **Sistema de notificações**
- 🤝 **Integração com redes sociais**

## 🏛️ Arquitetura Técnica

### **Stack Tecnológico**
- 🐍 **Backend:** Python + Flask
- 🗄️ **Banco:** SQLite (desenvolvimento) / PostgreSQL (produção)
- 🎨 **Frontend:** HTML5 + CSS3 + JavaScript vanilla
- 🤖 **IA:** OpenAI, Claude, Gemini APIs
- 🔐 **Segurança:** Werkzeug, tokens seguros, sanitização

### **Padrões de Código**
- ✅ **Arquitetura modular** com responsabilidades bem definidas
- ✅ **Tratamento robusto de erros** em todas as camadas
- ✅ **Validação consistente** de dados de entrada
- ✅ **Logging estruturado** para debugging
- ✅ **Código documentado** e testável

### **Performance e Escalabilidade**
- 🚀 **Cache inteligente** para APIs de IA
- ⚡ **Otimizações de banco** com índices apropriados
- 🔄 **Conexões reutilizáveis** para APIs externas
- 📊 **Paginação eficiente** para grandes datasets

## 🤝 Contribuição

### **Estrutura para Novos Módulos**
```python
# Exemplo de novo módulo no backend/
from utils import api_error_handler, validate_input, format_success_response

class NovoModulo:
    def __init__(self):
        # Inicialização
        pass
    
    @api_error_handler
    def metodo_principal(self, dados):
        # Validar entrada
        validation = validate_input(dados)
        if not validation['valid']:
            raise create_validation_error("Dados inválidos")
        
        # Lógica principal
        resultado = self.processar(dados)
        
        # Retorno padronizado
        return format_success_response(data=resultado)
```

## 📞 Suporte

- 📧 **Email:** dev@neuralnews.com
- 📚 **Documentação:** `/utils/README.md` para detalhes dos auxiliares
- 🐛 **Issues:** Relatar problemas via GitHub Issues
- 💬 **Discussões:** GitHub Discussions para ideias e dúvidas

---

## 🏆 **Neural News** - *Notícias Inteligentes para o Futuro* 🚀

> Sistema completo com autenticação segura, IA avançada e arquitetura modular para escalar com suas necessidades.

**Versão:** 1.0.0 | **Python:** 3.8+ | **Licença:** MIT