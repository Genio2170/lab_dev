#!/usr/bin/env python3
"""
Helpers - Módulo de utilitários gerais
Funções auxiliares para formatação, normalização e apoio ao backend
"""

import re
import html
import unicodedata
import hashlib
import secrets
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urljoin, quote, unquote
import locale
import base64

# Configuração de locale para português brasileiro
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except:
        pass  # Usa locale padrão

class DateHelper:
    """Utilitários para manipulação de datas"""
    
    @staticmethod
    def format_date_portuguese(date_obj: datetime, format_type: str = "full") -> str:
        """
        Formata data em português brasileiro
        
        Args:
            date_obj: Objeto datetime
            format_type: Tipo de formatação ("full", "short", "relative")
            
        Returns:
            Data formatada em português
        """
        if not isinstance(date_obj, datetime):
            return str(date_obj)
        
        if format_type == "full":
            # Ex: "15 de abril de 2024, 14:30"
            try:
                return date_obj.strftime("%d de %B de %Y, %H:%M")
            except:
                return date_obj.strftime("%d/%m/%Y %H:%M")
        
        elif format_type == "short":
            # Ex: "15/04/2024"
            return date_obj.strftime("%d/%m/%Y")
        
        elif format_type == "relative":
            # Ex: "há 2 horas", "ontem", "há 3 dias"
            return DateHelper.get_relative_time(date_obj)
        
        else:
            return date_obj.isoformat()
    
    @staticmethod
    def get_relative_time(date_obj: datetime) -> str:
        """Retorna tempo relativo em português"""
        now = datetime.now(timezone.utc)
        
        # Garantir que ambas as datas têm timezone
        if date_obj.tzinfo is None:
            date_obj = date_obj.replace(tzinfo=timezone.utc)
        
        diff = now - date_obj
        
        # Futuro
        if diff.total_seconds() < 0:
            diff = date_obj - now
            
            if diff.days > 0:
                return f"em {diff.days} dia{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"em {hours} hora{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"em {minutes} minuto{'s' if minutes > 1 else ''}"
            else:
                return "em breve"
        
        # Passado
        if diff.days > 365:
            years = diff.days // 365
            return f"há {years} ano{'s' if years > 1 else ''}"
        elif diff.days > 30:
            months = diff.days // 30
            return f"há {months} mês{'es' if months > 1 else ''}"
        elif diff.days > 0:
            if diff.days == 1:
                return "ontem"
            else:
                return f"há {diff.days} dias"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"há {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"há {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "agora"
    
    @staticmethod
    def parse_date_string(date_string: str) -> Optional[datetime]:
        """
        Tenta fazer parse de string de data em vários formatos
        
        Args:
            date_string: String de data
            
        Returns:
            Objeto datetime ou None se não conseguir fazer parse
        """
        if not date_string:
            return None
        
        # Formatos comuns
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',          # ISO 8601 UTC
            '%Y-%m-%dT%H:%M:%S.%fZ',       # ISO 8601 UTC com microsegundos
            '%Y-%m-%dT%H:%M:%S%z',         # ISO 8601 com timezone
            '%Y-%m-%dT%H:%M:%S',           # ISO 8601 sem timezone
            '%Y-%m-%d %H:%M:%S',           # Formato MySQL
            '%Y-%m-%d',                    # Apenas data
            '%d/%m/%Y %H:%M:%S',           # Formato brasileiro com hora
            '%d/%m/%Y',                    # Formato brasileiro
            '%d-%m-%Y %H:%M:%S',           # Formato alternativo
            '%d-%m-%Y',                    # Formato alternativo
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def get_date_range(period: str) -> Tuple[datetime, datetime]:
        """
        Retorna range de datas baseado no período
        
        Args:
            period: Período ("today", "week", "month", "year")
            
        Returns:
            Tuple com data inicial e final
        """
        now = datetime.now()
        
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(microseconds=1)
        
        elif period == "week":
            days_since_monday = now.weekday()
            start = now - timedelta(days=days_since_monday)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7) - timedelta(microseconds=1)
        
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1) - timedelta(microseconds=1)
            else:
                end = start.replace(month=now.month + 1) - timedelta(microseconds=1)
        
        elif period == "year":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=now.year + 1) - timedelta(microseconds=1)
        
        else:
            # Padrão: último mês
            start = now - timedelta(days=30)
            end = now
        
        return start, end

