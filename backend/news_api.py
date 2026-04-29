import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urlparse
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAPIError(Exception):
    """Exceção personalizada para erros da API de notícias"""
    pass

class NewsAPIManager:
    """Gerenciador para consumo de APIs de notícias"""
    
    def __init__(self):
        # APIs disponíveis - você pode adicionar mais aqui
        self.api_configs = {
            'newsapi': {
                'base_url': 'https://newsapi.org/v2',
                'key_param': 'apiKey',
                'requires_key': True
            },
            'guardian': {
                'base_url': 'https://content.guardianapis.com',
                'key_param': 'api-key',
                'requires_key': True
            },
            'rss_feeds': {
                'base_url': None,  # URLs diretas dos feeds RSS
                'key_param': None,
                'requires_key': False
            }
        }
        
        # Cache simples para evitar muitas requisições
        self.cache = {}
        self.cache_duration = 300  # 5 minutos
        
        # Headers padrão para requisições
        self.headers = {
            'User-Agent': 'NeuralNews/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8'
        }
    
    def _make_request(self, url: str, params: Dict = None, timeout: int = 10) -> Dict:
        """Faz requisição HTTP com tratamento de erros"""
        try:
            response = requests.get(
                url, 
                params=params, 
                headers=self.headers, 
                timeout=timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise NewsAPIError("Timeout na requisição - API muito lenta")
        except requests.exceptions.ConnectionError:
            raise NewsAPIError("Erro de conexão - verificar internet")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise NewsAPIError("Chave de API inválida ou expirada")
            elif e.response.status_code == 429:
                raise NewsAPIError("Limite de requisições excedido - tente mais tarde")
            else:
                raise NewsAPIError(f"Erro HTTP {e.response.status_code}")
        except json.JSONDecodeError:
            raise NewsAPIError("Resposta da API inválida - formato JSON incorreto")
        except Exception as e:
            raise NewsAPIError(f"Erro inesperado: {str(e)}")
    
    def _get_cache_key(self, api_name: str, endpoint: str, params: Dict) -> str:
        """Gera chave única para cache"""
        param_str = json.dumps(params, sort_keys=True)
        return f"{api_name}:{endpoint}:{hash(param_str)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se cache ainda é válido"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return (time.time() - cached_time) < self.cache_duration
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Recupera dados do cache se válidos"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Salva dados no cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def fetch_newsapi_articles(self, api_key: str, category: str = None, 
                              country: str = 'pt', language: str = 'pt',
                              page_size: int = 20) -> Tuple[List[Dict], str]:
        """Busca artigos da NewsAPI.org"""
        
        if not api_key:
            return [], "Chave da API NewsAPI não fornecida"
        
        try:
            params = {
                'apiKey': api_key,
                'language': language,
                'country': country,
                'pageSize': min(page_size, 100),
                'sortBy': 'publishedAt'
            }
            
            if category and category != 'all':
                params['category'] = category
            
            # Verificar cache primeiro
            cache_key = self._get_cache_key('newsapi', 'top-headlines', params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return self._normalize_newsapi_articles(cached_data['articles']), "Cache"
            
            url = f"{self.api_configs['newsapi']['base_url']}/top-headlines"
            data = self._make_request(url, params)
            
            # Salvar no cache
            self._save_to_cache(cache_key, data)
            
            articles = self._normalize_newsapi_articles(data.get('articles', []))
            return articles, f"Sucesso - {data.get('totalResults', 0)} artigos encontrados"
            
        except NewsAPIError as e:
            logger.error(f"Erro NewsAPI: {e}")
            return [], str(e)
        except Exception as e:
            logger.error(f"Erro inesperado NewsAPI: {e}")
            return [], f"Erro inesperado: {str(e)}"
    
    def fetch_guardian_articles(self, api_key: str, section: str = None,
                               page_size: int = 20) -> Tuple[List[Dict], str]:
        """Busca artigos do The Guardian API"""
        
        if not api_key:
            return [], "Chave da API Guardian não fornecida"
        
        try:
            params = {
                'api-key': api_key,
                'page-size': min(page_size, 50),
                'order-by': 'newest',
                'show-fields': 'headline,thumbnail,bodyText,shortUrl',
                'show-tags': 'contributor'
            }
            
            if section:
                params['section'] = section
            
            # Verificar cache
            cache_key = self._get_cache_key('guardian', 'search', params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return self._normalize_guardian_articles(cached_data['results']), "Cache"
            
            url = f"{self.api_configs['guardian']['base_url']}/search"
            data = self._make_request(url, params)
            
            # Salvar no cache
            self._save_to_cache(cache_key, data['response'])
            
            articles = self._normalize_guardian_articles(data['response']['results'])
            return articles, f"Sucesso - {data['response']['total']} artigos encontrados"
            
        except NewsAPIError as e:
            logger.error(f"Erro Guardian: {e}")
            return [], str(e)
        except Exception as e:
            logger.error(f"Erro inesperado Guardian: {e}")
            return [], f"Erro inesperado: {str(e)}"
    
    def fetch_rss_articles(self, rss_urls: List[str], 
                          max_articles: int = 50) -> Tuple[List[Dict], str]:
        """Busca artigos de feeds RSS"""
        
        try:
            import feedparser
        except ImportError:
            return [], "Biblioteca feedparser não instalada - execute: pip install feedparser"
        
        all_articles = []
        successful_feeds = 0
        
        for rss_url in rss_urls[:5]:  # Limitar a 5 feeds por vez
            try:
                # Verificar cache
                cache_key = self._get_cache_key('rss', rss_url, {})
                cached_data = self._get_from_cache(cache_key)
                if cached_data:
                    all_articles.extend(cached_data)
                    successful_feeds += 1
                    continue
                
                feed = feedparser.parse(rss_url)
                
                if feed.bozo:
                    logger.warning(f"RSS mal formado: {rss_url}")
                    continue
                
                articles = self._normalize_rss_articles(feed.entries, rss_url)
                
                # Salvar no cache
                self._save_to_cache(cache_key, articles)
                
                all_articles.extend(articles)
                successful_feeds += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar RSS {rss_url}: {e}")
                continue
        
        # Ordenar por data e limitar
        all_articles.sort(key=lambda x: x['published_at'], reverse=True)
        all_articles = all_articles[:max_articles]
        
        return all_articles, f"Sucesso - {successful_feeds} feeds processados"
    
    def _normalize_newsapi_articles(self, articles: List[Dict]) -> List[Dict]:
        """Normaliza artigos da NewsAPI para formato padrão"""
        normalized = []
        
        for article in articles:
            try:
                normalized_article = {
                    'id': hash(article.get('url', '')),
                    'title': self._clean_text(article.get('title', '')),
                    'description': self._clean_text(article.get('description', '')),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'Fonte Desconhecida'),
                    'image_url': article.get('urlToImage'),
                    'published_at': self._parse_date(article.get('publishedAt')),
                    'author': article.get('author', 'Autor Desconhecido'),
                    'content': self._clean_text(article.get('content', ''))[:200] + '...',
                    'category': 'geral',  # NewsAPI não retorna categoria específica
                    'language': 'pt',
                    'api_source': 'newsapi'
                }
                
                if self._validate_article(normalized_article):
                    normalized.append(normalized_article)
                    
            except Exception as e:
                logger.warning(f"Erro ao normalizar artigo NewsAPI: {e}")
                continue
        
        return normalized
    
    def _normalize_guardian_articles(self, articles: List[Dict]) -> List[Dict]:
        """Normaliza artigos do Guardian para formato padrão"""
        normalized = []
        
        for article in articles:
            try:
                fields = article.get('fields', {})
                
                normalized_article = {
                    'id': hash(article.get('webUrl', '')),
                    'title': self._clean_text(article.get('webTitle', '')),
                    'description': self._clean_text(fields.get('bodyText', ''))[:300],
                    'url': article.get('webUrl', ''),
                    'source': 'The Guardian',
                    'image_url': fields.get('thumbnail'),
                    'published_at': self._parse_date(article.get('webPublicationDate')),
                    'author': self._extract_guardian_author(article.get('tags', [])),
                    'content': self._clean_text(fields.get('bodyText', ''))[:200] + '...',
                    'category': article.get('sectionName', 'geral').lower(),
                    'language': 'en',  # Guardian é em inglês
                    'api_source': 'guardian'
                }
                
                if self._validate_article(normalized_article):
                    normalized.append(normalized_article)
                    
            except Exception as e:
                logger.warning(f"Erro ao normalizar artigo Guardian: {e}")
                continue
        
        return normalized
    
    def _normalize_rss_articles(self, entries: List, source_url: str) -> List[Dict]:
        """Normaliza artigos RSS para formato padrão"""
        normalized = []
        source_domain = urlparse(source_url).netloc
        
        for entry in entries:
            try:
                normalized_article = {
                    'id': hash(entry.get('link', '')),
                    'title': self._clean_text(entry.get('title', '')),
                    'description': self._clean_text(entry.get('description', '') or entry.get('summary', '')),
                    'url': entry.get('link', ''),
                    'source': source_domain.replace('www.', '').title(),
                    'image_url': self._extract_rss_image(entry),
                    'published_at': self._parse_rss_date(entry),
                    'author': entry.get('author', 'Autor Desconhecido'),
                    'content': self._clean_text(entry.get('description', ''))[:200] + '...',
                    'category': self._extract_rss_category(entry),
                    'language': 'pt',  # Assumir português para feeds locais
                    'api_source': 'rss'
                }
                
                if self._validate_article(normalized_article):
                    normalized.append(normalized_article)
                    
            except Exception as e:
                logger.warning(f"Erro ao normalizar artigo RSS: {e}")
                continue
        
        return normalized
    
    def _clean_text(self, text: str) -> str:
        """Remove HTML e limpa texto"""
        if not text:
            return ''
        
        # Remover tags HTML básicas
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Limpar espaços excessivos
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _parse_date(self, date_str: str) -> datetime:
        """Converte string de data para datetime"""
        if not date_str:
            return datetime.now()
        
        try:
            # Formato ISO 8601
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Outros formatos comuns
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Se não conseguir parsear, usar data atual
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def _parse_rss_date(self, entry: Dict) -> datetime:
        """Converte data RSS para datetime"""
        date_fields = ['published', 'updated', 'created']
        
        for field in date_fields:
            if hasattr(entry, field):
                date_info = getattr(entry, field)
                if hasattr(date_info, 'tm_year'):
                    # struct_time
                    return datetime(*date_info[:6])
        
        return datetime.now()
    
    def _extract_guardian_author(self, tags: List[Dict]) -> str:
        """Extrai autor dos tags do Guardian"""
        for tag in tags:
            if tag.get('type') == 'contributor':
                return tag.get('webTitle', 'Autor Desconhecido')
        return 'Autor Desconhecido'
    
    def _extract_rss_image(self, entry: Dict) -> Optional[str]:
        """Extrai URL da imagem do RSS"""
        # Verificar campos comuns de imagem
        if hasattr(entry, 'media_thumbnail'):
            return entry.media_thumbnail[0]['url'] if entry.media_thumbnail else None
        
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if enclosure.type.startswith('image/'):
                    return enclosure.href
        
        return None
    
    def _extract_rss_category(self, entry: Dict) -> str:
        """Extrai categoria do RSS"""
        if hasattr(entry, 'tags') and entry.tags:
            return entry.tags[0]['term'].lower()
        
        if hasattr(entry, 'category'):
            return entry.category.lower()
        
        return 'geral'
    
    def _validate_article(self, article: Dict) -> bool:
        """Valida se artigo tem dados mínimos necessários"""
        required_fields = ['title', 'url', 'source']
        
        for field in required_fields:
            if not article.get(field):
                return False
        
        # Verificar se título não é muito curto
        if len(article['title']) < 10:
            return False
        
        # Verificar se URL é válida
        if not article['url'].startswith('http'):
            return False
        
        return True
    
    def get_available_categories(self) -> Dict[str, List[str]]:
        """Retorna categorias disponíveis por API"""
        return {
            'newsapi': [
                'business', 'entertainment', 'general', 'health',
                'science', 'sports', 'technology'
            ],
            'guardian': [
                'world', 'politics', 'business', 'technology',
                'sport', 'culture', 'environment'
            ],
            'rss': [
                'geral', 'tecnologia', 'politica', 'desporto',
                'economia', 'cultura', 'ciencia'
            ]
        }
    
    def clear_cache(self):
        """Limpa todo o cache"""
        self.cache.clear()
        logger.info("Cache limpo")
    
    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        total_entries = len(self.cache)
        valid_entries = sum(1 for key in self.cache if self._is_cache_valid(key))
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'cache_hit_ratio': valid_entries / total_entries if total_entries > 0 else 0
        }