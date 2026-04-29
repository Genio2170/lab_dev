from werkzeug.security import generate_password_hash
from datetime import datetime
import re
from database.bd import Conexao

class RegisterManager:
    def __init__(self):
        self.db = Conexao()
    
    def hash_password(self, password):
        """Cria hash seguro da senha usando Werkzeug"""
        return generate_password_hash(password)
    
    def validate_email(self, email):
        """Valida formato do email"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def validate_password(self, password):
        """Valida força da palavra-passe"""
        errors = []
        
        if len(password) < 8:
            errors.append("A palavra-passe deve ter pelo menos 8 caracteres")
        
        if not re.search(r'[A-Z]', password):
            errors.append("A palavra-passe deve conter pelo menos uma letra maiúscula")
        
        if not re.search(r'[a-z]', password):
            errors.append("A palavra-passe deve conter pelo menos uma letra minúscula")
        
        if not re.search(r'\d', password):
            errors.append("A palavra-passe deve conter pelo menos um número")
        
        return len(errors) == 0, errors
    
    def validate_full_name(self, full_name):
        """Valida nome completo"""
        if not full_name or len(full_name.strip()) < 2:
            return False, "O nome deve ter pelo menos 2 caracteres"
        
        # Verificar se contém pelo menos nome e sobrenome
        name_parts = full_name.strip().split()
        if len(name_parts) < 2:
            return False, "Por favor insira o nome completo (nome e sobrenome)"
        
        # Verificar caracteres válidos
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', full_name):
            return False, "O nome deve conter apenas letras e espaços"
        
        return True, "Nome válido"
    
    def email_exists(self, email):
        """Verifica se email já está registado"""
        try:
            if not self.db.conectar():
                return True, "Erro de conexão com a base de dados"
            
            existing_user = self.db.buscar(
                "SELECT id FROM users WHERE email = ?", 
                (email.lower(),)
            )
            
            self.db.desconectar()
            return len(existing_user) > 0, "Email já está registado"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return True, f"Erro ao verificar email: {str(e)}"
    
    def create_user(self, full_name, email, password, confirm_password=None):
        """Cria novo usuário na base de dados com validações completas"""
        try:
            # Validações de entrada
            full_name = full_name.strip()
            email = email.strip().lower()
            
            # Validar nome completo
            name_valid, name_message = self.validate_full_name(full_name)
            if not name_valid:
                return False, name_message
            
            # Validar email
            if not self.validate_email(email):
                return False, "Formato de email inválido"
            
            # Verificar se email já existe
            exists, exists_message = self.email_exists(email)
            if exists:
                return False, exists_message
            
            # Validar confirmação de senha
            if confirm_password is not None and password != confirm_password:
                return False, "As palavras-passe não coincidem"
            
            # Validar força da senha
            password_valid, password_errors = self.validate_password(password)
            if not password_valid:
                return False, "\n".join(password_errors)
            
            # Conectar à base de dados
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Criar hash da senha
            password_hash = self.hash_password(password)
            
            # Inserir novo usuário
            self.db.executar(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (full_name, email, password_hash)
            )
            
            self.db.desconectar()
            return True, "Conta criada com sucesso! Pode agora fazer login."
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return False, f"Erro ao criar conta: {str(e)}"
    
    def get_user_stats(self):
        """Obtém estatísticas de usuários registados"""
        try:
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            # Total de usuários
            total_users = self.db.buscar("SELECT COUNT(*) FROM users")
            total = total_users[0][0] if total_users else 0
            
            # Usuários registados hoje
            today_users = self.db.buscar(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')"
            )
            today = today_users[0][0] if today_users else 0
            
            # Últimos 7 dias
            week_users = self.db.buscar(
                "SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')"
            )
            week = week_users[0][0] if week_users else 0
            
            self.db.desconectar()
            
            return {
                'total': total,
                'today': today,
                'week': week
            }, "Estatísticas obtidas com sucesso"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            return None, f"Erro ao obter estatísticas: {str(e)}"
    
    def validate_registration_data(self, data):
        """Valida todos os dados de registro de uma vez"""
        errors = {}
        
        # Validar nome
        if not data.get('full_name'):
            errors['full_name'] = 'Nome é obrigatório'
        else:
            name_valid, name_message = self.validate_full_name(data['full_name'])
            if not name_valid:
                errors['full_name'] = name_message
        
        # Validar email
        if not data.get('email'):
            errors['email'] = 'Email é obrigatório'
        elif not self.validate_email(data['email']):
            errors['email'] = 'Formato de email inválido'
        else:
            exists, exists_message = self.email_exists(data['email'])
            if exists:
                errors['email'] = exists_message
        
        # Validar senha
        if not data.get('password'):
            errors['password'] = 'Palavra-passe é obrigatória'
        else:
            password_valid, password_errors = self.validate_password(data['password'])
            if not password_valid:
                errors['password'] = password_errors[0]  # Primeiro erro apenas
        
        # Validar confirmação de senha
        if data.get('password') != data.get('confirm_password'):
            errors['confirm_password'] = 'As palavras-passe não coincidem'
        
        # Validar aceite de termos
        if not data.get('terms_accepted'):
            errors['terms'] = 'Deve aceitar os termos de uso'
        
        return len(errors) == 0, errors