class TextHelper:
    """Utilitários para manipulação de texto"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza texto removendo acentos e caracteres especiais
        
        Args:
            text: Texto a ser normalizado
            
        Returns:
            Texto normalizado
        """
        if not text:
            return ""
        
        # Remove acentos
        normalized = unicodedata.normalize('NFD', text)
        normalized = ''.join(char for char in normalized 
                           if unicodedata.category(char) != 'Mn')
        
        return normalized
    
    @staticmethod
    def clean_html(html_text: str) -> str:
        """
        Remove tags HTML e entidades do texto
        
        Args:
            html_text: Texto com HTML
            
        Returns:
            Texto limpo
        """
        if not html_text:
            return ""
        
        # Remove tags HTML
        clean = re.sub(r'<[^>]*>', '', html_text)
        
        # Decodifica entidades HTML
        clean = html.unescape(clean)
        
        # Remove múltiplos espaços e quebras de linha
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Trunca texto mantendo palavras completas
        
        Args:
            text: Texto a ser truncado
            max_length: Comprimento máximo
            suffix: Sufixo para textos truncados
            
        Returns:
            Texto truncado
        """
        if not text or len(text) <= max_length:
            return text
        
        # Trunca no limite
        truncated = text[:max_length - len(suffix)]
        
        # Procura último espaço para não cortar palavra
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:  # Se o espaço está em mais de 70%
            truncated = truncated[:last_space]
        
        return truncated + suffix
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        Extrai palavras-chave do texto
        
        Args:
            text: Texto para análise
            max_keywords: Número máximo de palavras-chave
            
        Returns:
            Lista de palavras-chave
        """
        if not text:
            return []
        
        # Lista de stop words em português
        stop_words = {
            'a', 'o', 'e', 'é', 'de', 'do', 'da', 'em', 'um', 'uma', 'para',
            'com', 'não', 'se', 'na', 'por', 'mais', 'as', 'os', 'como',
            'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua',
            'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está',
            'eu', 'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela',
            'entre', 'era', 'depois', 'sem', 'mesmo', 'aos', 'ter', 'seus',
            'suas', 'num', 'numa', 'pelos', 'pelas', 'esse', 'esses',
            'essa', 'essas', 'outro', 'outros', 'outra', 'outras'
        }
        
        # Limpa e normaliza o texto
        clean_text = TextHelper.clean_html(text.lower())
        
        # Extrai palavras (apenas letras, mínimo 3 caracteres)
        words = re.findall(r'[a-záàâãéèêíìîóòôõúùûç]{3,}', clean_text)
        
        # Remove stop words
        keywords = [word for word in words if word not in stop_words]
        
        # Conta frequência
        word_count = {}
        for word in keywords:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Ordena por frequência e retorna as top
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, count in sorted_words[:max_keywords]]
    
    @staticmethod
    def generate_slug(text: str) -> str:
        """
        Gera slug URL-friendly a partir do texto
        
        Args:
            text: Texto original
            
        Returns:
            Slug normalizado
        """
        if not text:
            return ""
        
        # Normaliza e converte para minúsculas
        slug = TextHelper.normalize_text(text).lower()
        
        # Remove caracteres especiais e espaços
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug)
        
        # Remove hífens do início e fim
        slug = slug.strip('-')
        
        return slug

