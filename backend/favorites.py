#!/usr/bin/env python3
"""
Favorites - Módulo para gestão de artigos favoritos dos utilizadores
Integra com utils para validação, IA e tratamento de erros
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import hashlib

# Adicionar caminho para utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Importar módulos utils
from utils import (
    api_error_handler,
    create_validation_error,
    create_database_error,
    create_not_found_error,
    format_success_response,
    validate_article_data,
    sanitize_user_input,
    clean_text,
    SecurityHelper,
    DataHelper
)

# Função auxiliar para format_date_portuguese se não estiver disponível
def format_date_portuguese(date_str):
    """Formata data em português"""
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = date_str
        return dt.strftime('%d/%m/%Y às %H:%M')
    except Exception:
        return str(date_str)

# Função auxiliar para create_duplicate_error
class DuplicateError(Exception):
    """Exceção para erros de duplicação"""
    def __init__(self, message: str, data=None):
        super().__init__(message)
        self.message = message
        self.data = data

def create_duplicate_error(message: str, data=None):
    """Cria erro de duplicação"""
    raise DuplicateError(message, data)

# Importar conexão com banco
from database.bd import Conexao

logger = logging.getLogger(__name__)

class FavoritesManager:
    """Gerenciador para artigos favoritos dos utilizadores"""
    
    def __init__(self):
        self.db = Conexao()
        self._init_favorites_table()
    
    def _init_favorites_table(self):
        """Inicializa tabela de favoritos se não existir"""
        try:
            if not self.db.conectar():
                return
            
            # Criar tabela de favoritos se não existir
            self.db.executar("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    news_id INTEGER,
                    external_url TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    source TEXT,
                    image_url TEXT,
                    category TEXT DEFAULT 'geral',
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    tags TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (news_id) REFERENCES news(id),
                    UNIQUE(user_id, news_id, external_url)
                )
            """)
            
            self.db.desconectar()
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao inicializar tabela de favoritos: {e}")
    
    @api_error_handler
    def add_favorite_by_news_id(self, user_id: int, news_id: int, 
                               notes: str = "", tags: Optional[List[str]] = None) -> Dict:
        """Adiciona artigo aos favoritos usando ID da tabela news"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if not news_id or news_id <= 0:
            raise create_validation_error("ID de notícia inválido")
        
        # Limpar e validar entradas
        clean_notes = sanitize_user_input(notes, 500) if notes else ""
        clean_tags = [sanitize_user_input(tag, 50) for tag in (tags or [])][:10]  # Max 10 tags
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id, "news_id": news_id})
            
            # Verificar se artigo existe na tabela news
            news_data = self.db.buscar("""
                SELECT n.title, n.description, n.source, n.image_url, c.name as category
                FROM news n
                LEFT JOIN categories c ON n.category_id = c.id
                WHERE n.id = ?
            """, (news_id,))
            
            if not news_data:
                self.db.desconectar()
                raise create_not_found_error("Artigo", str(news_id))
            
            title, description, source, image_url, category = news_data[0]
            
            # Verificar se já está nos favoritos
            existing = self.db.buscar("""
                SELECT id FROM favorites WHERE user_id = ? AND news_id = ?
            """, (user_id, news_id))
            
            if existing:
                self.db.desconectar()
                raise create_duplicate_error("Artigo já está nos favoritos")
            
            # Preparar dados limpos
            clean_title = clean_text(title)
            clean_description = clean_text(description) if description else ""
            clean_source = sanitize_user_input(source, 100) if source else ""
            tags_str = ','.join(clean_tags) if clean_tags else ''
            
            # Adicionar aos favoritos
            self.db.executar("""
                INSERT INTO favorites (user_id, news_id, title, description, source, 
                                     image_url, category, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, news_id, clean_title, clean_description, clean_source, 
                  image_url, category or 'geral', clean_notes, tags_str))
            
            # Buscar ID do favorito criado
            favorite_result = self.db.buscar("""
                SELECT id FROM favorites WHERE user_id = ? AND news_id = ?
                ORDER BY added_at DESC LIMIT 1
            """, (user_id, news_id))
            
            favorite_id = favorite_result[0][0] if favorite_result else None
            
            self.db.desconectar()
            
            return format_success_response(
                data={
                    'favorite_id': favorite_id,
                    'news_id': news_id,
                    'title': clean_title,
                    'category': category or 'geral',
                    'notes': clean_notes,
                    'tags': clean_tags,
                    'added_at': datetime.now().isoformat()
                },
                message="Artigo adicionado aos favoritos"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("adicionar favorito", {"user_id": user_id, "news_id": news_id, "error": str(e)})
    
    def add_favorite_by_url(self, user_id: int, url: str, title: str, 
                           description: str = "", source: str = "", 
                           image_url: str = "", category: str = "geral",
                           notes: str = "", tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Adiciona artigo externo aos favoritos usando URL"""
        try:
            if not url or not title:
                return False, "URL e título são obrigatórios"
            
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Verificar se URL já está nos favoritos
            existing = self.db.buscar("""
                SELECT id FROM favorites WHERE user_id = ? AND external_url = ?
            """, (user_id, url))
            
            if existing:
                self.db.desconectar()
                return False, "Artigo já está nos favoritos"
            
            # Preparar tags
            tags_str = ','.join(tags) if tags else ''
            
            # Adicionar aos favoritos
            self.db.executar("""
                INSERT INTO favorites (user_id, external_url, title, description, 
                                     source, image_url, category, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, url, title, description, source, 
                  image_url, category, notes, tags_str))
            
            self.db.desconectar()
            return True, "Artigo externo adicionado aos favoritos"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao adicionar favorito externo: {e}")
            return False, f"Erro ao adicionar favorito: {str(e)}"
    
    def remove_favorite(self, user_id: int, favorite_id: int) -> Tuple[bool, str]:
        """Remove artigo dos favoritos"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Verificar se favorito existe e pertence ao usuário
            existing = self.db.buscar("""
                SELECT id, title FROM favorites WHERE id = ? AND user_id = ?
            """, (favorite_id, user_id))
            
            if not existing:
                self.db.desconectar()
                return False, "Favorito não encontrado ou não pertence ao utilizador"
            
            title = existing[0][1]
            
            # Remover favorito
            self.db.executar("""
                DELETE FROM favorites WHERE id = ? AND user_id = ?
            """, (favorite_id, user_id))
            
            self.db.desconectar()
            return True, f"Artigo '{title}' removido dos favoritos"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao remover favorito: {e}")
            return False, f"Erro ao remover favorito: {str(e)}"
    
    def remove_favorite_by_news_id(self, user_id: int, news_id: int) -> Tuple[bool, str]:
        """Remove favorito usando ID do artigo na tabela news"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Buscar e remover favorito
            existing = self.db.buscar("""
                SELECT id, title FROM favorites WHERE user_id = ? AND news_id = ?
            """, (user_id, news_id))
            
            if not existing:
                self.db.desconectar()
                return False, "Artigo não está nos favoritos"
            
            title = existing[0][1]
            
            self.db.executar("""
                DELETE FROM favorites WHERE user_id = ? AND news_id = ?
            """, (user_id, news_id))
            
            self.db.desconectar()
            return True, f"Artigo '{title}' removido dos favoritos"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao remover favorito por news_id: {e}")
            return False, f"Erro ao remover favorito: {str(e)}"
    
    @api_error_handler
    def get_user_favorites(self, user_id: int, category: Optional[str] = None, 
                          limit: int = 50, offset: int = 0,
                          sort_by: str = 'added_at', order: str = 'DESC') -> Dict:
        """Lista favoritos do utilizador"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if limit < 1 or limit > 100:
            raise create_validation_error("Limite deve ser entre 1 e 100")
        
        if offset < 0:
            raise create_validation_error("Offset deve ser >= 0")
        
        # Validar parâmetros de ordenação
        valid_sort_fields = ['added_at', 'title', 'category', 'is_read']
        if sort_by not in valid_sort_fields:
            raise create_validation_error(f"Campo de ordenação inválido: {sort_by}")
        
        if order.upper() not in ['ASC', 'DESC']:
            raise create_validation_error("Ordem deve ser ASC ou DESC")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id})
            
            # Construir query base
            query = """
                SELECT id, news_id, external_url, title, description, source, 
                       image_url, category, added_at, is_read, notes, tags
                FROM favorites
                WHERE user_id = ?
            """
            params: List = [user_id]
            
            # Filtrar por categoria se especificado
            if category and category != 'all':
                category = sanitize_user_input(category, 50)
                query += " AND category = ?"
                params.append(category)
            
            # Query para contar total
            count_query = query.replace("SELECT id, news_id, external_url, title, description, source, image_url, category, added_at, is_read, notes, tags", "SELECT COUNT(*)")
            
            total_result = self.db.buscar(count_query, params)
            total_count = total_result[0][0] if total_result else 0
            
            # Adicionar ordenação e paginação
            query += f" ORDER BY {sort_by} {order.upper()}"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            favorites_data = self.db.buscar(query, params)
            
            self.db.desconectar()
            
            # Formatar dados
            favorites = []
            for favorite in (favorites_data or []):
                (fav_id, news_id, external_url, title, description, source,
                 image_url, cat, added_at, is_read, notes, tags) = favorite
                
                # Limpar e formatar dados
                clean_title = clean_text(title) if title else ""
                clean_description = clean_text(description) if description else ""
                tags_list = [tag.strip() for tag in (tags or "").split(',') if tag.strip()]
                
                favorite_item = {
                    'id': fav_id,
                    'news_id': news_id,
                    'external_url': external_url,
                    'title': clean_title,
                    'description': clean_description,
                    'source': source,
                    'image_url': image_url,
                    'category': cat,
                    'added_at': added_at,
                    'added_at_formatted': format_date_portuguese(added_at) if added_at else None,
                    'is_read': bool(is_read),
                    'notes': notes,
                    'tags': tags_list,
                    'is_external': bool(external_url and not news_id)
                }
                
                favorites.append(favorite_item)
            
            return format_success_response(
                data={
                    'favorites': favorites,
                    'pagination': {
                        'total': total_count,
                        'limit': limit,
                        'offset': offset,
                        'has_more': offset + len(favorites) < total_count,
                        'next_offset': offset + limit if offset + len(favorites) < total_count else None
                    },
                    'filter': {
                        'category': category,
                        'sort_by': sort_by,
                        'order': order
                    }
                },
                message=f"{len(favorites)} favoritos encontrados"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("buscar favoritos", {"user_id": user_id, "error": str(e)})
    
    @api_error_handler
    def update_read_status(self, user_id: int, favorite_id: int, is_read: bool) -> Dict:
        """Atualiza o status de leitura de um favorito"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if not favorite_id or favorite_id <= 0:
            raise create_validation_error("ID de favorito inválido")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id, "favorite_id": favorite_id})
            
            # Verificar se favorito existe e pertence ao usuário
            existing = self.db.buscar("""
                SELECT id, title FROM favorites WHERE id = ? AND user_id = ?
            """, (favorite_id, user_id))
            
            if not existing:
                self.db.desconectar()
                raise create_not_found_error("Favorito", str(favorite_id))
            
            title = existing[0][1]
            
            # Atualizar status de leitura
            self.db.executar("""
                UPDATE favorites SET is_read = ? WHERE id = ? AND user_id = ?
            """, (is_read, favorite_id, user_id))
            
            self.db.desconectar()
            
            status_text = "lido" if is_read else "não lido"
            return format_success_response(
                data={
                    'favorite_id': favorite_id,
                    'is_read': is_read,
                    'title': title
                },
                message=f"Artigo '{title}' marcado como {status_text}"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("atualizar status", {"user_id": user_id, "favorite_id": favorite_id, "error": str(e)})
    
    @api_error_handler
    def update_notes(self, user_id: int, favorite_id: int, notes: str) -> Dict:
        """Atualiza as notas de um favorito"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if not favorite_id or favorite_id <= 0:
            raise create_validation_error("ID de favorito inválido")
        
        # Limpar e validar notas
        clean_notes = sanitize_user_input(notes, 1000) if notes else ""
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id, "favorite_id": favorite_id})
            
            # Verificar se favorito existe e pertence ao usuário
            existing = self.db.buscar("""
                SELECT id, title FROM favorites WHERE id = ? AND user_id = ?
            """, (favorite_id, user_id))
            
            if not existing:
                self.db.desconectar()
                raise create_not_found_error("Favorito", str(favorite_id))
            
            title = existing[0][1]
            
            # Atualizar notas
            self.db.executar("""
                UPDATE favorites SET notes = ? WHERE id = ? AND user_id = ?
            """, (clean_notes, favorite_id, user_id))
            
            self.db.desconectar()
            
            return format_success_response(
                data={
                    'favorite_id': favorite_id,
                    'notes': clean_notes,
                    'title': title
                },
                message=f"Notas do artigo '{title}' atualizadas"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("atualizar notas", {"user_id": user_id, "favorite_id": favorite_id, "error": str(e)})
    
    @api_error_handler
    def get_user_favorites_stats(self, user_id: int) -> Dict:
        """Obtém estatísticas dos favoritos do usuário"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id})
            
            # Contar total de favoritos
            total_result = self.db.buscar("""
                SELECT COUNT(*) FROM favorites WHERE user_id = ?
            """, (user_id,))
            total_favorites = total_result[0][0] if total_result else 0
            
            # Contar favoritos não lidos
            unread_result = self.db.buscar("""
                SELECT COUNT(*) FROM favorites WHERE user_id = ? AND is_read = FALSE
            """, (user_id,))
            unread_favorites = unread_result[0][0] if unread_result else 0
            
            # Contar favoritos lidos
            read_favorites = total_favorites - unread_favorites
            
            # Calcular porcentagem de lidos
            read_percentage = (read_favorites / total_favorites * 100) if total_favorites > 0 else 0
            
            # Estatísticas por categoria
            categories_result = self.db.buscar("""
                SELECT category, COUNT(*) as count
                FROM favorites 
                WHERE user_id = ?
                GROUP BY category
                ORDER BY count DESC
            """, (user_id,))
            
            categories_stats = []
            for cat_row in (categories_result or []):
                categories_stats.append({
                    'category': cat_row[0],
                    'count': cat_row[1]
                })
            
            # Favoritos recentes (últimos 7 dias)
            recent_result = self.db.buscar("""
                SELECT COUNT(*) FROM favorites 
                WHERE user_id = ? AND added_at >= datetime('now', '-7 days')
            """, (user_id,))
            recent_favorites = recent_result[0][0] if recent_result else 0
            
            self.db.desconectar()
            
            return format_success_response(
                data={
                    'total_favorites': total_favorites,
                    'read_favorites': read_favorites,
                    'unread_favorites': unread_favorites,
                    'read_percentage': round(read_percentage, 1),
                    'recent_favorites': recent_favorites,
                    'categories': categories_stats
                },
                message="Estatísticas de favoritos obtidas"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("buscar estatísticas", {"user_id": user_id, "error": str(e)})
    
    @api_error_handler
    def get_user_categories(self, user_id: int) -> Dict:
        """Obtém lista de categorias dos favoritos do usuário"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id})
            
            # Buscar categorias únicas dos favoritos do usuário
            categories_result = self.db.buscar("""
                SELECT DISTINCT category
                FROM favorites 
                WHERE user_id = ? AND category IS NOT NULL
                ORDER BY category
            """, (user_id,))
            
            self.db.desconectar()
            
            categories = [row[0] for row in (categories_result or []) if row[0]]
            
            return format_success_response(
                data=categories,
                message=f"{len(categories)} categorias encontradas"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("buscar categorias", {"user_id": user_id, "error": str(e)})
    
    @api_error_handler
    def is_favorite(self, user_id: int, news_id: int) -> Dict:
        """Verifica se um artigo está nos favoritos do usuário"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if not news_id or news_id <= 0:
            raise create_validation_error("ID de notícia inválido")
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id, "news_id": news_id})
            
            # Verificar se artigo está nos favoritos
            favorite_result = self.db.buscar("""
                SELECT id, is_read, notes, added_at
                FROM favorites 
                WHERE user_id = ? AND news_id = ?
            """, (user_id, news_id))
            
            self.db.desconectar()
            
            if favorite_result:
                favorite_id, is_read, notes, added_at = favorite_result[0]
                return format_success_response(
                    data={
                        'is_favorite': True,
                        'favorite_id': favorite_id,
                        'is_read': bool(is_read),
                        'notes': notes,
                        'added_at': added_at
                    },
                    message="Artigo está nos favoritos"
                )
            else:
                return format_success_response(
                    data={'is_favorite': False},
                    message="Artigo não está nos favoritos"
                )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("verificar favorito", {"user_id": user_id, "news_id": news_id, "error": str(e)})
    
    @api_error_handler
    def add_favorite(self, user_id: int, title: str, description: str = "", 
                    external_url: str = "", source: str = "", category: str = "geral",
                    notes: str = "", tags: Optional[List[str]] = None) -> Dict:
        """Adiciona artigo externo aos favoritos"""
        if not user_id or user_id <= 0:
            raise create_validation_error("ID de usuário inválido")
        
        if not title:
            raise create_validation_error("Título é obrigatório")
        
        # Limpar e validar entradas
        clean_title = sanitize_user_input(title, 200)
        clean_description = sanitize_user_input(description, 500) if description else ""
        clean_url = sanitize_user_input(external_url, 500) if external_url else ""
        clean_source = sanitize_user_input(source, 100) if source else ""
        clean_category = sanitize_user_input(category, 50) if category else "geral"
        clean_notes = sanitize_user_input(notes, 1000) if notes else ""
        clean_tags = [sanitize_user_input(tag, 50) for tag in (tags or [])][:10]  # Max 10 tags
        
        try:
            if not self.db.conectar():
                raise create_database_error("conectar", {"user_id": user_id})
            
            # Verificar se URL já está nos favoritos (se fornecida)
            if clean_url:
                existing = self.db.buscar("""
                    SELECT id FROM favorites WHERE user_id = ? AND external_url = ?
                """, (user_id, clean_url))
                
                if existing:
                    self.db.desconectar()
                    raise create_duplicate_error("Artigo já está nos favoritos")
            
            # Preparar tags
            tags_str = ','.join(clean_tags) if clean_tags else ''
            
            # Adicionar aos favoritos
            self.db.executar("""
                INSERT INTO favorites (user_id, external_url, title, description, 
                                     source, category, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, clean_url, clean_title, clean_description, 
                  clean_source, clean_category, clean_notes, tags_str))
            
            # Buscar ID do favorito criado
            favorite_result = self.db.buscar("""
                SELECT id FROM favorites WHERE user_id = ? AND title = ? 
                ORDER BY added_at DESC LIMIT 1
            """, (user_id, clean_title))
            
            favorite_id = favorite_result[0][0] if favorite_result else None
            
            self.db.desconectar()
            
            return format_success_response(
                data={
                    'favorite_id': favorite_id,
                    'title': clean_title,
                    'external_url': clean_url,
                    'category': clean_category,
                    'notes': clean_notes,
                    'tags': clean_tags,
                    'added_at': datetime.now().isoformat()
                },
                message="Artigo externo adicionado aos favoritos"
            )
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            raise create_database_error("adicionar favorito externo", {"user_id": user_id, "error": str(e)})

# Instância global
favorites_manager = FavoritesManager()

# Funções de conveniência para API
def add_news_to_favorites(user_id: int, news_id: int, notes: str = "", tags: Optional[List[str]] = None) -> Dict:
    """Função de conveniência para adicionar notícia aos favoritos"""
    return favorites_manager.add_favorite_by_news_id(user_id, news_id, notes, tags)

def get_favorites_list(user_id: int, category: Optional[str] = None, limit: int = 50) -> Dict:
    """Função de conveniência para listar favoritos"""
    return favorites_manager.get_user_favorites(user_id, category, limit)

def remove_from_favorites(user_id: int, favorite_id: int) -> Dict:
    """Função de conveniência para remover favorito"""
    result = favorites_manager.remove_favorite(user_id, favorite_id)
    if result[0]:  # success
        return format_success_response(
            data={'removed': True, 'favorite_id': favorite_id},
            message=result[1]
        )
    else:
        raise create_database_error("remover favorito", {"error": result[1]})