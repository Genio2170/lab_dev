#!/usr/bin/env python3
"""
Script para criar usuários de teste no sistema NeuralNews
"""

from backend.register import RegisterManager
from backend.auth import AuthManager
import sys

def create_test_users():
    """Cria usuários de teste para desenvolvimento"""
    
    register_manager = RegisterManager()
    
    test_users = [
        {
            'full_name': 'Utilizador Teste',
            'email': 'teste@neuralnews.com',
            'password': 'Teste123456'
        },
        {
            'full_name': 'Admin Sistema',
            'email': 'admin@neuralnews.com', 
            'password': 'Admin123456'
        },
        {
            'full_name': 'João Silva Santos',
            'email': 'joao@exemplo.com',
            'password': 'Password123'
        },
        {
            'full_name': 'Maria Fernanda Costa',
            'email': 'maria@exemplo.com',
            'password': 'Maria123456'
        }
    ]
    
    print("👥 Criando usuários de teste...")
    print("-" * 40)
    
    created_count = 0
    
    for user_data in test_users:
        success, message = register_manager.create_user(
            user_data['full_name'],
            user_data['email'],
            user_data['password'],
            user_data['password']  # confirm_password
        )
        
        if success:
            print(f"✓ {user_data['full_name']} ({user_data['email']})")
            created_count += 1
        else:
            if "já está registado" in message:
                print(f"⚪ {user_data['full_name']} ({user_data['email']}) - já existe")
            else:
                print(f"❌ {user_data['full_name']} - Erro: {message}")
    
    print("-" * 40)
    print(f"🎉 {created_count} usuários criados com sucesso!")
    
    if created_count > 0:
        print("\n🔐 Credenciais de teste:")
        for user_data in test_users:
            print(f"   📧 {user_data['email']}")
            print(f"   🔒 {user_data['password']}")
            print("   ---")

def show_all_users():
    """Mostra todos os usuários registados no sistema"""
    
    auth_manager = AuthManager()
    
    if not auth_manager.db.conectar():
        print("❌ Erro de conexão com a base de dados")
        return
    
    try:
        users = auth_manager.db.buscar("""
            SELECT id, full_name, email, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        
        print("👥 Usuários registados no sistema:")
        print("-" * 60)
        
        if not users:
            print("❌ Nenhum usuário encontrado")
            return
        
        for user in users:
            user_id, name, email, created_at = user
            print(f"🆔 ID: {user_id}")
            print(f"👤 Nome: {name}")
            print(f"📧 Email: {email}")
            print(f"📅 Criado: {created_at}")
            print("-" * 30)
        
        print(f"📊 Total: {len(users)} usuários")
        
    except Exception as e:
        print(f"❌ Erro ao buscar usuários: {e}")
    
    finally:
        auth_manager.db.desconectar()

def delete_test_users():
    """Remove usuários de teste"""
    
    auth_manager = AuthManager()
    
    test_emails = [
        'teste@neuralnews.com',
        'admin@neuralnews.com', 
        'joao@exemplo.com',
        'maria@exemplo.com'
    ]
    
    if not auth_manager.db.conectar():
        print("❌ Erro de conexão com a base de dados")
        return
    
    print("🗑️  Removendo usuários de teste...")
    print("-" * 40)
    
    try:
        for email in test_emails:
            # Primeiro buscar o usuário
            user_data = auth_manager.db.buscar("SELECT id, full_name FROM users WHERE email = ?", (email,))
            
            if user_data:
                user_id, name = user_data[0]
                
                # Remover sessões do usuário
                auth_manager.db.executar("DELETE FROM sessions WHERE user_id = ?", (user_id,))
                
                # Remover preferências do usuário
                auth_manager.db.executar("DELETE FROM preferences WHERE user_id = ?", (user_id,))
                
                # Remover o usuário
                auth_manager.db.executar("DELETE FROM users WHERE id = ?", (user_id,))
                
                print(f"🗑️  Removido: {name} ({email})")
            else:
                print(f"⚪ Não encontrado: {email}")
        
        print("-" * 40)
        print("✅ Usuários de teste removidos!")
        
    except Exception as e:
        print(f"❌ Erro ao remover usuários: {e}")
    
    finally:
        auth_manager.db.desconectar()

def show_register_stats():
    """Mostra estatísticas de registro"""
    
    register_manager = RegisterManager()
    stats, message = register_manager.get_user_stats()
    
    if stats:
        print("📊 Estatísticas de Registro:")
        print("-" * 30)
        print(f"👥 Total de usuários: {stats['total']}")
        print(f"🆕 Registos hoje: {stats['today']}")
        print(f"📅 Últimos 7 dias: {stats['week']}")
    else:
        print(f"❌ Erro ao obter estatísticas: {message}")

if __name__ == "__main__":
    print("=" * 50)
    print("👥 NEURAL NEWS - Gestão de Usuários de Teste")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            create_test_users()
        elif command == "list":
            show_all_users()
        elif command == "delete":
            delete_test_users()
        elif command == "stats":
            show_register_stats()
        else:
            print("❌ Comando inválido!")
            print("💡 Uso: python test_users.py [create|list|delete|stats]")
    else:
        print("📋 Comandos disponíveis:")
        print("   create - Criar usuários de teste")
        print("   list   - Listar todos os usuários")
        print("   delete - Remover usuários de teste")
        print("   stats  - Mostrar estatísticas de registro")
        print()
        print("💡 Exemplo: python test_users.py create")