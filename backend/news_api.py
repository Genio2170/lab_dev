import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urlparse
import time
import os
import sys

# Adicionar caminho para utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importar módulos utils
from utils import (
    api_error_handler,
    create_api_error, 
    create_network_error,
    create_validation_error,
    format_success_response,
    validate_api_response,
    validate_article_data,
    sanitize_user_input,
    clean_text,
    format_date,
    summarize_article,
    UrlHelper,
    DataHelper
)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            raise create_api_error("Timeout na requisição - API muito lenta", "News API", 408)
        except requests.exceptions.ConnectionError:
            raise create_network_error("Erro de conexão - verificar internet")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise create_api_error("Chave de API inválida ou expirada", "News API", 401)
            elif e.response.status_code == 429:
                raise create_api_error("Limite de requisições excedido - tente mais tarde", "News API", 429)
            else:
                raise create_api_error(f"Erro HTTP {e.response.status_code}", "News API", e.response.status_code)
        except json.JSONDecodeError:
            raise create_api_error("Resposta da API inválida - formato JSON incorreto", "News API", 502)
        except Exception as e:
            raise create_api_error(f"Erro inesperado: {str(e)}", "News API", 500)
    
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
    
    @api_error_handler
    def fetch_newsapi_articles(self, api_key: str, category: str = None, 
                              country: str = 'pt', language: str = 'pt',
                              page_size: int = 20) -> Dict:
        """Busca artigos da NewsAPI.org"""
        
        if not api_key:
            raise create_validation_error("Chave da API NewsAPI não fornecida")
        
        # Sanitizar parâmetros
        if category:
            category = sanitize_user_input(category, 50)
        
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
                articles = self._normalize_newsapi_articles(cached_data['articles'])
                return format_success_response(
                    data={'articles': articles, 'source': 'cache'}, 
                    message=f"Dados do cache - {len(articles)} artigos"
                )
            
            url = f"{self.api_configs['newsapi']['base_url']}/top-headlines"
            data = self._make_request(url, params)
            
            # Validar resposta da API
            validation = validate_api_response(data, 'news_api')
            if not validation['valid']:
                raise create_api_error(f"Dados inválidos da API: {validation['errors']}")
            
            # Salvar no cache
            self._save_to_cache(cache_key, data)
            
            articles = self._normalize_newsapi_articles(data.get('articles', []))
            
            # Gerar resumos automáticos usando IA
            articles = self._add_ai_summaries(articles)
            
            return format_success_response(
                data={'articles': articles, 'source': 'api'}, 
                message=f"Sucesso - {data.get('totalResults', 0)} artigos processados"
            )
            
        except Exception as e:
            # O decorator api_error_handler vai tratar automaticamente
            raise e
    
    @api_error_handler
    def fetch_guardian_articles(self, api_key: str, section: str = None,
                               page_size: int = 20) -> Dict:
        """Busca artigos do The Guardian API"""
        
        if not api_key:
            raise create_validation_error("Chave da API Guardian não fornecida")
        
        if section:
            section = sanitize_user_input(section, 50)
        
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
                articles = self._normalize_guardian_articles(cached_data['results'])
                return format_success_response(
                    data={'articles': articles, 'source': 'cache'},
                    message=f"Cache - {len(articles)} artigos"
                )
            
            url = f"{self.api_configs['guardian']['base_url']}/search"
            data = self._make_request(url, params)
            
            # Salvar no cache
            self._save_to_cache(cache_key, data['response'])
            
            articles = self._normalize_guardian_articles(data['response']['results'])
            articles = self._add_ai_summaries(articles)
            
            return format_success_response(
                data={'articles': articles, 'source': 'api'},
                message=f"Guardian - {data['response']['total']} artigos encontrados"
            )
            
        except Exception as e:
            # O decorator api_error_handler vai tratar automaticamente
            raise e
    
    @api_error_handler
    def fetch_rss_articles(self, rss_urls: List[str], 
                          max_articles: int = 50) -> Dict:
        """Busca artigos de feeds RSS"""
        
        try:
            import feedparser
        except ImportError:
            raise create_validation_error(
                "Biblioteca feedparser não instalada - execute: pip install feedparser"
            )
        
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
        
        # Adicionar resumos IA
        all_articles = self._add_ai_summaries(all_articles)
        
        return format_success_response(
            data={'articles': all_articles, 'source': 'rss'},
            message=f"RSS - {successful_feeds} feeds processados, {len(all_articles)} artigos"
        )
    
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
    
    def _add_ai_summaries(self, articles: List[Dict]) -> List[Dict]:
        """Adiciona resumos automáticos usando IA"""
        for article in articles:
            try:
                # Gerar resumo se houver conteúdo suficiente
                content = article.get('content', '') or article.get('description', '')
                if content and len(content) > 100:
                    summary, source = summarize_article(
                        content, 
                        article.get('title', ''), 
                        max_length=150
                    )
                    article['ai_summary'] = summary
                    article['summary_source'] = source
                else:
                    article['ai_summary'] = article.get('description', '')[:150]
                    article['summary_source'] = 'original'
            except Exception as e:
                logger.warning(f"Erro ao gerar resumo: {e}")
                article['ai_summary'] = article.get('description', '')
                article['summary_source'] = 'fallback'
        
        return articles
    
    def search_articles(self, query: str, api_key: str = None, 
                       sources: List[str] = None, language: str = 'pt',
                       sort_by: str = 'relevancy', page_size: int = 20) -> Dict:
        """Busca artigos por query usando múltiplas fontes"""
        query = sanitize_user_input(query, 100)
        
        if not query:
            raise create_validation_error("Query de busca não pode estar vazia")
        
        all_articles = []
        
        # Buscar na NewsAPI se chave fornecida
        if api_key:
            try:
                newsapi_result = self._search_newsapi(query, api_key, language, sort_by, page_size)
                if newsapi_result['success']:
                    all_articles.extend(newsapi_result['data']['articles'])
            except Exception as e:
                logger.warning(f"Erro na busca NewsAPI: {e}")
        
        # Buscar em feeds RSS se disponíveis
        try:
            rss_articles = self._search_rss_feeds(query, page_size // 2)
            all_articles.extend(rss_articles)
        except Exception as e:
            logger.warning(f"Erro na busca RSS: {e}")
        
        # Remover duplicatas por URL
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        # Ordenar por relevância e data
        unique_articles.sort(
            key=lambda x: (x.get('published_at', datetime.now()), x.get('title', '')),
            reverse=True
        )
        
        # Adicionar resumos IA
        unique_articles = self._add_ai_summaries(unique_articles[:page_size])
        
        return format_success_response(
            data={
                'articles': unique_articles,
                'query': query,
                'total_found': len(unique_articles)
            },
            message=f"Encontrados {len(unique_articles)} artigos para '{query}'"
        )
    
    def _search_newsapi(self, query: str, api_key: str, language: str, 
                       sort_by: str, page_size: int) -> Dict:
        """Busca específica na NewsAPI"""
        params = {
            'apiKey': api_key,
            'q': query,
            'language': language,
            'sortBy': sort_by,
            'pageSize': min(page_size, 100)
        }
        
        url = f"{self.api_configs['newsapi']['base_url']}/everything"
        data = self._make_request(url, params)
        
        articles = self._normalize_newsapi_articles(data.get('articles', []))
        
        return format_success_response(
            data={'articles': articles},
            message=f"NewsAPI: {len(articles)} artigos"
        )
    
    def _search_rss_feeds(self, query: str, max_articles: int) -> List[Dict]:
        """Busca em feeds RSS por palavras-chave"""
        # Feeds RSS portugueses e angolanos
        rss_feeds = [
            'https://www.rtp.pt/noticias/rss.php',
            'https://www.publico.pt/rss.xml',
            'https://feeds.feedburner.com/observador-economia',
            # Adicione mais feeds conforme necessário
        ]
        
        try:
            articles, _ = self.fetch_rss_articles(rss_feeds, max_articles * 2)
            
            # Filtrar artigos por query
            query_lower = query.lower()
            filtered_articles = []
            
            for article in articles:
                title = article.get('title', '').lower()
                description = article.get('description', '').lower()
                
                if query_lower in title or query_lower in description:
                    filtered_articles.append(article)
            
            return filtered_articles[:max_articles]
            
        except Exception as e:
            logger.warning(f"Erro na busca RSS: {e}")
            return []
    
    def get_articles_by_category(self, category: str, api_key: str = None,
                                language: str = 'pt', page_size: int = 20) -> Dict:
        """Obtém artigos de uma categoria específica"""
        category = sanitize_user_input(category, 50).lower()
        
        # Mapear categorias para português
        category_mapping = {
            'tecnologia': 'technology',
            'ciência': 'science', 
            'saúde': 'health',
            'desporto': 'sports',
            'negócios': 'business',
            'política': 'general',
            'geral': 'general'
        }
        
        newsapi_category = category_mapping.get(category, 'general')
        
        if api_key:
            result = self.fetch_newsapi_articles(
                api_key=api_key,
                category=newsapi_category,
                language=language,
                page_size=page_size
            )
            
            if result['success']:
                return format_success_response(
                    data={
                        'articles': result['data']['articles'],
                        'category': category,
                        'total': len(result['data']['articles'])
                    },
                    message=f"Artigos da categoria {category}"
                )
        
        return format_success_response(
            data={'articles': [], 'category': category},
            message="Nenhum artigo encontrado para esta categoria"
        )
    
    def _clean_text(self, text: str) -> str:
        """Remove HTML e limpa texto usando utils"""
        return clean_text(text)
    
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
        """Valida se artigo tem dados mínimos necessários usando utils"""
        validation = validate_article_data(article)
        return validation['valid']
    
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