class SecurityHelper:
    """Utilitários para segurança"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Gera token seguro"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_string(text: str, algorithm: str = 'sha256') -> str:
        """
        Gera hash de string
        
        Args:
            text: Texto a ser hasheado
            algorithm: Algoritmo de hash
            
        Returns:
            Hash hexadecimal
        """
        if not text:
            return ""
        
        if algorithm == 'md5':
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(text.encode()).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(text.encode()).hexdigest()
        else:
            return hashlib.sha256(text.encode()).hexdigest()
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """
        Mascara dados sensíveis
        
        Args:
            data: Dados a serem mascarados
            mask_char: Caractere de máscara
            visible_chars: Caracteres visíveis no final
            
        Returns:
            Dados mascarados
        """
        if not data or len(data) <= visible_chars:
            return data
        
        masked_length = len(data) - visible_chars
        return mask_char * masked_length + data[-visible_chars:]

class UrlHelper:
    """Utilitários para URLs"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Verifica se URL é válida"""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except:
            return False
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extrai domínio da URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    @staticmethod
    def build_url(base_url: str, path: str, params: Dict[str, Any] = None) -> str:
        """
        Constrói URL com parâmetros
        
        Args:
            base_url: URL base
            path: Caminho
            params: Parâmetros de query
            
        Returns:
            URL completa
        """
        url = urljoin(base_url, path)
        
        if params:
            query_parts = []
            for key, value in params.items():
                if value is not None:
                    encoded_key = quote(str(key))
                    encoded_value = quote(str(value))
                    query_parts.append(f"{encoded_key}={encoded_value}")
            
            if query_parts:
                url += "?" + "&".join(query_parts)
        
        return url

class DataHelper:
    """Utilitários para manipulação de dados"""
    
    @staticmethod
    def safe_get(data: Dict, keys: str, default: Any = None) -> Any:
        """
        Acesso seguro a dados aninhados
        
        Args:
            data: Dicionário de dados
            keys: Chaves separadas por ponto (ex: "user.profile.name")
            default: Valor padrão
            
        Returns:
            Valor encontrado ou padrão
        """
        try:
            current = data
            for key in keys.split('.'):
                current = current[key]
            return current
        except (KeyError, TypeError, AttributeError):
            return default
    
    @staticmethod
    def flatten_dict(data: Dict, separator: str = '.', prefix: str = '') -> Dict:
        """
        Achata dicionário aninhado
        
        Args:
            data: Dicionário aninhado
            separator: Separador de chaves
            prefix: Prefixo para chaves
            
        Returns:
            Dicionário achatado
        """
        result = {}
        
        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(DataHelper.flatten_dict(value, separator, new_key))
            else:
                result[new_key] = value
        
        return result
    
    @staticmethod
    def group_by(data: List[Dict], key: str) -> Dict[Any, List[Dict]]:
        """
        Agrupa lista de dicionários por chave
        
        Args:
            data: Lista de dicionários
            key: Chave para agrupamento
            
        Returns:
            Dicionário agrupado
        """
        grouped = {}
        
        for item in data:
            group_key = item.get(key)
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(item)
        
        return grouped
    
    @staticmethod
    def paginate_data(data: List[Any], page: int = 1, per_page: int = 10) -> Dict:
        """
        Pagina lista de dados
        
        Args:
            data: Lista de dados
            page: Página atual (começa em 1)
            per_page: Itens por página
            
        Returns:
            Dados paginados com metadata
        """
        total = len(data)
        total_pages = (total + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            'data': data[start:end],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

class JsonHelper:
    """Utilitários para JSON"""
    
    @staticmethod
    def safe_json_load(json_string: str, default: Any = None) -> Any:
        """Carrega JSON com tratamento de erro"""
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dump(data: Any, indent: int = None, ensure_ascii: bool = False) -> str:
        """Serializa JSON com tratamento de erro"""
        try:
            return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, default=str)
        except (TypeError, ValueError):
            return "{}"

# Funções de conveniência
def format_date(date_obj: datetime, format_type: str = "full") -> str:
    """Função de conveniência para formatação de data"""
    return DateHelper.format_date_portuguese(date_obj, format_type)

def clean_text(text: str) -> str:
    """Função de conveniência para limpeza de texto"""
    return TextHelper.clean_html(text)

def normalize_string(text: str) -> str:
    """Função de conveniência para normalização"""
    return TextHelper.normalize_text(text)

def generate_token(length: int = 32) -> str:
    """Função de conveniência para geração de token"""
    return SecurityHelper.generate_secure_token(length)

def get_nested_value(data: Dict, path: str, default: Any = None) -> Any:
    """Função de conveniência para acesso aninhado"""
    return DataHelper.safe_get(data, path, default)