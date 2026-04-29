#!/usr/bin/env python3
"""
Script de teste para verificar funcionamento do login e registro
"""

from backend.auth import AuthManager  
from backend.register import RegisterManager
import time

def test_auth_system():
    """Testa todo o sistema de autenticação"""
    print("🧪 TESTE DO SISTEMA DE AUTENTICAÇÃO")
    print("=" * 50)
    
    auth_manager = AuthManager()
    register_manager = RegisterManager()
    
    # Dados de teste
    test_user = {
        'full_name': 'Teste Sistema',
        'email': 'teste_sistema@neuralnews.com',
        'password': 'TesteSistema123'
    }
    
    print("1️⃣ Testando Registro de Usuário...")
    print("-" * 30)
    
    # Teste de registro
    success, message = register_manager.create_user(
        test_user['full_name'],
        test_user['email'], 
        test_user['password'],
        test_user['password']  # confirm_password
    )
    
    if success:
        print(f"✅ Registro: {message}")
    else:
        if "já está registado" in message:
            print(f"⚪ Registro: Usuário já existe, continuando...")
        else:
            print(f"❌ Registro falhou: {message}")
            return False
    
    print("\n2️⃣ Testando Login...")
    print("-" * 30)
    
    # Teste de login
    user_info, message = auth_manager.authenticate_user(
        test_user['email'],
        test_user['password']
    )
    
    if user_info:
        print(f"✅ Login: {message}")
        print(f"   👤 Nome: {user_info['full_name']}")
        print(f"   📧 Email: {user_info['email']}")
        print(f"   🆔 ID: {user_info['id']}")
        
        print("\n3️⃣ Testando Criação de Sessão...")
        print("-" * 30)
        
        # Teste de sessão
        token, token_message = auth_manager.create_session_token(user_info['id'])
        
        if token:
            print(f"✅ Sessão criada: {token_message}")
            print(f"   🔑 Token: {token[:20]}...")
            
            print("\n4️⃣ Testando Validação de Sessão...")
            print("-" * 30)
            
            # Teste de validação de sessão
            session_user, session_message = auth_manager.validate_session_token(token)
            
            if session_user:
                print(f"✅ Validação: {session_message}")
                print(f"   👤 Nome: {session_user['full_name']}")
                
                print("\n5️⃣ Testando Logout...")
                print("-" * 30)
                
                # Teste de logout
                logout_success, logout_message = auth_manager.invalidate_session(token)
                
                if logout_success:
                    print(f"✅ Logout: {logout_message}")
                    
                    # Verificar se sessão foi realmente invalidada
                    invalid_check, invalid_message = auth_manager.validate_session_token(token)
                    if not invalid_check:
                        print(f"✅ Verificação: Sessão invalidada corretamente")
                    else:
                        print(f"❌ Verificação: Sessão ainda válida (erro)")
                        return False
                else:
                    print(f"❌ Logout falhou: {logout_message}")
                    return False
            else:
                print(f"❌ Validação de sessão falhou: {session_message}")
                return False
        else:
            print(f"❌ Criação de sessão falhou: {token_message}")
            return False
    else:
        print(f"❌ Login falhou: {message}")
        return False
    
    print("\n6️⃣ Testando Validações...")
    print("-" * 30)
    
    # Teste de validações
    test_validations(register_manager)
    
    print("\n" + "=" * 50)
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("✅ Sistema de autenticação funcionando corretamente")
    return True

def test_validations(register_manager):
    """Testa as validações do sistema"""
    
    # Teste de email inválido
    valid_email = register_manager.validate_email('email_invalido')
    print(f"📧 Email inválido: {'❌' if not valid_email else '⚠️'}")
    
    valid_email = register_manager.validate_email('teste@exemplo.com')
    print(f"📧 Email válido: {'✅' if valid_email else '❌'}")
    
    # Teste de senha fraca
    password_valid, errors = register_manager.validate_password('123')
    print(f"🔒 Senha fraca: {'❌' if not password_valid else '⚠️'} ({len(errors)} erros)")
    
    password_valid, errors = register_manager.validate_password('SenhaForte123')
    print(f"🔒 Senha forte: {'✅' if password_valid else '❌'}")
    
    # Teste de nome inválido
    name_valid, message = register_manager.validate_full_name('João')
    print(f"👤 Nome incompleto: {'❌' if not name_valid else '⚠️'}")
    
    name_valid, message = register_manager.validate_full_name('João Silva')
    print(f"👤 Nome completo: {'✅' if name_valid else '❌'}")

def test_registration_stats():
    """Testa estatísticas de registro"""
    print("\n📊 ESTATÍSTICAS DE REGISTRO")
    print("-" * 30)
    
    register_manager = RegisterManager()
    stats, message = register_manager.get_user_stats()
    
    if stats:
        print(f"👥 Total de usuários: {stats['total']}")
        print(f"🆕 Registos hoje: {stats['today']}")
        print(f"📅 Últimos 7 dias: {stats['week']}")
    else:
        print(f"❌ Erro ao obter estatísticas: {message}")

if __name__ == "__main__":
    print("🚀 Iniciando testes do sistema...")
    time.sleep(1)
    
    try:
        # Executar testes principais
        if test_auth_system():
            # Mostrar estatísticas
            test_registration_stats()
            
            print("\n💡 Para testar no navegador:")
            print("   1. Execute: python app.py")
            print("   2. Acesse: http://localhost:5000")
            print("   3. Teste login e registro")
            
        else:
            print("\n❌ Alguns testes falharam!")
            
    except Exception as e:
        print(f"\n💥 Erro durante os testes: {e}")
        print("🔧 Verifique se a base de dados foi inicializada:")
        print("   python init_db.py")