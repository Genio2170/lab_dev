#!/usr/bin/env python3
"""
Script para inicializar a base de dados do NeuralNews
Cria todas as tabelas necessárias para o sistema
"""

import sqlite3
import os
from database.bd import Conexao

def init_database():
    """Inicializa a base de dados criando todas as tabelas necessárias"""
    
    # Caminho para o arquivo de esquema
    schema_file = os.path.join('database', 'schema.db')
    
    # Conectar à base de dados
    db = Conexao()
    
    if not db.conectar():
        print("❌ Erro: Não foi possível conectar à base de dados")
        return False
    
    try:
        print("🔧 Inicializando base de dados...")
        
        # Ativar chaves estrangeiras
        db.executar("PRAGMA foreign_keys = ON")
        
        # Criar tabela categories
        db.executar("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        print("✓ Tabela 'categories' criada/verificada")
        
        # Criar tabela users
        db.executar("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Tabela 'users' criada/verificada")
        
        # Criar tabela news
        db.executar("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL UNIQUE,
                source TEXT,
                image_url TEXT,
                published_at DATETIME,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        print("✓ Tabela 'news' criada/verificada")
        
        # Criar tabela preferences
        db.executar("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                UNIQUE(user_id, category_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        print("✓ Tabela 'preferences' criada/verificada")
        
        # Criar tabela sessions
        db.executar("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("✓ Tabela 'sessions' criada/verificada")
        
        # Inserir categorias padrão se não existirem
        default_categories = [
            'Tecnologia',
            'Negócios', 
            'Ciência',
            'Política',
            'Desporto',
            'Entretenimento',
            'Saúde',
            'Educação',
            'Ambiente',
            'África'
        ]
        
        for category in default_categories:
            # Verificar se categoria já existe
            existing = db.buscar("SELECT id FROM categories WHERE name = ?", (category,))
            if not existing:
                db.executar("INSERT INTO categories (name) VALUES (?)", (category,))
                print(f"✓ Categoria '{category}' adicionada")
        
        print("\n🎉 Base de dados inicializada com sucesso!")
        print("📊 Tabelas criadas: categories, users, news, preferences, sessions")
        print(f"🗂️  Categorias disponíveis: {len(default_categories)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar base de dados: {e}")
        return False
        
    finally:
        db.desconectar()

def check_database_status():
    """Verifica o status da base de dados"""
    
    db = Conexao()
    
    if not db.conectar():
        print("❌ Não foi possível conectar à base de dados")
        return False
    
    try:
        # Verificar tabelas
        tables = db.buscar("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        print(f"📋 Tabelas encontradas: {len(tables)}")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Verificar usuários
        users_count = db.buscar("SELECT COUNT(*) FROM users")
        print(f"👥 Usuários registados: {users_count[0][0] if users_count else 0}")
        
        # Verificar categorias
        categories_count = db.buscar("SELECT COUNT(*) FROM categories") 
        print(f"🏷️  Categorias disponíveis: {categories_count[0][0] if categories_count else 0}")
        
        # Verificar sessões ativas
        sessions_count = db.buscar("""
            SELECT COUNT(*) FROM sessions 
            WHERE expires_at > datetime('now')
        """)
        print(f"🔐 Sessões ativas: {sessions_count[0][0] if sessions_count else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return False
        
    finally:
        db.desconectar()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 NEURAL NEWS - Inicializador de Base de Dados")
    print("=" * 50)
    
    # Criar diretório database se não existir
    os.makedirs('database', exist_ok=True)
    
    # Inicializar base de dados
    if init_database():
        print("\n" + "-" * 30)
        print("📊 STATUS DA BASE DE DADOS:")
        print("-" * 30)
        check_database_status()
        
        print("\n✅ Sistema pronto para uso!")
        print("💡 Execute 'python app.py' para iniciar o servidor")
    else:
        print("\n❌ Falha na inicialização")
        print("🔧 Verifique as permissões e tente novamente")