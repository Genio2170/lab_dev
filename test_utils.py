#!/usr/bin/env python3
"""
Teste dos Módulos Utils - Demonstração das funcionalidades
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import *
from datetime import datetime
import json

def test_ai_utils():
    """Testa funcionalidades de IA"""
    print("🤖 TESTANDO AI_UTILS")
    print("=" * 40)
    
    # Teste de resumo
    article_text = """
    A inteligência artificial tem revolucionado diversos setores da economia mundial. 
    Empresas de tecnologia investem bilhões em pesquisa e desenvolvimento de algoritmos 
    cada vez mais sofisticados. O machine learning permite que sistemas aprendam com 
    dados históricos e façam previsões precisas sobre tendências futuras. Esta tecnologia 
    está sendo aplicada em áreas como medicina, finanças, educação e entretenimento.
    """
    
    summary, source = summarize_article(article_text, "IA Revoluciona Economia")
    print(f"📝 Resumo gerado ({source}):")
    print(f"   {summary}")
    
    # Teste de análise de padrões
    reading_history = [
        {"category": "Tecnologia", "reading_time_minutes": 5, "is_favorite": True},
        {"category": "Ciência", "reading_time_minutes": 8, "is_favorite": False},
        {"category": "Tecnologia", "reading_time_minutes": 6, "is_favorite": False},
        {"category": "Saúde", "reading_time_minutes": 4, "is_favorite": True},
    ]
    
    patterns = analyze_user_patterns(1, reading_history)
    print(f"\n📊 Análise de padrões:")
    print(f"   Artigos lidos: {patterns['total_articles_read']}")
    print(f"   Categoria favorita: {patterns['favorite_category']}")
    print(f"   Tempo médio: {patterns.get('average_reading_time', 'N/A')} min")
    
    return True

def test_validation():
    """Testa funcionalidades de validação"""
    print("\n✅ TESTANDO VALIDATION")
    print("=" * 40)
    
    # Teste de validação de artigo
    article_data = {
        "title": "Novidades em Python 3.12",
        "url": "https://python.org/news",
        "description": "Principais novidades da versão 3.12 do Python",
        "publishedAt": "2024-04-29T10:00:00Z",
        "source": {"name": "Python.org"},
        "category": "tecnologia"
    }
    
    validation = validate_article_data(article_data)
    print(f"📰 Validação de artigo:")
    print(f"   Válido: {validation['valid']}")
    if validation['errors']:
        print(f"   Erros: {validation['errors']}")
    if validation['warnings']:
        print(f"   Avisos: {validation['warnings']}")
    
    # Teste de validação de busca
    search_validation = validate_search_input("inteligência artificial", 1, 10)
    print(f"\n🔍 Validação de busca:")
    print(f"   Válida: {search_validation['valid']}")
    
    # Teste de sanitização
    dirty_text = "<script>alert('xss')</script>Texto limpo aqui"
    clean = sanitize_user_input(dirty_text)
    print(f"\n🧹 Sanitização:")
    print(f"   Original: {dirty_text}")
    print(f"   Limpo: {clean}")
    
    return True

def test_error_handler():
    """Testa tratamento de erros"""
    print("\n⚠️ TESTANDO ERROR_HANDLER")
    print("=" * 40)
    
    # Teste de erro customizado
    try:
        raise create_validation_error("Dados inválidos", {"field": "email"})
    except AppError as e:
        error_response = error_handler.handle_error(e)
        print(f"🚨 Erro tratado:")
        print(f"   Sucesso: {error_response['success']}")
        print(f"   Mensagem: {error_response['error']['message']}")
        print(f"   Tipo: {error_response['error']['type']}")
    
    # Teste de função segura
    def funcao_que_falha():
        raise ValueError("Ops, algo deu errado!")
    
    resultado = safe_execute(funcao_que_falha, default_return="Valor padrão")
    print(f"\n🛡️ Execução segura:")
    print(f"   Resultado: {resultado}")
    
    # Teste de resposta de sucesso
    success_response = format_success_response(
        data={"users": 150, "articles": 2500},
        message="Dados carregados com sucesso"
    )
    print(f"\n✅ Resposta de sucesso:")
    print(f"   Formato: {success_response}")
    
    return True

def test_helpers():
    """Testa funções auxiliares"""
    print("\n🛠️ TESTANDO HELPERS")
    print("=" * 40)
    
    # Teste de formatação de data
    now = datetime.now()
    date_formats = {
        "Completa": format_date(now, "full"),
        "Curta": format_date(now, "short"),
        "Relativa": format_date(now, "relative")
    }
    
    print("📅 Formatação de datas:")
    for formato, resultado in date_formats.items():
        print(f"   {formato}: {resultado}")
    
    # Teste de limpeza de texto
    html_text = "<h1>Título</h1><p>Parágrafo com <b>negrito</b> e <i>itálico</i></p>"
    clean = clean_text(html_text)
    print(f"\n🧹 Limpeza de HTML:")
    print(f"   Original: {html_text}")
    print(f"   Limpo: {clean}")
    
    # Teste de normalização
    texto_acentuado = "Programação em Python é fantástica!"
    normalizado = normalize_string(texto_acentuado)
    print(f"\n🔤 Normalização:")
    print(f"   Original: {texto_acentuado}")
    print(f"   Normalizado: {normalizado}")
    
    # Teste de token seguro
    token = generate_token(16)
    print(f"\n🔐 Token gerado: {token}")
    
    # Teste de acesso aninhado
    data = {
        "user": {
            "profile": {
                "name": "João Silva",
                "email": "joao@email.com"
            }
        }
    }
    
    name = get_nested_value(data, "user.profile.name", "Nome não encontrado")
    missing = get_nested_value(data, "user.settings.theme", "Padrão")
    
    print(f"\n📋 Acesso aninhado:")
    print(f"   Nome: {name}")
    print(f"   Tema: {missing}")
    
    # Teste de extração de palavras-chave
    text = "Python é uma linguagem de programação versátil e poderosa"
    keywords = TextHelper.extract_keywords(text)
    print(f"\n🔍 Palavras-chave extraídas: {keywords}")
    
    return True

def test_integration():
    """Testa integração entre módulos"""
    print("\n🔗 TESTANDO INTEGRAÇÃO")
    print("=" * 40)
    
    # Simula fluxo completo: validação → processamento → resposta
    input_data = {
        "query": "python programação",
        "page": 1,
        "limit": 5
    }
    
    # 1. Validação
    validation = validate_search_input(
        input_data["query"], 
        input_data["page"], 
        input_data["limit"]
    )
    
    if not validation["valid"]:
        error_response = format_success_response(
            data=None,
            message="Dados de entrada inválidos"
        )
        print(f"❌ Validação falhou: {error_response}")
        return False
    
    # 2. Processamento (simulado)
    try:
        # Simula busca
        results = [
            {
                "title": "Python para Iniciantes",
                "url": "https://example.com/python-init",
                "description": "Guia completo de Python",
                "publishedAt": datetime.now().isoformat()
            }
        ]
        
        # 3. Formatação da resposta
        response = format_success_response(
            data={
                "results": results,
                "total": len(results),
                "query": input_data["query"]
            },
            message="Busca realizada com sucesso"
        )
        
        print(f"✅ Integração bem-sucedida:")
        print(f"   Query: {input_data['query']}")
        print(f"   Resultados: {len(results)}")
        print(f"   Timestamp: {response['timestamp']}")
        
        return True
        
    except Exception as e:
        error_response = error_handler.handle_error(e)
        print(f"💥 Erro na integração: {error_response}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE COMPLETO DOS MÓDULOS UTILS")
    print("=" * 50)
    
    tests = [
        ("AI Utils", test_ai_utils),
        ("Validation", test_validation), 
        ("Error Handler", test_error_handler),
        ("Helpers", test_helpers),
        ("Integração", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "✅ PASSOU" if result else "❌ FALHOU"))
        except Exception as e:
            results.append((test_name, f"💥 ERRO: {e}"))
    
    # Resumo
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 50)
    for test_name, result in results:
        print(f"{test_name:15} → {result}")
    
    # Informações do pacote
    print(f"\n📦 INFORMAÇÕES DO PACOTE UTILS")
    print("=" * 50)
    info = get_utils_info()
    print(f"Versão: {info['version']}")
    print(f"Autor: {info['author']}")
    print(f"Funções: {info['total_functions']}")
    print(f"\nMódulos disponíveis:")
    for module in info['modules']:
        print(f"  • {module}")
    
    print(f"\n🎉 UTILS PRONTOS PARA USO!")
    print("📚 Para usar nos módulos backend:")
    print("   from utils import ai_service, validate_article_data, error_handler")
    print("   from utils import format_success_response, clean_text")

if __name__ == "__main__":
    main()