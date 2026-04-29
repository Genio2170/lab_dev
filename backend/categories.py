#!/usr/bin/env python3
"""
Categories - Módulo para organização de notícias por categorias e filtragem
Integra com os módulos utils para validação, tratamento de erros e helpers
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Adicionar caminho para utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importar módulos utils
from utils import (
    api_error_handler,
    create_validation_error,
    create_database_error,
    create_not_found_error,
    format_success_response,
    validate_search_input,
    sanitize_user_input,
    clean_text,
    normalize_string,
    DataHelper
)

# Importar conexão com banco
from database.bd import Conexao

logger = logging.getLogger(__name__)

class CategoryManager:
    """Gerenciador de categorias para organização de notícias"""
    
    def __init__(self):
        self.db = Conexao()
        
        # Categorias padrão do sistema
        self.default_categories = {
            'geral': {
                'name': 'Geral',
                'description': 'Notícias gerais e variadas',
                'keywords': ['geral', 'notícias', 'atualidades', 'informação'],
                'color': '#6B7280',
                'icon': '📰'
            },
            'tecnologia': {
                'name': 'Tecnologia',
                'description': 'Inovação, IA, programação e tendências tech',
                'keywords': ['tecnologia', 'ia', 'inteligencia artificial', 'programacao', 'software', 'hardware', 'inovacao'],
                'color': '#3B82F6',
                'icon': '💻'
            },
            'ciencia': {
                'name': 'Ciência',
                'description': 'Descobertas científicas, pesquisa e desenvolvimento',
                'keywords': ['ciencia', 'pesquisa', 'descoberta', 'estudo', 'laboratorio', 'investigacao'],
                'color': '#10B981',
                'icon': '🔬'
            },
            'saude': {
                'name': 'Saúde',
                'description': 'Medicina, bem-estar e cuidados de saúde',
                'keywords': ['saude', 'medicina', 'hospital', 'tratamento', 'vacina', 'doenca'],
                'color': '#EF4444',
                'icon': '🏥'
            },
            'negocios': {
                'name': 'Negócios',
                'description': 'Economia, finanças e mundo empresarial',
                'keywords': ['negocios', 'economia', 'financas', 'empresa', 'mercado', 'investimento'],
                'color': '#F59E0B',
                'icon': '💼'
            },
            'desporto': {
                'name': 'Desporto',
                'description': 'Futebol, modalidades e eventos desportivos',
                'keywords': ['desporto', 'futebol', 'jogos', 'competicao', 'atleta', 'equipa'],
                'color': '#8B5CF6',
                'icon': '⚽'
            },
            'politica': {
                'name': 'Política',
                'description': 'Governo, eleições e políticas públicas',
                'keywords': ['politica', 'governo', 'eleicoes', 'presidente', 'ministro', 'parlamento'],
                'color': '#DC2626',
                'icon': '🏛️'
            },
            'cultura': {
                'name': 'Cultura',
                'description': 'Arte, música, cinema e entretenimento',
                'keywords': ['cultura', 'arte', 'musica', 'cinema', 'teatro', 'festival'],
                'color': '#EC4899',
                'icon': '🎭'
            },
            'ambiente': {
                'name': 'Ambiente',
                'description': 'Sustentabilidade, clima e ecologia',
                'keywords': ['ambiente', 'clima', 'sustentabilidade', 'ecologia', 'poluicao', 'natureza'],
                'color': '#059669',
                'icon': '🌱'
            }
        }
    
    @api_error_handler
    def get_all_categories(self, include_stats: bool = False) -> Dict:
        """
        Retorna todas as categorias disponíveis
        
        Args:
            include_stats: Se deve incluir estatísticas de uso
            
        Returns:
            Dicionário com categorias e opcionalmente estatísticas
        """
        try:
            categories = []
            
            for cat_id, cat_data in self.default_categories.items():
                category = {
                    'id': cat_id,
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'color': cat_data['color'],
                    'icon': cat_data['icon'],
                    'slug': cat_id
                }
                
                if include_stats:
                    stats = self._get_category_stats(cat_id)
                    category.update(stats)
                
                categories.append(category)
            
            return format_success_response(
                data={'categories': categories},
                message=f"{len(categories)} categorias disponíveis"
            )
            
        except Exception as e:
            raise create_database_error("buscar categorias", {'error': str(e)})
    
    @api_error_handler
    def classify_article(self, article_title: str, article_content: str = "") -> Dict:
        """
        Classifica um artigo em uma categoria baseado no conteúdo
        
        Args:
            article_title: Título do artigo
            article_content: Conteúdo do artigo (opcional)
            
        Returns:
            Categoria sugerida com confidence score
        """
        if not article_title:
            raise create_validation_error("Título do artigo é obrigatório")
        
        title = clean_text(article_title).lower()
        content = clean_text(article_content).lower() if article_content else ""
        
        # Texto combinado para análise
        full_text = f"{title} {content}"
        normalized_text = normalize_string(full_text)
        
        # Calcular scores para cada categoria
        category_scores = {}
        
        for cat_id, cat_data in self.default_categories.items():
            score = 0
            keywords = cat_data['keywords']
            
            for keyword in keywords:
                normalized_keyword = normalize_string(keyword)
                
                # Score por título (peso maior)
                if normalized_keyword in normalize_string(title):
                    score += 3
                
                # Score por conteúdo
                if normalized_keyword in normalized_text:
                    score += 1
                
                # Bonus por match exato
                if keyword == normalized_keyword and keyword in full_text:
                    score += 2
            
            if score > 0:
                category_scores[cat_id] = score
        
        # Se não encontrou matches, usar 'geral'
        if not category_scores:
            category_scores['geral'] = 1
        
        # Categoria com maior score
        best_category = max(category_scores.items(), key=lambda x: x[1])
        cat_id, score = best_category
        
        # Calcular confidence (normalizado)
        max_possible_score = len(self.default_categories[cat_id]['keywords']) * 3
        confidence = min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.1
        
        result = {
            'category': {
                'id': cat_id,
                'name': self.default_categories[cat_id]['name'],
                'color': self.default_categories[cat_id]['color'],
                'icon': self.default_categories[cat_id]['icon']
            },
            'confidence': round(confidence, 2),
            'score': score,
            'alternatives': []
        }
        
        # Adicionar categorias alternativas
        sorted_scores = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        for alt_cat_id, alt_score in sorted_scores[1:4]:  # Top 3 alternativas
            if alt_score > 0:
                alt_confidence = min(alt_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.1
                result['alternatives'].append({
                    'id': alt_cat_id,
                    'name': self.default_categories[alt_cat_id]['name'],
                    'confidence': round(alt_confidence, 2),
                    'score': alt_score
                })
        
        return format_success_response(
            data=result,
            message=f"Artigo classificado como {result['category']['name']}"
        )
    
    @api_error_handler
    def filter_articles_by_category(self, articles: List[Dict], category_id: str) -> Dict:
        """
        Filtra lista de artigos por categoria
        
        Args:
            articles: Lista de artigos
            category_id: ID da categoria para filtrar
            
        Returns:
            Artigos filtrados
        """
        category_id = sanitize_user_input(category_id, 50).lower()
        
        if category_id != 'todos' and category_id not in self.default_categories:
            raise create_not_found_error("Categoria", category_id)
        
        if category_id == 'todos':
            filtered_articles = articles
        else:
            filtered_articles = []
            
            for article in articles:
                # Se artigo já tem categoria
                if article.get('category') == category_id:
                    filtered_articles.append(article)
                # Senão, classificar automaticamente
                else:
                    classification = self.classify_article(
                        article.get('title', ''), 
                        article.get('description', '')
                    )
                    
                    if classification['data']['category']['id'] == category_id:
                        # Adicionar categoria ao artigo
                        article['category'] = category_id
                        article['category_confidence'] = classification['data']['confidence']
                        filtered_articles.append(article)
        
        return format_success_response(
            data={
                'articles': filtered_articles,
                'category': category_id,
                'total_found': len(filtered_articles),
                'total_analyzed': len(articles)
            },
            message=f"{len(filtered_articles)} artigos encontrados na categoria"
        )
    
    def _get_category_stats(self, category_id: str) -> Dict:
        """Obtém estatísticas de uma categoria"""
        try:
            # Simular estatísticas por enquanto
            # Em produção, consultaria tabelas de artigos e visualizações
            stats = {
                'total_articles': 0,
                'articles_today': 0,
                'articles_week': 0,
                'avg_views': 0,
                'last_updated': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.warning(f"Erro ao obter estatísticas da categoria {category_id}: {e}")
            return {
                'total_articles': 0,
                'articles_today': 0,
                'articles_week': 0,
                'avg_views': 0,
                'last_updated': datetime.now().isoformat()
            }
    
    def bulk_classify_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Classifica múltiplos artigos em lote
        
        Args:
            articles: Lista de artigos sem categoria
            
        Returns:
            Artigos com categorias atribuídas
        """
        classified_articles = []
        
        for article in articles:
            try:
                if not article.get('category'):
                    classification = self.classify_article(
                        article.get('title', ''),
                        article.get('description', '')
                    )
                    
                    if classification['success']:
                        article['category'] = classification['data']['category']['id']
                        article['category_name'] = classification['data']['category']['name']
                        article['category_confidence'] = classification['data']['confidence']
                        article['category_color'] = classification['data']['category']['color']
                        article['category_icon'] = classification['data']['category']['icon']
                
                classified_articles.append(article)
                
            except Exception as e:
                logger.warning(f"Erro ao classificar artigo: {e}")
                # Usar categoria padrão
                article['category'] = 'geral'
                article['category_name'] = 'Geral'
                article['category_confidence'] = 0.1
                classified_articles.append(article)
        
        return classified_articles

