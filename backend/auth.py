from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import secrets
import sqlite3
from database.bd import Conexao

class AuthManager:
    def __init__(self):
        self.db = Conexao()
    
    def verify_password(self, password_hash, password):
        """Verifica se a senha corresponde ao hash"""
        return check_password_hash(password_hash, password)
    
    def authenticate_user(self, email, password):
        """Autentica usuário com email e senha"""
        try:
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            # Buscar usuário por email
            user_data = self.db.buscar(
                "SELECT id, full_name, email, password_hash FROM users WHERE email = ?", 
                (email,)
            )
            
            self.db.desconectar()
            
            if not user_data:
                return None, "Email ou palavra-passe incorretos"
            
            user = user_data[0]
            user_id, full_name, user_email, password_hash = user
            
            # Verificar senha
            if self.verify_password(password_hash, password):
                user_info = {
                    'id': user_id,
                    'full_name': full_name,
                    'email': user_email
                }
                return user_info, "Login realizado com sucesso"
            else:
                return None, "Email ou palavra-passe incorretos"
                
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return None, f"Erro na autenticação: {str(e)}"
    
    def create_session_token(self, user_id):
        """Cria token de sessão para o usuário"""
        try:
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            # Gerar token aleatório seguro
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)  # Token válido por 7 dias
            
            # Remover sessões antigas do usuário (opcional)
            self.db.executar(
                "DELETE FROM sessions WHERE user_id = ?",
                (user_id,)
            )
            
            # Inserir nova sessão
            self.db.executar(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires_at.isoformat())
            )
            
            self.db.desconectar()
            return token, "Sessão criada com sucesso"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return None, f"Erro ao criar sessão: {str(e)}"
    
    def validate_session_token(self, token):
        """Valida token de sessão e retorna informações do usuário"""
        try:
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            # Buscar sessão e usuário
            session_data = self.db.buscar("""
                SELECT s.user_id, s.expires_at, u.full_name, u.email 
                FROM sessions s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.token = ?
            """, (token,))
            
            self.db.desconectar()
            
            if not session_data:
                return None, "Sessão inválida"
            
            user_id, expires_at, full_name, email = session_data[0]
            
            # Verificar se sessão não expirou
            expires_datetime = datetime.fromisoformat(expires_at)
            if expires_datetime < datetime.now():
                self.invalidate_session(token)
                return None, "Sessão expirada"
            
            user_info = {
                'id': user_id,
                'full_name': full_name,
                'email': email
            }
            return user_info, "Sessão válida"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return None, f"Erro ao validar sessão: {str(e)}"
    
    def invalidate_session(self, token):
        """Remove token de sessão (logout)"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            self.db.executar(
                "DELETE FROM sessions WHERE token = ?",
                (token,)
            )
            
            self.db.desconectar()
            return True, "Sessão removida com sucesso"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return False, f"Erro ao remover sessão: {str(e)}"
    
    def get_user_by_id(self, user_id):
        """Busca usuário por ID"""
        try:
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            user_data = self.db.buscar(
                "SELECT id, full_name, email FROM users WHERE id = ?", 
                (user_id,)
            )
            
            self.db.desconectar()
            
            if user_data:
                user_id, full_name, email = user_data[0]
                return {
                    'id': user_id,
                    'full_name': full_name,
                    'email': email
                }, "Usuário encontrado"
            else:
                return None, "Usuário não encontrado"
                
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return None, f"Erro ao buscar usuário: {str(e)}"


# Função auxiliar para decorador de login obrigatório
def login_required(f):
    """Decorador para verificar se usuário está logado"""
    from functools import wraps
    from flask import session, redirect, url_for, request
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_token' not in session:
            return redirect(url_for('login', next=request.url))
        
        auth_manager = AuthManager()
        user_info, message = auth_manager.validate_session_token(session['session_token'])
        
        if not user_info:
            session.pop('session_token', None)
            return redirect(url_for('login'))
        
        # Adicionar informações do usuário ao contexto
        request.current_user = user_info
        return f(*args, **kwargs)
    
    return decorated_function