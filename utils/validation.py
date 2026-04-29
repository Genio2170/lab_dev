#!/usr/bin/env python3
"""
Validation Utils - Módulo para validação de dados
Funções para validar dados recebidos do frontend e APIs externas
"""

import re
import urllib.parse
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from email.utils import parseaddr
import json

class ValidationResult:
    """Resultado de validação com detalhes"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Adiciona erro e marca como inválido"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Adiciona aviso (não invalida)"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings
        }

class NewsApiValidator:
    """Validador para dados da API de notícias"""
    
    @staticmethod
    def validate_article(article_data: Dict) -> ValidationResult:
        """
        Valida dados de um artigo da API
        
        Args:
            article_data: Dicionário com dados do artigo
            
        Returns:
            ValidationResult com resultado da validação
        """
        result = ValidationResult(True)
        
        # Campos obrigatórios
        required_fields = ['title', 'url']
        for field in required_fields:
            if not article_data.get(field):
                result.add_error(f"Campo obrigatório ausente: {field}")
        
        # Validação do título
        title = article_data.get('title', '')
        if title:
            if len(title) < 10:
                result.add_warning("Título muito curto (menos de 10 caracteres)")
            elif len(title) > 200:
                result.add_error("Título muito longo (mais de 200 caracteres)")
            
            # Verifica se não é apenas espaços ou caracteres especiais
            if not re.search(r'[a-zA-Z0-9àáâãäçéêëíîïñóôõöùúûüýÀÁÂÃÄÇÉÊËÍÎÏÑÓÔÕÖÙÚÛÜÝ]', title):
                result.add_error("Título não contém caracteres válidos")
        
        # Validação da URL
        url = article_data.get('url', '')
        if url:
            url_validation = NewsApiValidator.validate_url(url)
            if not url_validation.is_valid:
                result.errors.extend(url_validation.errors)
        
        # Validação da descrição (opcional mas recomendada)
        description = article_data.get('description', '')
        if description:
            if len(description) > 1000:
                result.add_error("Descrição muito longa (mais de 1000 caracteres)")
        else:
            result.add_warning("Artigo sem descrição")
        
        # Validação da data de publicação
        published_at = article_data.get('publishedAt') or article_data.get('published_at')
        if published_at:
            date_validation = NewsApiValidator.validate_date(published_at)
            if not date_validation.is_valid:
                result.errors.extend(date_validation.errors)
        
        # Validação da fonte
        source = article_data.get('source', {})
        if isinstance(source, dict):
            if not source.get('name'):
                result.add_warning("Fonte sem nome identificado")
        elif isinstance(source, str):
            if not source.strip():
                result.add_warning("Nome da fonte vazio")
        
        # Validação da categoria
        category = article_data.get('category', '')
        if category:
            category_validation = NewsApiValidator.validate_category(category)
            if not category_validation.is_valid:
                result.warnings.extend(category_validation.errors)  # Categoria é warning, não erro
        
        # Validação da imagem
        image_url = article_data.get('urlToImage') or article_data.get('image_url')
        if image_url:
            img_validation = NewsApiValidator.validate_image_url(image_url)
            if not img_validation.is_valid:
                result.warnings.extend(img_validation.errors)  # Imagem é warning
        
        return result
    
    @staticmethod
    def validate_url(url: str) -> ValidationResult:
        """Valida formato de URL"""
        result = ValidationResult(True)
        
        if not url:
            result.add_error("URL não pode estar vazia")
            return result
        
        # Verifica formato básico
        url_pattern = re.compile(
            r'^https?://'  # http:// ou https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domínio
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # porta opcional
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            result.add_error("Formato de URL inválido")
        
        # Verifica comprimento
        if len(url) > 2000:
            result.add_error("URL muito longa (mais de 2000 caracteres)")
        
        # Verifica se não contém caracteres suspeitos
        if any(char in url for char in ['<', '>', '"', "'"]):
            result.add_error("URL contém caracteres inválidos")
        
        return result
    
    @staticmethod
    def validate_image_url(image_url: str) -> ValidationResult:
        """Valida URL de imagem"""
        result = NewsApiValidator.validate_url(image_url)
        
        if result.is_valid:
            # Verifica extensão de imagem
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']
            url_lower = image_url.lower()
            
            # Remove query parameters para check da extensão
            clean_url = url_lower.split('?')[0]
            
            has_valid_extension = any(clean_url.endswith(ext) for ext in valid_extensions)
            
            # Algumas URLs de imagem não têm extensão mas podem ser válidas
            if not has_valid_extension:
                # Verifica se contém palavras-chave de imagem
                image_keywords = ['image', 'img', 'photo', 'picture', 'thumbnail', 'avatar']
                has_image_keyword = any(keyword in url_lower for keyword in image_keywords)
                
                if not has_image_keyword:
                    result.add_warning("URL pode não ser uma imagem válida")
        
        return result
    
    @staticmethod
    def validate_date(date_string: str) -> ValidationResult:
        """Valida formato de data"""
        result = ValidationResult(True)
        
        if not date_string:
            result.add_error("Data não pode estar vazia")
            return result
        
        # Formatos aceitos
        date_formats = [
            '%Y-%m-%dT%H:%M:%SZ',  # ISO 8601 UTC
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO 8601 UTC com microsegundos
            '%Y-%m-%dT%H:%M:%S%z',  # ISO 8601 com timezone
            '%Y-%m-%d %H:%M:%S',  # Formato simples
            '%Y-%m-%d',  # Apenas data
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_string, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            result.add_error(f"Formato de data inválido: {date_string}")
            return result
        
        # Verifica se a data não é muito antiga ou futura
        now = datetime.now()
        one_year_ago = now - timedelta(days=365)
        one_month_ahead = now + timedelta(days=30)
        
        if parsed_date < one_year_ago:
            result.add_warning("Artigo com mais de 1 ano")
        elif parsed_date > one_month_ahead:
            result.add_error("Data de publicação no futuro é inválida")
        
        return result
    
    @staticmethod
    def validate_category(category: str) -> ValidationResult:
        """Valida categoria do artigo"""
        result = ValidationResult(True)
        
        if not category:
            return result  # Categoria é opcional
        
        # Lista de categorias válidas
        valid_categories = [
            'tecnologia', 'ciência', 'saúde', 'esportes', 'entretenimento',
            'negócios', 'política', 'mundo', 'brasil', 'economia',
            'educação', 'cultura', 'meio ambiente', 'geral'
        ]
        
        category_lower = category.lower().strip()
        
        # Mapeamento de categorias em inglês para português
        english_mapping = {
            'technology': 'tecnologia',
            'science': 'ciência', 
            'health': 'saúde',
            'sports': 'esportes',
            'entertainment': 'entretenimento',
            'business': 'negócios',
            'politics': 'política',
            'world': 'mundo',
            'general': 'geral'
        }
        
        # Tenta mapear se for inglês
        if category_lower in english_mapping:
            return result  # Válida, será mapeada depois
        
        # Verifica se é uma categoria válida em português
        if category_lower not in valid_categories:
            result.add_warning(f"Categoria '{category}' não está na lista padrão")
        
        return result

class UserInputValidator:
    """Validador para entrada de dados do usuário"""
    
    @staticmethod
    def validate_search_query(query: str) -> ValidationResult:
        """Valida query de busca"""
        result = ValidationResult(True)
        
        if not query or not query.strip():
            result.add_error("Query de busca não pode estar vazia")
            return result
        
        query = query.strip()
        
        # Comprimento
        if len(query) < 2:
            result.add_error("Query muito curta (mínimo 2 caracteres)")
        elif len(query) > 100:
            result.add_error("Query muito longa (máximo 100 caracteres)")
        
        # Verifica caracteres suspeitos (possível injeção)
        suspicious_chars = ['<script', '<iframe', 'javascript:', 'data:', 'vbscript:']
        query_lower = query.lower()
        
        for suspicious in suspicious_chars:
            if suspicious in query_lower:
                result.add_error("Query contém caracteres não permitidos")
                break
        
        # Verifica se não é apenas espaços ou caracteres especiais
        if not re.search(r'[a-zA-Z0-9àáâãäçéêëíîïñóôõöùúûüýÀÁÂÃÄÇÉÊËÍÎÏÑÓÔÕÖÙÚÛÜÝ]', query):
            result.add_error("Query deve conter pelo menos um caractere alfanumérico")
        
        return result
    
    @staticmethod
    def validate_pagination(page: Any, limit: Any) -> ValidationResult:
        """Valida parâmetros de paginação"""
        result = ValidationResult(True)
        
        # Validar página
        try:
            page_num = int(page) if page is not None else 1
            if page_num < 1:
                result.add_error("Número da página deve ser maior que 0")
            elif page_num > 1000:
                result.add_error("Número da página muito alto (máximo 1000)")
        except (ValueError, TypeError):
            result.add_error("Número da página deve ser um inteiro válido")
        
        # Validar limite
        try:
            limit_num = int(limit) if limit is not None else 10
            if limit_num < 1:
                result.add_error("Limite deve ser maior que 0")
            elif limit_num > 100:
                result.add_error("Limite muito alto (máximo 100)")
        except (ValueError, TypeError):
            result.add_error("Limite deve ser um inteiro válido")
        
        return result
    
    @staticmethod
    def validate_user_preferences(preferences_data: Dict) -> ValidationResult:
        """Valida dados de preferências do usuário"""
        result = ValidationResult(True)
        
        # Valida categorias preferidas
        categories = preferences_data.get('categories', [])
        if categories:
            if not isinstance(categories, list):
                result.add_error("Categorias devem ser uma lista")
            else:
                if len(categories) > 10:
                    result.add_error("Máximo 10 categorias permitidas")
                
                for category in categories:
                    if not isinstance(category, str):
                        result.add_error("Cada categoria deve ser uma string")
                    elif len(category.strip()) < 2:
                        result.add_error("Nome da categoria muito curto")
        
        # Valida fontes preferidas
        sources = preferences_data.get('sources', [])
        if sources:
            if not isinstance(sources, list):
                result.add_error("Fontes devem ser uma lista")
            else:
                if len(sources) > 20:
                    result.add_error("Máximo 20 fontes permitidas")
                
                for source in sources:
                    if not isinstance(source, str):
                        result.add_error("Cada fonte deve ser uma string")
                    elif len(source.strip()) < 2:
                        result.add_error("Nome da fonte muito curto")
        
        # Valida configurações de notificação
        notifications = preferences_data.get('notifications', {})
        if notifications and isinstance(notifications, dict):
            email_enabled = notifications.get('email_enabled')
            if email_enabled is not None and not isinstance(email_enabled, bool):
                result.add_error("'email_enabled' deve ser booleano")
            
            frequency = notifications.get('frequency')
            if frequency and frequency not in ['daily', 'weekly', 'never']:
                result.add_error("Frequência de notificação inválida")
        
        return result

class ApiResponseValidator:
    """Validador para respostas de APIs externas"""
    
    @staticmethod
    def validate_json_response(response_data: Any) -> ValidationResult:
        """Valida se a resposta é um JSON válido"""
        result = ValidationResult(True)
        
        if response_data is None:
            result.add_error("Resposta não pode ser nula")
            return result
        
        # Verifica se é um dicionário válido
        if not isinstance(response_data, dict):
            result.add_error("Resposta deve ser um objeto JSON")
            return result
        
        # Verifica estrutura básica esperada
        if 'status' in response_data:
            status = response_data['status']
            if status not in ['ok', 'error']:
                result.add_warning(f"Status '{status}' pode não ser padrão")
        
        return result
    
    @staticmethod
    def validate_news_api_response(response_data: Dict) -> ValidationResult:
        """Valida resposta específica da News API"""
        result = ApiResponseValidator.validate_json_response(response_data)
        
        if not result.is_valid:
            return result
        
        # Verifica campos esperados da News API
        if 'articles' not in response_data:
            result.add_error("Resposta deve conter campo 'articles'")
            return result
        
        articles = response_data['articles']
        if not isinstance(articles, list):
            result.add_error("Campo 'articles' deve ser uma lista")
            return result
        
        # Valida cada artigo
        for i, article in enumerate(articles[:5]):  # Valida apenas os primeiros 5
            article_validation = NewsApiValidator.validate_article(article)
            if not article_validation.is_valid:
                for error in article_validation.errors:
                    result.add_error(f"Artigo {i+1}: {error}")
            
            # Warnings não invalidam a resposta completa
            for warning in article_validation.warnings:
                result.add_warning(f"Artigo {i+1}: {warning}")
        
        return result

# Funções de conveniência
def validate_article_data(article: Dict) -> Dict:
    """Função de conveniência para validar artigo"""
    validation = NewsApiValidator.validate_article(article)
    return validation.to_dict()

def validate_search_input(query: str, page: int = 1, limit: int = 10) -> Dict:
    """Função de conveniência para validar entrada de busca"""
    query_validation = UserInputValidator.validate_search_query(query)
    pagination_validation = UserInputValidator.validate_pagination(page, limit)
    
    # Combina resultados
    combined_result = ValidationResult(
        query_validation.is_valid and pagination_validation.is_valid,
        query_validation.errors + pagination_validation.errors,
        query_validation.warnings + pagination_validation.warnings
    )
    
    return combined_result.to_dict()

def validate_api_response(response: Dict, api_type: str = 'generic') -> Dict:
    """Função de conveniência para validar resposta de API"""
    if api_type == 'news_api':
        validation = ApiResponseValidator.validate_news_api_response(response)
    else:
        validation = ApiResponseValidator.validate_json_response(response)
    
    return validation.to_dict()

def sanitize_user_input(text: str, max_length: int = 500) -> str:
    """
    Sanitiza entrada do usuário removendo caracteres perigosos
    
    Args:
        text: Texto a ser sanitizado
        max_length: Comprimento máximo permitido
        
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Remove tags HTML
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove caracteres de controle
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Remove múltiplos espaços
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Trunca se necessário
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0] + '...'
    
    return text