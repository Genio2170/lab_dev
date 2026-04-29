#!/usr/bin/env python3
"""
Error Handler - Módulo para tratamento padronizado de erros
Garante respostas consistentes para falhas de rede, APIs e exceções internas
"""

import logging
import traceback
import sys
from functools import wraps
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
import json

class ErrorType(Enum):
    """Tipos de erro padronizados"""
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND = "not_found"
    INTERNAL_ERROR = "internal_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"

class ErrorSeverity(Enum):
    """Níveis de severidade do erro"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AppError(Exception):
    """Exceção customizada da aplicação"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.INTERNAL_ERROR, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Dict = None,
                 status_code: int = 500):
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.now()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        """Converte erro para dicionário"""
        return {
            'error': True,
            'message': self.message,
            'type': self.error_type.value,
            'severity': self.severity.value,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'status_code': self.status_code
        }

class ErrorLogger:
    """Logger especializado para erros"""
    
    def __init__(self):
        self.logger = logging.getLogger('neuralnews_errors')
        self.logger.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para arquivo
        try:
            file_handler = logging.FileHandler('logs/errors.log')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except:
            pass  # Se não conseguir criar arquivo, usa apenas console
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_error(self, error: AppError, context: Dict = None):
        """Registra erro no log"""
        context = context or {}
        
        error_data = {
            'message': error.message,
            'type': error.error_type.value,
            'severity': error.severity.value,
            'details': error.details,
            'context': context,
            'timestamp': error.timestamp.isoformat()
        }
        
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"ERRO {error.severity.value.upper()}: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        else:
            self.logger.warning(f"ERRO {error.severity.value.upper()}: {json.dumps(error_data, ensure_ascii=False)}")
    
    def log_exception(self, exc: Exception, context: Dict = None):
        """Registra exceção não tratada"""
        context = context or {}
        
        error_data = {
            'exception_type': exc.__class__.__name__,
            'message': str(exc),
            'traceback': traceback.format_exc(),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.error(f"EXCEÇÃO NÃO TRATADA: {json.dumps(error_data, ensure_ascii=False, indent=2)}")

class ErrorHandler:
    """Handler principal para tratamento de erros"""
    
    def __init__(self):
        self.logger = ErrorLogger()
        self.error_stats = {
            'total_errors': 0,
            'errors_by_type': {},
            'errors_by_severity': {}
        }
    
    def handle_error(self, error: Union[AppError, Exception], context: Dict = None) -> Dict:
        """
        Trata erro e retorna resposta padronizada
        
        Args:
            error: Erro a ser tratado
            context: Contexto adicional do erro
            
        Returns:
            Dicionário com resposta formatada
        """
        context = context or {}
        
        # Se não é AppError, converte
        if not isinstance(error, AppError):
            app_error = self._convert_exception_to_app_error(error)
        else:
            app_error = error
        
        # Log do erro
        self.logger.log_error(app_error, context)
        
        # Atualiza estatísticas
        self._update_stats(app_error)
        
        # Retorna resposta formatada
        return self._format_error_response(app_error)
    
    def _convert_exception_to_app_error(self, exc: Exception) -> AppError:
        """Converte exceção Python para AppError"""
        exc_type = exc.__class__.__name__
        
        # Mapeamento de exceções comuns
        error_mapping = {
            'ConnectionError': (ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM, 503),
            'TimeoutError': (ErrorType.TIMEOUT_ERROR, ErrorSeverity.MEDIUM, 408),
            'FileNotFoundError': (ErrorType.NOT_FOUND, ErrorSeverity.LOW, 404),
            'PermissionError': (ErrorType.PERMISSION_ERROR, ErrorSeverity.HIGH, 403),
            'ValueError': (ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW, 400),
            'KeyError': (ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW, 400),
            'TypeError': (ErrorType.VALIDATION_ERROR, ErrorSeverity.MEDIUM, 400),
            'AttributeError': (ErrorType.INTERNAL_ERROR, ErrorSeverity.HIGH, 500),
        }
        
        error_type, severity, status_code = error_mapping.get(
            exc_type, 
            (ErrorType.INTERNAL_ERROR, ErrorSeverity.HIGH, 500)
        )
        
        # Log da exceção original
        self.logger.log_exception(exc)
        
        return AppError(
            message=f"Erro interno: {str(exc)}",
            error_type=error_type,
            severity=severity,
            status_code=status_code,
            details={'exception_type': exc_type, 'original_message': str(exc)}
        )
    
    def _update_stats(self, error: AppError):
        """Atualiza estatísticas de erro"""
        self.error_stats['total_errors'] += 1
        
        # Por tipo
        error_type = error.error_type.value
        self.error_stats['errors_by_type'][error_type] = \
            self.error_stats['errors_by_type'].get(error_type, 0) + 1
        
        # Por severidade
        severity = error.severity.value
        self.error_stats['errors_by_severity'][severity] = \
            self.error_stats['errors_by_severity'].get(severity, 0) + 1
    
    def _format_error_response(self, error: AppError) -> Dict:
        """Formata resposta de erro"""
        return {
            'success': False,
            'error': {
                'message': error.message,
                'type': error.error_type.value,
                'code': error.status_code
            },
            'data': None,
            'timestamp': error.timestamp.isoformat()
        }
    
    def get_error_stats(self) -> Dict:
        """Retorna estatísticas de erro"""
        return self.error_stats.copy()

# Instância global
error_handler = ErrorHandler()

# Decorators para tratamento de erros
def handle_errors(error_type: ErrorType = ErrorType.INTERNAL_ERROR, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """
    Decorator para tratamento automático de erros
    
    Args:
        error_type: Tipo de erro padrão
        severity: Severidade padrão
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppError as e:
                # Re-propaga AppError
                raise e
            except Exception as e:
                # Converte exceção para AppError
                app_error = AppError(
                    message=f"Erro em {func.__name__}: {str(e)}",
                    error_type=error_type,
                    severity=severity,
                    details={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)}
                )
                raise app_error
        return wrapper
    return decorator

def api_error_handler(func):
    """Decorator específico para APIs"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Se a função retorna um dicionário, adiciona success=True
            if isinstance(result, dict) and 'success' not in result:
                result['success'] = True
                
            return result
            
        except AppError as e:
            return error_handler.handle_error(e, {'function': func.__name__})
        except Exception as e:
            return error_handler.handle_error(e, {'function': func.__name__})
    return wrapper

# Funções específicas para tipos de erro
def create_validation_error(message: str, details: Dict = None) -> AppError:
    """Cria erro de validação"""
    return AppError(
        message=message,
        error_type=ErrorType.VALIDATION_ERROR,
        severity=ErrorSeverity.LOW,
        status_code=400,
        details=details
    )

def create_network_error(message: str, details: Dict = None) -> AppError:
    """Cria erro de rede"""
    return AppError(
        message=message,
        error_type=ErrorType.NETWORK_ERROR,
        severity=ErrorSeverity.MEDIUM,
        status_code=503,
        details=details
    )

def create_api_error(message: str, api_name: str = None, status_code: int = 502, details: Dict = None) -> AppError:
    """Cria erro de API"""
    error_details = details or {}
    if api_name:
        error_details['api'] = api_name
        
    return AppError(
        message=message,
        error_type=ErrorType.API_ERROR,
        severity=ErrorSeverity.MEDIUM,
        status_code=status_code,
        details=error_details
    )

def create_not_found_error(resource: str, identifier: str = None) -> AppError:
    """Cria erro de recurso não encontrado"""
    message = f"{resource} não encontrado"
    if identifier:
        message += f": {identifier}"
        
    return AppError(
        message=message,
        error_type=ErrorType.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        status_code=404,
        details={'resource': resource, 'identifier': identifier}
    )

def create_authentication_error(message: str = "Falha na autenticação") -> AppError:
    """Cria erro de autenticação"""
    return AppError(
        message=message,
        error_type=ErrorType.AUTHENTICATION_ERROR,
        severity=ErrorSeverity.HIGH,
        status_code=401
    )

def create_permission_error(action: str = None) -> AppError:
    """Cria erro de permissão"""
    message = "Acesso negado"
    if action:
        message += f" para: {action}"
        
    return AppError(
        message=message,
        error_type=ErrorType.PERMISSION_ERROR,
        severity=ErrorSeverity.HIGH,
        status_code=403,
        details={'action': action}
    )

def create_database_error(operation: str, details: Dict = None) -> AppError:
    """Cria erro de banco de dados"""
    return AppError(
        message=f"Erro na operação de banco: {operation}",
        error_type=ErrorType.DATABASE_ERROR,
        severity=ErrorSeverity.HIGH,
        status_code=500,
        details=details
    )

def create_rate_limit_error(limit: int = None, window: str = None) -> AppError:
    """Cria erro de limite de taxa"""
    message = "Muitas solicitações"
    details = {}
    
    if limit and window:
        message += f" (máximo {limit} por {window})"
        details = {'limit': limit, 'window': window}
    
    return AppError(
        message=message,
        error_type=ErrorType.RATE_LIMIT_ERROR,
        severity=ErrorSeverity.MEDIUM,
        status_code=429,
        details=details
    )

# Funções utilitárias
def safe_execute(func, *args, default_return=None, log_errors=True, **kwargs):
    """
    Executa função com tratamento seguro de erros
    
    Args:
        func: Função a ser executada
        *args: Argumentos da função
        default_return: Valor padrão em caso de erro
        log_errors: Se deve logar erros
        **kwargs: Argumentos nomeados da função
        
    Returns:
        Resultado da função ou valor padrão
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            error_handler.logger.log_exception(e, {
                'function': getattr(func, '__name__', str(func)),
                'args': str(args),
                'kwargs': str(kwargs)
            })
        return default_return

def format_success_response(data: Any = None, message: str = None, meta: Dict = None) -> Dict:
    """
    Formata resposta de sucesso padronizada
    
    Args:
        data: Dados da resposta
        message: Mensagem de sucesso
        meta: Metadados adicionais
        
    Returns:
        Resposta formatada
    """
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    if message:
        response['message'] = message
    
    if meta:
        response['meta'] = meta
    
    return response

def validate_and_execute(validation_func, execute_func, *args, **kwargs):
    """
    Executa validação antes da função principal
    
    Args:
        validation_func: Função de validação
        execute_func: Função a ser executada
        *args: Argumentos das funções
        **kwargs: Argumentos nomeados
        
    Returns:
        Resultado da execução ou erro de validação
    """
    try:
        # Executar validação
        validation_result = validation_func(*args, **kwargs)
        
        if isinstance(validation_result, dict) and not validation_result.get('valid', True):
            raise create_validation_error(
                "Dados inválidos",
                details=validation_result
            )
        
        # Executar função principal
        return execute_func(*args, **kwargs)
        
    except AppError:
        raise
    except Exception as e:
        raise error_handler._convert_exception_to_app_error(e)