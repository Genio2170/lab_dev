#!/usr/bin/env python3
"""
Utils Package - Módulos auxiliares do Neural News
Centraliza funcionalidades de apoio ao backend
"""

# Importações principais para facilitar uso
from .ai_utils import (
    ai_service,
    summarize_article,
    get_recommendations,
    analyze_user_patterns
)

from .validation import (
    validate_article_data,
    validate_search_input,
    validate_api_response,
    sanitize_user_input,
    ValidationResult,
    NewsApiValidator,
    UserInputValidator,
    ApiResponseValidator
)

from .error_handler import (
    error_handler,
    AppError,
    ErrorType,
    ErrorSeverity,
    handle_errors,
    api_error_handler,
    create_validation_error,
    create_network_error,
    create_api_error,
    create_not_found_error,
    create_authentication_error,
    create_permission_error,
    create_database_error,
    create_rate_limit_error,
    format_success_response,
    safe_execute
)

from .helpers import (
    DateHelper,
    TextHelper,
    SecurityHelper,
    UrlHelper,
    DataHelper,
    JsonHelper,
    format_date,
    clean_text,
    normalize_string,
    generate_token,
    get_nested_value
)

# Versão do pacote
__version__ = "1.0.0"

# Metadados
__author__ = "Neural News Team"
__email__ = "dev@neuralnews.com"
__description__ = "Módulos auxiliares para o sistema Neural News"

# Exports principais
__all__ = [
    # AI Utils
    'ai_service',
    'summarize_article',
    'get_recommendations',
    'analyze_user_patterns',
    
    # Validation
    'validate_article_data',
    'validate_search_input',
    'validate_api_response',
    'sanitize_user_input',
    'ValidationResult',
    'NewsApiValidator',
    'UserInputValidator',
    'ApiResponseValidator',
    
    # Error Handler
    'error_handler',
    'AppError',
    'ErrorType',
    'ErrorSeverity',
    'handle_errors',
    'api_error_handler',
    'create_validation_error',
    'create_network_error',
    'create_api_error',
    'create_not_found_error',
    'create_authentication_error',
    'create_permission_error',
    'create_database_error',
    'create_rate_limit_error',
    'format_success_response',
    'safe_execute',
    
    # Helpers
    'DateHelper',
    'TextHelper',
    'SecurityHelper',
    'UrlHelper',
    'DataHelper',
    'JsonHelper',
    'format_date',
    'clean_text',
    'normalize_string',
    'generate_token',
    'get_nested_value'
]

def get_utils_info():
    """Retorna informações sobre o pacote utils"""
    return {
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'description': __description__,
        'modules': [
            'ai_utils - Funcionalidades de IA para resumos e recomendações',
            'validation - Validação de dados e entrada do usuário',
            'error_handler - Tratamento padronizado de erros',
            'helpers - Utilitários gerais e formatação'
        ],
        'total_functions': len(__all__)
    }