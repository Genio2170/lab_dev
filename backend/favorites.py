from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database.bd import Conexao
import logging
import hashlib

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
    
    def add_favorite_by_news_id(self, user_id: int, news_id: int, 
                               notes: str = "", tags: List[str] = None) -> Tuple[bool, str]:
        """Adiciona artigo aos favoritos usando ID da tabela news"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Verificar se artigo existe na tabela news
            news_data = self.db.buscar("""
                SELECT n.title, n.description, n.source, n.image_url, c.name as category
                FROM news n
                LEFT JOIN categories c ON n.category_id = c.id
                WHERE n.id = ?
            """, (news_id,))
            
            if not news_data:
                self.db.desconectar()
                return False, "Artigo não encontrado"
            
            title, description, source, image_url, category = news_data[0]
            
            # Verificar se já está nos favoritos
            existing = self.db.buscar("""
                SELECT id FROM favorites WHERE user_id = ? AND news_id = ?
            """, (user_id, news_id))
            
            if existing:
                self.db.desconectar()
                return False, "Artigo já está nos favoritos"
            
            # Preparar tags
            tags_str = ','.join(tags) if tags else ''
            
            # Adicionar aos favoritos
            self.db.executar("""
                INSERT INTO favorites (user_id, news_id, title, description, source, 
                                     image_url, category, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, news_id, title, description, source, 
                  image_url, category or 'geral', notes, tags_str))
            
            self.db.desconectar()
            return True, "Artigo adicionado aos favoritos"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao adicionar favorito: {e}")
            return False, f"Erro ao adicionar favorito: {str(e)}"
    
    def add_favorite_by_url(self, user_id: int, url: str, title: str, 
                           description: str = "", source: str = "", 
                           image_url: str = "", category: str = "geral",
                           notes: str = "", tags: List[str] = None) -> Tuple[bool, str]:
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
    
    def get_user_favorites(self, user_id: int, category: str = None, 
                          limit: int = 50, offset: int = 0,
                          sort_by: str = 'added_at', order: str = 'DESC') -> Tuple[List[Dict], str]:
        """Lista favoritos do utilizador"""
        try:
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            # Construir query base
            query = """
                SELECT id, news_id, external_url, title, description, source, 
                       image_url, category, added_at, is_read, notes, tags
                FROM favorites
                WHERE user_id = ?
            """
            params = [user_id]
            
            # Filtrar por categoria se especificado
            if category and category != 'all':
                query += " AND LOWER(category) = LOWER(?)"
                params.append(category)
            
            # Ordenação
            allowed_sorts = ['added_at', 'title', 'source', 'category']
            allowed_orders = ['ASC', 'DESC']
            
            if sort_by not in allowed_sorts:
                sort_by = 'added_at'
            if order not in allowed_orders:
                order = 'DESC'
            
            query += f" ORDER BY {sort_by} {order}"
            
            # Paginação
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            favorites_data = self.db.buscar(query, params)
            
            self.db.desconectar()
            
            favorites = []
            for fav_data in favorites_data:
                (fav_id, news_id, external_url, title, description, source,
                 image_url, category, added_at, is_read, notes, tags_str) = fav_data
                
                # Processar tags
                tags = tags_str.split(',') if tags_str else []
                tags = [tag.strip() for tag in tags if tag.strip()]
                
                favorites.append({
                    'id': fav_id,
                    'news_id': news_id,
                    'url': self._get_article_url(news_id, external_url),
                    'external_url': external_url,
                    'title': title,
                    'description': description,
                    'source': source,
                    'image_url': image_url,
                    'category': category,
                    'added_at': added_at,
                    'is_read': bool(is_read),
                    'notes': notes or '',
                    'tags': tags,
                    'type': 'internal' if news_id else 'external'
                })
            
            return favorites, f"{len(favorites)} favoritos encontrados"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao listar favoritos: {e}")
            return [], f"Erro ao listar favoritos: {str(e)}"
    
    def mark_as_read(self, user_id: int, favorite_id: int, is_read: bool = True) -> Tuple[bool, str]:
        """Marca/desmarca favorito como lido"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Verificar se favorito existe e pertence ao usuário
            existing = self.db.buscar("""
                SELECT id FROM favorites WHERE id = ? AND user_id = ?
            """, (favorite_id, user_id))
            
            if not existing:
                self.db.desconectar()
                return False, "Favorito não encontrado"
            
            # Atualizar status de leitura
            self.db.executar("""
                UPDATE favorites SET is_read = ? WHERE id = ? AND user_id = ?
            """, (is_read, favorite_id, user_id))
            
            self.db.desconectar()
            status = "lido" if is_read else "não lido"
            return True, f"Favorito marcado como {status}"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao marcar como lido: {e}")
            return False, f"Erro ao atualizar status: {str(e)}"
    
    def update_favorite_notes(self, user_id: int, favorite_id: int, notes: str) -> Tuple[bool, str]:
        """Atualiza notas do favorito"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Verificar se favorito existe e pertence ao usuário
            existing = self.db.buscar("""
                SELECT id FROM favorites WHERE id = ? AND user_id = ?
            """, (favorite_id, user_id))
            
            if not existing:
                self.db.desconectar()
                return False, "Favorito não encontrado"
            
            # Atualizar notas
            self.db.executar("""
                UPDATE favorites SET notes = ? WHERE id = ? AND user_id = ?
            """, (notes, favorite_id, user_id))
            
            self.db.desconectar()
            return True, "Notas atualizadas com sucesso"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao atualizar notas: {e}")
            return False, f"Erro ao atualizar notas: {str(e)}"
    
    def update_favorite_tags(self, user_id: int, favorite_id: int, tags: List[str]) -> Tuple[bool, str]:
        """Atualiza tags do favorito"""
        try:
            if not self.db.conectar():
                return False, "Erro de conexão com a base de dados"
            
            # Verificar se favorito existe e pertence ao usuário
            existing = self.db.buscar("""
                SELECT id FROM favorites WHERE id = ? AND user_id = ?
            """, (favorite_id, user_id))
            
            if not existing:
                self.db.desconectar()
                return False, "Favorito não encontrado"
            
            # Processar tags (remover vazias e duplicatas)
            clean_tags = list(set([tag.strip() for tag in tags if tag.strip()]))
            tags_str = ','.join(clean_tags)
            
            # Atualizar tags
            self.db.executar("""
                UPDATE favorites SET tags = ? WHERE id = ? AND user_id = ?
            """, (tags_str, favorite_id, user_id))
            
            self.db.desconectar()
            return True, f"Tags atualizadas: {clean_tags}"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao atualizar tags: {e}")
            return False, f"Erro ao atualizar tags: {str(e)}"
    
    def search_favorites(self, user_id: int, search_term: str, 
                        search_in: List[str] = None) -> Tuple[List[Dict], str]:
        """Pesquisa nos favoritos do utilizador"""
        try:
            if not search_term or len(search_term.strip()) < 2:
                return [], "Termo de pesquisa deve ter pelo menos 2 caracteres"
            
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            # Campos de pesquisa padrão
            if not search_in:
                search_in = ['title', 'description', 'notes', 'tags']
            
            search_term = f"%{search_term.strip()}%"
            
            # Construir condições de pesquisa
            search_conditions = []
            params = [user_id]
            
            if 'title' in search_in:
                search_conditions.append("LOWER(title) LIKE LOWER(?)")
                params.append(search_term)
            
            if 'description' in search_in:
                search_conditions.append("LOWER(description) LIKE LOWER(?)")
                params.append(search_term)
            
            if 'notes' in search_in:
                search_conditions.append("LOWER(notes) LIKE LOWER(?)")
                params.append(search_term)
            
            if 'tags' in search_in:
                search_conditions.append("LOWER(tags) LIKE LOWER(?)")
                params.append(search_term)
            
            if not search_conditions:
                return [], "Nenhum campo de pesquisa válido especificado"
            
            query = f"""
                SELECT id, news_id, external_url, title, description, source, 
                       image_url, category, added_at, is_read, notes, tags
                FROM favorites
                WHERE user_id = ? AND ({' OR '.join(search_conditions)})
                ORDER BY added_at DESC
                LIMIT 100
            """
            
            results = self.db.buscar(query, params)
            
            self.db.desconectar()
            
            favorites = []
            for result in results:
                (fav_id, news_id, external_url, title, description, source,
                 image_url, category, added_at, is_read, notes, tags_str) = result
                
                tags = tags_str.split(',') if tags_str else []
                tags = [tag.strip() for tag in tags if tag.strip()]
                
                favorites.append({
                    'id': fav_id,
                    'news_id': news_id,
                    'url': self._get_article_url(news_id, external_url),
                    'external_url': external_url,
                    'title': title,
                    'description': description,
                    'source': source,
                    'image_url': image_url,
                    'category': category,
                    'added_at': added_at,
                    'is_read': bool(is_read),
                    'notes': notes or '',
                    'tags': tags,
                    'type': 'internal' if news_id else 'external'
                })
            
            return favorites, f"{len(favorites)} favoritos encontrados"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro na pesquisa de favoritos: {e}")
            return [], f"Erro na pesquisa: {str(e)}"
    
    def get_favorites_by_category(self, user_id: int) -> Tuple[Dict[str, int], str]:
        """Obtém contagem de favoritos por categoria"""
        try:
            if not self.db.conectar():
                return {}, "Erro de conexão com a base de dados"
            
            category_counts = self.db.buscar("""
                SELECT category, COUNT(*) as count
                FROM favorites
                WHERE user_id = ?
                GROUP BY category
                ORDER BY count DESC
            """, (user_id,))
            
            self.db.desconectar()
            
            categories = {}
            for cat_data in category_counts:
                category, count = cat_data
                categories[category] = count
            
            return categories, f"{len(categories)} categorias com favoritos"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao obter categorias de favoritos: {e}")
            return {}, f"Erro ao obter categorias: {str(e)}"
    
    def get_favorites_statistics(self, user_id: int) -> Tuple[Dict, str]:
        """Obtém estatísticas dos favoritos do utilizador"""
        try:
            if not self.db.conectar():
                return {}, "Erro de conexão com a base de dados"
            
            # Estatísticas básicas
            total = self.db.buscar("SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,))[0][0]
            read = self.db.buscar("SELECT COUNT(*) FROM favorites WHERE user_id = ? AND is_read = 1", (user_id,))[0][0]
            
            # Favoritos recentes (última semana)
            recent = self.db.buscar("""
                SELECT COUNT(*) FROM favorites 
                WHERE user_id = ? AND added_at >= datetime('now', '-7 days')
            """, (user_id,))[0][0]
            
            # Categoria mais favoritada
            top_category = self.db.buscar("""
                SELECT category, COUNT(*) as count
                FROM favorites
                WHERE user_id = ?
                GROUP BY category
                ORDER BY count DESC
                LIMIT 1
            """, (user_id,))
            
            # Fonte mais favoritada
            top_source = self.db.buscar("""
                SELECT source, COUNT(*) as count
                FROM favorites
                WHERE user_id = ? AND source IS NOT NULL AND source != ''
                GROUP BY source
                ORDER BY count DESC
                LIMIT 1
            """, (user_id,))
            
            self.db.desconectar()
            
            stats = {
                'total_favorites': total,
                'read_favorites': read,
                'unread_favorites': total - read,
                'read_percentage': (read / total * 100) if total > 0 else 0,
                'recent_additions': recent,
                'top_category': top_category[0][0] if top_category else 'N/A',
                'top_category_count': top_category[0][1] if top_category else 0,
                'top_source': top_source[0][0] if top_source else 'N/A',
                'top_source_count': top_source[0][1] if top_source else 0
            }
            
            return stats, "Estatísticas calculadas com sucesso"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}, f"Erro ao calcular estatísticas: {str(e)}"
    
    def get_all_tags(self, user_id: int) -> Tuple[List[str], str]:
        """Obtém todas as tags usadas pelo utilizador"""
        try:
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            tags_data = self.db.buscar("""
                SELECT tags FROM favorites 
                WHERE user_id = ? AND tags IS NOT NULL AND tags != ''
            """, (user_id,))
            
            self.db.desconectar()
            
            all_tags = set()
            for tag_row in tags_data:
                tags_str = tag_row[0]
                if tags_str:
                    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                    all_tags.update(tags)
            
            sorted_tags = sorted(list(all_tags))
            return sorted_tags, f"{len(sorted_tags)} tags encontradas"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao obter tags: {e}")
            return [], f"Erro ao obter tags: {str(e)}"
    
    def is_favorite(self, user_id: int, news_id: int = None, url: str = None) -> bool:
        """Verifica se artigo está nos favoritos"""
        try:
            if not self.db.conectar():
                return False
            
            if news_id:
                existing = self.db.buscar("""
                    SELECT id FROM favorites WHERE user_id = ? AND news_id = ?
                """, (user_id, news_id))
            elif url:
                existing = self.db.buscar("""
                    SELECT id FROM favorites WHERE user_id = ? AND external_url = ?
                """, (user_id, url))
            else:
                return False
            
            self.db.desconectar()
            return len(existing) > 0
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao verificar favorito: {e}")
            return False
    
    def _get_article_url(self, news_id: Optional[int], external_url: Optional[str]) -> Optional[str]:
        """Obtém URL do artigo (interno ou externo)"""
        if external_url:
            return external_url
        elif news_id:
            # Para artigos internos, você poderia construir URL baseada no ID
            return f"/article/{news_id}"
        return None
    
    def export_favorites(self, user_id: int) -> Tuple[Optional[Dict], str]:
        """Exporta favoritos do utilizador"""
        try:
            favorites, message = self.get_user_favorites(user_id, limit=1000)
            if not favorites:
                return None, message
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'user_id': user_id,
                'total_favorites': len(favorites),
                'favorites': favorites
            }
            
            return export_data, f"Exportação concluída: {len(favorites)} favoritos"
            
        except Exception as e:
            logger.error(f"Erro ao exportar favoritos: {e}")
            return None, f"Erro ao exportar: {str(e)}"