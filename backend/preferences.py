#!/usr/bin/env python3
"""
Preferences - Módulo para gestão de preferências de leitura dos utilizadores
Integra com utils para validação, IA e tratamento de erros
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Set
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
    sanitize_user_input,
    clean_text,
    analyze_user_patterns,
    get_recommendations,
    DataHelper,
    JsonHelper
)

# Importar conexão com banco
from database.bd import Conexao

logger = logging.getLogger(__name__)

class PreferencesManager:
    """Gerenciador para preferências de leitura e fontes favoritas dos utilizadores"""
    
    def __init__(self):
        self.db = Conexao()
        
        # Fontes de notícias disponíveis
        self.available_sources = {
            'newsapi': {
                'name': 'News API',
                'description': 'Agregador global de notícias',
                'languages': ['pt', 'en', 'es', 'fr'],
                'categories': ['geral', 'tecnologia', 'politica', 'desporto', 'saude'],
                'reliability': 8,  # Score de 1-10
                'update_frequency': 'hourly'
            },
            'guardian': {
                'name': 'The Guardian',
                'description': 'Jornal britânico de qualidade',
                'languages': ['en'],
                'categories': ['internacional', 'politica', 'tecnologia', 'cultura'],
                'reliability': 9,
                'update_frequency': 'hourly'
            },
            'rtp': {
                'name': 'RTP Notícias',
                'description': 'Serviço público de televisão português',
                'languages': ['pt'],
                'categories': ['local', 'politica', 'economia', 'cultura', 'desporto'],
                'reliability': 9,
                'update_frequency': 'continuous'
            },
            'publico': {
                'name': 'Público',
                'description': 'Jornal português independente',
                'languages': ['pt'],
                'categories': ['politica', 'economia', 'cultura', 'ciencia', 'local'],
                'reliability': 8,
                'update_frequency': 'hourly'
            },
            'observador': {
                'name': 'Observador',
                'description': 'Portal de notícias português',
                'languages': ['pt'],
                'categories': ['politica', 'economia', 'tecnologia', 'cultura'],
                'reliability': 7,
                'update_frequency': 'hourly'
            },
            'bbc': {
                'name': 'BBC News',
                'description': 'Serviço de notícias da BBC',
                'languages': ['en', 'pt'],
                'categories': ['internacional', 'tecnologia', 'ciencia', 'cultura'],
                'reliability': 9,
                'update_frequency': 'continuous'
            }
        }
    
    @api_error_handler
    def get_user_preferences(self, user_id: int) -> Dict:
        """Busca preferências completas do utilizador"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id})
            
            # Buscar categorias preferidas
            categories_data = self.db.buscar("""
                SELECT c.id, c.name
                FROM preferences p
                JOIN categories c ON p.category_id = c.id
                WHERE p.user_id = ?
                ORDER BY c.name
            """, (user_id,))
            
            # Buscar configurações adicionais (se existir tabela para isso)
            # Por enquanto, vamos simular com dados padrão
            
            self.db.desconectar()
            
            preferred_categories = [
                {'id': cat[0], 'name': cat[1]} 
                for cat in (categories_data or [])
            ]
            
            # Estrutura padrão de preferências
            preferences = {
                'user_id': user_id,
                'preferred_categories': preferred_categories,
                'preferred_sources': self._get_default_sources(),
                'language': 'pt',
                'notification_frequency': 'daily',
                'article_length_preference': 'medium',  # short, medium, long
                'reading_time_preference': '5-10min',
                'auto_categorization': True,
                'show_images': True,
                'dark_mode': False,
                'articles_per_page': 20,
                'email_notifications': True,
                'push_notifications': False,
                'weekend_notifications': False,
                'quiet_hours': {'start': '22:00', 'end': '08:00'},
                'blocked_sources': [],
                'custom_keywords': []
            }
            
            return format_success_response(
                data=preferences,
                message="Preferências carregadas com sucesso"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("buscar preferências", {"user_id": user_id, "error": str(e)})
    
    @api_error_handler
    def add_preferred_category(self, user_id: int, category_id: int) -> Dict:
        """Adiciona categoria às preferências do utilizador"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if not category_id or category_id <= 0:
            raise create_validation_error("ID de categoria inválido")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id, "category_id": category_id})
            
            # Verificar se categoria existe
            category_exists = self.db.buscar("""
                SELECT id, name FROM categories WHERE id = ?
            """, (category_id,))
            
            if not category_exists:
                self.db.desconectar()
                raise create_not_found_error("Categoria", str(category_id))
            
            # Verificar se preferência já existe
            existing = self.db.buscar("""
                SELECT id FROM preferences WHERE user_id = ? AND category_id = ?
            """, (user_id, category_id))
            
            if existing:
                self.db.desconectar()
                return format_success_response(
                    data={'category_name': category_exists[0][1], 'already_exists': True},
                    message="Categoria já está nas preferências"
                )
            
            # Adicionar preferência
            self.db.executar("""
                INSERT INTO preferences (user_id, category_id) VALUES (?, ?)
            """, (user_id, category_id))
            
            self.db.desconectar()
            
            return format_success_response(
                data={'category_name': category_exists[0][1], 'category_id': category_id},
                message="Categoria adicionada às preferências"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("adicionar categoria preferida", {"user_id": user_id, "category_id": category_id, "error": str(e)})
    
    def remove_preferred_category(self, user_id: int, category_id: int) -> Tuple[bool, str]:
        """Remove categoria das preferências do utilizador"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Verificar se preferência existe
            existing = self.db.buscar("""
                SELECT id FROM preferences WHERE user_id = ? AND category_id = ?
            """, (user_id, category_id))
            
            if not existing:
                self.db.desconectar()
                return False, "Categoria não está nas preferências"
            
            # Remover preferência
            self.db.executar("""
                DELETE FROM preferences WHERE user_id = ? AND category_id = ?
            """, (user_id, category_id))
            
            self.db.desconectar()
            return True, "Categoria removida das preferências"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao remover categoria preferida: {e}")
            return False, f"Erro ao remover categoria: {str(e)}"
    
    def set_preferred_categories(self, user_id: int, category_ids: List[int]) -> Tuple[bool, str]:
        """Define lista completa de categorias preferidas (substitui existentes)"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Validar que todas as categorias existem
            if category_ids:
                placeholders = ','.join(['?' for _ in category_ids])
                valid_categories = self.db.buscar(f"""
                    SELECT id FROM categories WHERE id IN ({placeholders})
                """, category_ids)
                
                valid_ids = [cat[0] for cat in (valid_categories or [])]
                invalid_ids = set(category_ids) - set(valid_ids)
                
                if invalid_ids:
                    self.db.desconectar()
                    return False, f"Categorias inválidas: {list(invalid_ids)}"
            
            # Remover preferências existentes
            self.db.executar("""
                DELETE FROM preferences WHERE user_id = ?
            """, (user_id,))
            
            # Adicionar novas preferências
            for category_id in category_ids:
                self.db.executar("""
                    INSERT INTO preferences (user_id, category_id) VALUES (?, ?)
                """, (user_id, category_id))
            
            self.db.desconectar()
            return True, f"{len(category_ids)} categorias definidas como preferidas"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao definir categorias preferidas: {e}")
            return False, f"Erro ao definir categorias: {str(e)}"
    
    @api_error_handler
    def get_recommended_articles(self, user_id: int, limit: int = 20) -> Dict:
        """Busca artigos recomendados baseados nas preferências do utilizador"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if limit < 1 or limit > 100:
            raise create_validation_error("Limite deve ser entre 1 e 100")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id})
            
            # Buscar artigos das categorias preferidas
            recommended = self.db.buscar("""
                SELECT DISTINCT n.id, n.title, n.description, n.url, n.source,
                       n.image_url, n.published_at, c.name as category_name
                FROM news n
                JOIN categories c ON n.category_id = c.id
                WHERE c.id IN (
                    SELECT category_id FROM preferences WHERE user_id = ?
                )
                AND n.published_at >= datetime('now', '-7 days')
                ORDER BY n.published_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            # Se não há artigos suficientes das categorias preferidas, buscar mais gerais
            recommended = recommended or []
            if len(recommended) < limit:
                additional = self.db.buscar("""
                    SELECT n.id, n.title, n.description, n.url, n.source,
                           n.image_url, n.published_at, c.name as category_name
                    FROM news n
                    JOIN categories c ON n.category_id = c.id
                    WHERE n.id NOT IN (
                        SELECT DISTINCT n2.id
                        FROM news n2
                        JOIN categories c2 ON n2.category_id = c2.id
                        WHERE c2.id IN (
                            SELECT category_id FROM preferences WHERE user_id = ?
                        )
                        AND n2.published_at >= datetime('now', '-7 days')
                    )
                    AND n.published_at >= datetime('now', '-3 days')
                    ORDER BY n.published_at DESC
                    LIMIT ?
                """, (user_id, limit - len(recommended)))
                
                if additional:
                    recommended.extend(additional)
            
            self.db.desconectar()
            
            articles = []
            additional_count = len(additional) if 'additional' in locals() and additional else 0
            for i, news in enumerate(recommended or []):
                (news_id, title, description, url, source,
                 image_url, published_at, category_name) = news
                
                # Limpar dados
                clean_title = clean_text(title) if title else ""
                clean_description = clean_text(description) if description else ""
                
                articles.append({
                    'id': news_id,
                    'title': clean_title,
                    'description': clean_description,
                    'url': url,
                    'source': source,
                    'image_url': image_url,
                    'published_at': published_at,
                    'category': category_name,
                    'recommendation_reason': 'Categoria preferida' if i < len(recommended) - additional_count else 'Sugestão geral'
                })
            
            return format_success_response(
                data={
                    'articles': articles,
                    'total': len(articles),
                    'limit': limit,
                    'from_preferences': len(recommended) - additional_count,
                    'general_suggestions': additional_count
                },
                message=f"{len(articles)} artigos recomendados"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("buscar recomendações", {"user_id": user_id, "error": str(e)})
    
    def get_available_sources(self) -> Dict[str, Dict]:
        """Retorna todas as fontes disponíveis com suas informações"""
        return self.available_sources.copy()
    
    def get_user_source_preferences(self, user_id: int) -> Tuple[List[str], str]:
        """Busca fontes preferidas do utilizador (simulado por enquanto)"""
        # Esta funcionalidade precisaria de uma tabela adicional para ser persistida
        # Por agora, retornamos fontes padrão baseadas nas preferências de categoria
        
        try:
            user_prefs, _ = self.get_user_preferences(user_id)
            if not user_prefs:
                return list(self.available_sources.keys()), "Fontes padrão"
            
            # Recomendar fontes baseadas nas categorias preferidas
            preferred_categories = [cat['name'].lower() for cat in user_prefs['preferred_categories']]
            recommended_sources = []
            
            for source_id, source_info in self.available_sources.items():
                source_categories = [cat.lower() for cat in source_info['categories']]
                
                # Se há overlap entre categorias preferidas e categorias da fonte
                if any(cat in source_categories for cat in preferred_categories):
                    recommended_sources.append(source_id)
            
            # Se não há recomendações específicas, retornar fontes portuguesas
            if not recommended_sources:
                recommended_sources = ['rtp', 'publico', 'observador']
            
            return recommended_sources, f"{len(recommended_sources)} fontes recomendadas"
            
        except Exception as e:
            logger.error(f"Erro ao buscar fontes preferidas: {e}")
            return list(self.available_sources.keys()), "Fontes padrão (erro)"
    
    def get_reading_statistics(self, user_id: int, days: int = 30) -> Tuple[Dict, str]:
        """Obtém estatísticas de leitura do utilizador"""
        # Esta funcionalidade precisaria de tracking de leitura
        # Por agora, simulamos com dados baseados nas preferências
        
        try:
            user_prefs, _ = self.get_user_preferences(user_id)
            if not user_prefs:
                return {}, "Utilizador sem preferências"
            
            # Simular estatísticas baseadas nas categorias preferidas
            preferred_count = len(user_prefs['preferred_categories'])
            
            stats = {
                'period_days': days,
                'preferred_categories_count': preferred_count,
                'estimated_articles_read': preferred_count * 15,  # Simulado
                'most_read_category': user_prefs['preferred_categories'][0]['name'] if user_prefs['preferred_categories'] else 'N/A',
                'reading_consistency': min(100, preferred_count * 20),  # Score 0-100
                'diversity_score': min(100, preferred_count * 15),
                'engagement_level': 'High' if preferred_count >= 4 else 'Medium' if preferred_count >= 2 else 'Low'
            }
            
            return stats, "Estatísticas calculadas"
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}, f"Erro ao calcular estatísticas: {str(e)}"
    
    def suggest_categories(self, user_id: int) -> Tuple[List[Dict], str]:
        """Sugere novas categorias baseadas no perfil do utilizador"""
        try:
            user_prefs, _ = self.get_user_preferences(user_id)
            if not user_prefs:
                return [], "Utilizador sem preferências"
            
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            # Buscar categorias que o usuário ainda não tem
            preferred_ids = [cat['id'] for cat in user_prefs['preferred_categories']]
            
            if preferred_ids:
                placeholders = ','.join(['?' for _ in preferred_ids])
                available_categories = self.db.buscar(f"""
                    SELECT c.id, c.name, COUNT(n.id) as news_count
                    FROM categories c
                    LEFT JOIN news n ON c.id = n.category_id
                    WHERE c.id NOT IN ({placeholders})
                    GROUP BY c.id, c.name
                    HAVING news_count > 0
                    ORDER BY news_count DESC
                    LIMIT 5
                """, preferred_ids)
            else:
                # Se não tem preferências, sugerir categorias mais populares
                available_categories = self.db.buscar("""
                    SELECT c.id, c.name, COUNT(n.id) as news_count
                    FROM categories c
                    LEFT JOIN news n ON c.id = n.category_id
                    GROUP BY c.id, c.name
                    HAVING news_count > 0
                    ORDER BY news_count DESC
                    LIMIT 5
                """)
            
            self.db.desconectar()
            
            suggestions = []
            for cat in (available_categories or []):
                cat_id, name, news_count = cat
                suggestions.append({
                    'id': cat_id,
                    'name': name,
                    'news_count': news_count,
                    'suggestion_reason': 'Popular' if not preferred_ids else 'Complementar ao seu perfil'
                })
            
            return suggestions, f"{len(suggestions)} categorias sugeridas"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao sugerir categorias: {e}")
            return [], f"Erro ao sugerir categorias: {str(e)}"
    
    def export_user_preferences(self, user_id: int) -> Tuple[Optional[Dict], str]:
        """Exporta preferências do utilizador em formato JSON"""
        try:
            preferences, message = self.get_user_preferences(user_id)
            if not preferences:
                return None, message
            
            # Adicionar metadados de exportação
            export_data = {
                'export_date': datetime.now().isoformat(),
                'user_id': user_id,
                'version': '1.0',
                'preferences': preferences
            }
            
            return export_data, "Preferências exportadas com sucesso"
            
        except Exception as e:
            logger.error(f"Erro ao exportar preferências: {e}")
            return None, f"Erro ao exportar: {str(e)}"
    
    def import_user_preferences(self, user_id: int, preferences_data: Dict) -> Tuple[bool, str]:
        """Importa preferências do utilizador de dados JSON"""
        try:
            if 'preferences' not in preferences_data:
                return False, "Formato de dados inválido"
            
            prefs = preferences_data['preferences']
            
            # Extrair IDs das categorias
            if 'preferred_categories' in prefs:
                category_ids = [cat['id'] for cat in prefs['preferred_categories']]
                success, message = self.set_preferred_categories(user_id, category_ids)
                
                if success:
                    return True, "Preferências importadas com sucesso"
                else:
                    return False, f"Erro ao importar: {message}"
            
            return False, "Dados de preferências não encontrados"
            
        except Exception as e:
            logger.error(f"Erro ao importar preferências: {e}")
            return False, f"Erro ao importar: {str(e)}"
    
    def _get_default_sources(self) -> List[str]:
        """Retorna fontes padrão para utilizadores portugueses"""
        return ['rtp', 'publico', 'observador', 'newsapi']
    
    def validate_user_exists(self, user_id: int) -> bool:
        """Valida se utilizador existe na base de dados"""
        try:
            if not self.db.conectar():
                return False
            
            user_exists = self.db.buscar("""
                SELECT id FROM users WHERE id = ?
            """, (user_id,))
            
            self.db.desconectar()
            return bool(user_exists) and len(user_exists) > 0
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao validar usuário: {e}")
            return False