# Instância global
category_manager = CategoryManager()

# Funções de conveniência
def get_categories(include_stats: bool = False) -> Dict:
    """Função de conveniência para obter categorias"""
    return category_manager.get_all_categories(include_stats)

def classify_news_article(title: str, content: str = "") -> Dict:
    """Função de conveniência para classificar artigo"""
    return category_manager.classify_article(title, content)

def filter_by_category(articles: List[Dict], category: str) -> Dict:
    """Função de conveniência para filtrar artigos"""
    return category_manager.filter_articles_by_category(articles, category)

def auto_categorize_articles(articles: List[Dict]) -> List[Dict]:
    """Função de conveniência para categorização em lote"""
    return category_manager.bulk_classify_articles(articles)
                HAVING news_count > 0
                ORDER BY news_count DESC
                LIMIT 10
            """.format(days))
            
            self.db.desconectar()
            
            trending = []
            for data in trending_data:
                cat_id, name, count = data
                trending.append({
                    'id': cat_id,
                    'name': name,
                    'slug': self._create_slug(name),
                    'recent_news_count': count,
                    'keywords': self.keywords_mapping.get(name.lower(), [])
                })
            
            return trending, f"Top {len(trending)} categorias em alta"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao buscar categorias em alta: {e}")
            return [], f"Erro ao buscar categorias em alta: {str(e)}"
    
    def search_news_by_keywords(self, keywords: str, category_id: Optional[int] = None,
                               limit: int = 50) -> Tuple[List[Dict], str]:
        """Busca notícias por palavras-chave"""
        try:
            if not keywords or len(keywords.strip()) < 3:
                return [], "Palavras-chave devem ter pelo menos 3 caracteres"
            
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            # Preparar termos de busca
            search_terms = f"%{keywords.strip()}%"
            
            if category_id:
                # Buscar dentro de categoria específica
                news_data = self.db.buscar("""
                    SELECT n.id, n.title, n.description, n.url, n.source,
                           n.image_url, n.published_at, c.name as category_name
                    FROM news n
                    LEFT JOIN categories c ON n.category_id = c.id
                    WHERE n.category_id = ? AND (
                        LOWER(n.title) LIKE LOWER(?) OR 
                        LOWER(n.description) LIKE LOWER(?)
                    )
                    ORDER BY n.published_at DESC
                    LIMIT ?
                """, (category_id, search_terms, search_terms, limit))
            else:
                # Buscar em todas as categorias
                news_data = self.db.buscar("""
                    SELECT n.id, n.title, n.description, n.url, n.source,
                           n.image_url, n.published_at, c.name as category_name
                    FROM news n
                    LEFT JOIN categories c ON n.category_id = c.id
                    WHERE LOWER(n.title) LIKE LOWER(?) OR 
                          LOWER(n.description) LIKE LOWER(?)
                    ORDER BY n.published_at DESC
                    LIMIT ?
                """, (search_terms, search_terms, limit))
            
            self.db.desconectar()
            
            news_list = []
            for news in news_data:
                (news_id, title, description, url, source, 
                 image_url, published_at, category_name) = news
                
                news_list.append({
                    'id': news_id,
                    'title': title,
                    'description': description,
                    'url': url,
                    'source': source,
                    'image_url': image_url,
                    'published_at': published_at,
                    'category': category_name or 'Geral'
                })
            
            return news_list, f"{len(news_list)} notícias encontradas para '{keywords}'"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro na busca por palavras-chave: {e}")
            return [], f"Erro na busca: {str(e)}"
    
    def _create_slug(self, text: str) -> str:
        """Cria slug a partir do texto"""
        slug = text.lower()
        slug = self._remove_accents(slug)
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    def _remove_accents(self, text: str) -> str:
        """Remove acentos do texto para melhor matching"""
        accents = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        
        for accented, plain in accents.items():
            text = text.replace(accented, plain)
            text = text.replace(accented.upper(), plain.upper())
        
        return text
    
    def get_category_statistics(self) -> Tuple[Dict, str]:
        """Obtém estatísticas gerais das categorias"""
        try:
            if not self.db.conectar():
                return {}, "Erro de conexão com a base de dados"
            
            # Estatísticas básicas
            total_categories = self.db.buscar("SELECT COUNT(*) FROM categories")[0][0]
            total_news = self.db.buscar("SELECT COUNT(*) FROM news")[0][0]
            
            # Categoria mais popular
            most_popular = self.db.buscar("""
                SELECT c.name, COUNT(n.id) as count
                FROM categories c
                LEFT JOIN news n ON c.id = n.category_id
                GROUP BY c.id, c.name
                ORDER BY count DESC
                LIMIT 1
            """)
            
            # Notícias sem categoria
            uncategorized = self.db.buscar("""
                SELECT COUNT(*) FROM news WHERE category_id IS NULL
            """)[0][0]
            
            self.db.desconectar()
            
            stats = {
                'total_categories': total_categories,
                'total_news': total_news,
                'uncategorized_news': uncategorized,
                'categorization_rate': ((total_news - uncategorized) / total_news * 100) if total_news > 0 else 0,
                'most_popular_category': {
                    'name': most_popular[0][0] if most_popular else 'N/A',
                    'news_count': most_popular[0][1] if most_popular else 0
                },
                'average_news_per_category': total_news / total_categories if total_categories > 0 else 0
            }
            
            return stats, "Estatísticas calculadas com sucesso"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}, f"Erro ao calcular estatísticas: {str(e)}"