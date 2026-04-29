# Sistema de Autenticação NeuralNews 🔐

## Estrutura Reorganizada

A funcionalidade de autenticação foi reorganizada em módulos especializados:

### 📁 Estrutura dos Arquivos

```
backend/
├── auth.py      # ✅ Autenticação e sessões
└── register.py  # ✅ Registro de usuários
```

## 🚀 Como Usar

### 1. Inicialização da Base de Dados

```bash
# Criar todas as tabelas e categorias padrão
python init_db.py
```

### 2. Criar Usuários de Teste

```bash
# Criar usuários de teste
python test_users.py create

# Listar todos os usuários
python test_users.py list

# Ver estatísticas
python test_users.py stats

# Remover usuários de teste
python test_users.py delete
```

### 3. Executar a Aplicação

```bash
python app.py
```

Acesse: `http://localhost:5000`

## 📋 Funcionalidades Implementadas

### 🔑 Autenticação (auth.py)

- **Login seguro**: Email e palavra-passe
- **Gestão de sessões**: Tokens seguros com expiração
- **Validação de sessões**: Verificação automática
- **Logout**: Invalidação de tokens
- **Proteção de rotas**: Decorador `@login_required`

### 👥 Registro (register.py)

- **Validação completa**: Email, senha, nome
- **Verificação de email**: Formato e disponibilidade
- **Força da senha**: Requisitos de segurança
- **Hash seguro**: Werkzeug para senhas
- **Estatísticas**: Dados de registos

## 🛡️ Requisitos de Segurança

### Palavra-passe deve ter:
- ✅ Mínimo 8 caracteres
- ✅ Pelo menos 1 maiúscula
- ✅ Pelo menos 1 minúscula  
- ✅ Pelo menos 1 número

### Nome completo deve ter:
- ✅ Mínimo 2 caracteres
- ✅ Nome e sobrenome
- ✅ Apenas letras e espaços

## 🌐 Rotas Disponíveis

### Páginas Web
- `GET /` - Página inicial
- `GET /login` - Formulário de login
- `POST /login` - Processar login
- `GET /register` - Formulário de registro
- `POST /register` - Processar registro
- `GET|POST /logout` - Logout
- `GET /artigos` - Dashboard (protegido)
- `GET /favoritos` - Favoritos (protegido)
- `GET /preferencias` - Preferências (protegido)

### API Endpoints
- `GET /api/user` - Informações do usuário
- `GET /api/session/validate` - Validar sessão
- `POST /api/register/validate` - Validar dados de registro
- `POST /api/register/check-email` - Verificar disponibilidade de email
- `GET /api/register/stats` - Estatísticas de registro

## 🔧 Configuração

### Variáveis de Ambiente
```bash
SECRET_KEY=sua_chave_secreta_aqui
```

### Base de Dados
- **SQLite**: `database/schema.db`
- **Tabelas**: users, categories, news, preferences, sessions

## 💡 Exemplos de Uso

### Login via JavaScript (AJAX)
```javascript
fetch('/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: 'teste@neuralnews.com',
        password: 'Teste123456',
        remember_me: true
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        window.location.href = data.redirect;
    }
});
```

### Registro via JavaScript (AJAX)
```javascript
fetch('/register', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        full_name: 'João Silva Santos',
        email: 'joao@exemplo.com',
        password: 'Password123',
        confirm_password: 'Password123',
        terms_accepted: true
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        window.location.href = data.redirect;
    }
});
```

### Uso em Python
```python
from backend.auth import AuthManager
from backend.register import RegisterManager

# Autenticação
auth = AuthManager()
user, message = auth.authenticate_user('email', 'password')

# Registro
register = RegisterManager()
success, message = register.create_user('Nome', 'email', 'password')
```

## 🔒 Fluxo de Segurança

1. **Login**: Email + senha → Hash verification → Token JWT
2. **Sessão**: Token armazenado → Validação a cada request
3. **Proteção**: Rotas protegidas verificam token válido
4. **Logout**: Token invalidado no servidor e cliente

## 📊 Monitoramento

### Verificar Logs
```python
# Ver usuários conectados
python test_users.py stats

# Ver todos os usuários
python test_users.py list
```

## 🐛 Resolução de Problemas

### Base de dados não existe
```bash
python init_db.py
```

### Usuários de teste não funcionam
```bash
python test_users.py delete
python test_users.py create
```

### Sessões inválidas
- Tokens expiram em 7 dias
- Logout limpa tokens do servidor

## 📝 Credenciais de Teste

Após executar `python test_users.py create`:

| Email | Palavra-passe | Nome |
|-------|---------------|------|
| `teste@neuralnews.com` | `Teste123456` | Utilizador Teste |
| `admin@neuralnews.com` | `Admin123456` | Admin Sistema |
| `joao@exemplo.com` | `Password123` | João Silva Santos |
| `maria@exemplo.com` | `Maria123456` | Maria Fernanda Costa |

---

🎉 **Sistema pronto para uso!** Execute `python app.py` e acesse `http://localhost:5000`