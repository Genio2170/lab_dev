from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from database.bd import Conexao
import logging

logger = logging.getLogger(__name__)

class CategoryManager:
    """Gerenciador para categorização e filtragem de notícias"""
    
    def __init__(self):
        self.db = Conexao()
        
        # Mapeamento de palavras-chave para categorias (português)
        self.keywords_mapping = {
            'tecnologia': [
                'tecnologia', 'software', 'hardware', 'inteligência artificial',
                'machine learning', 'programação', 'desenvolvimento', 'aplicações',
                'smartphone', 'computador', 'internet', 'digital', 'online',
                'startup', 'inovação', 'tech', 'google', 'microsoft', 'apple',
                'meta', 'facebook', 'instagram', 'whatsapp', 'twitter', 'tiktok',
                'cibersegurança', 'blockchain', 'bitcoin', 'criptomoeda',
                'robótica', 'drones', 'iot', 'cloud', 'nuvem', 'data center'
            ],
            'politica': [
                'política', 'governo', 'presidente', 'ministro', 'parlamento',
                'assembleia', 'eleições', 'votação', 'partido', 'democracia',
                'ditadura', 'corrupção', 'escândalo', 'lei', 'legislação',
                'constituição', 'tribunal', 'justiça', 'estado', 'nação',
                'diplomacia', 'relações internacionais', 'união europeia',
                'nato', 'onu', 'guerra', 'conflito', 'paz', 'tratado'
            ],
            'economia': [
                'economia', 'financeiro', 'mercado', 'bolsa', 'investimento',
                'banco', 'crédito', 'empréstimo', 'inflação', 'deflação',
                'pib', 'crescimento', 'recessão', 'crise', 'recovery',
                'juros', 'taxa', 'câmbio', 'moeda', 'euro', 'dólar',
                'empresa', 'negócio', 'startup', 'ipo', 'fusão', 'aquisição',
                'emprego', 'desemprego', 'salário', 'pensão', 'reforma'
            ],
            'desporto': [
                'futebol', 'basquetebol', 'ténis', 'natação', 'atletismo',
                'ciclismo', 'motociclismo', 'automobilismo', 'formula 1',
                'campeonato', 'liga', 'copa', 'mundial', 'europeu',
                'olimpíadas', 'paralímpicos', 'jogador', 'atleta', 'treinador',
                'clube', 'equipa', 'vitória', 'derrota', 'golo', 'ponto',
                'benfica', 'porto', 'sporting', 'braga', 'champions league'
            ],
            'saude': [
                'saúde', 'medicina', 'hospital', 'médico', 'enfermeiro',
                'doença', 'sintoma', 'tratamento', 'medicamento', 'vacina',
                'pandemia', 'epidemia', 'vírus', 'bactéria', 'covid',
                'cancro', 'diabetes', 'coração', 'mental', 'psicologia',
                'nutrição', 'dieta', 'exercício', 'bem-estar', 'stress',
                'investigação médica', 'ensaio clínico', 'farmácia'
            ],
            'ciencia': [
                'ciência', 'investigação', 'estudo', 'descoberta', 'experiência',
                'laboratório', 'universidade', 'professor', 'científico',
                'física', 'química', 'biologia', 'matemática', 'astronomia',
                'espaço', 'planeta', 'estrela', 'nasa', 'esa', 'foguete',
                'energia', 'renovável', 'solar', 'eólica', 'nuclear',
                'ambiente', 'clima', 'aquecimento global', 'sustentabilidade'
            ],
            'cultura': [
                'cultura', 'arte', 'música', 'cinema', 'teatro', 'dança',
                'literatura', 'livro', 'autor', 'escritor', 'poeta',
                'museu', 'exposição', 'festival', 'concerto', 'espetáculo',
                'filme', 'série', 'ator', 'actriz', 'realizador', 'produtor',
                'artista', 'pintor', 'escultor', 'galeria', 'património',
                'tradição', 'costumes', 'folclore', 'história', 'arqueologia'
            ],
            'internacional': [
                'internacional', 'mundial', 'global', 'país', 'nação',
                'fronteira', 'imigração', 'refugiados', 'diplomacia',
                'embaixada', 'consulado', 'tratado', 'acordo', 'cimeira',
                'união europeia', 'estados unidos', 'china', 'rússia',
                'brasil', 'áfrica', 'ásia', 'europa', 'américa', 'oceania'
            ],
            'local': [
                'portugal', 'lisboa', 'porto', 'coimbra', 'braga', 'faro',
                'aveiro', 'viseu', 'leiria', 'santarém', 'setúbal',
                'câmara municipal', 'autarquia', 'junta de freguesia',
                'município', 'região', 'distrito', 'concelho', 'aldeia',
                'cidade', 'vila', 'bairro', 'rua', 'avenida', 'praça'
            ],
            'ambiente': [
                'ambiente', 'ecologia', 'natureza', 'biodiversidade',
                'conservação', 'proteção', 'poluição', 'sustentabilidade',
                'reciclagem', 'energia renovável', 'solar', 'eólica',
                'floresta', 'árvore', 'animal', 'espécie', 'extinção',
                'clima', 'aquecimento global', 'carbono', 'emissões',
                'oceano', 'mar', 'rio', 'água', 'ar', 'solo'
            ]
        }
        
        # Categorias em diferentes idiomas para normalização
        self.category_translations = {
            'business': 'economia',
            'technology': 'tecnologia',
            'politics': 'politica',
            'sport': 'desporto',
            'sports': 'desporto',
            'health': 'saude',
            'science': 'ciencia',
            'entertainment': 'cultura',
            'world': 'internacional',
            'general': 'geral',
            'local': 'local',
            'environment': 'ambiente'
        }
    
    def get_all_categories(self) -> Tuple[List[Dict], str]:
        """Busca todas as categorias da base de dados"""
        try:
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            categories_data = self.db.buscar("""
                SELECT id, name, 
                       (SELECT COUNT(*) FROM news WHERE category_id = categories.id) as news_count
                FROM categories 
                ORDER BY name
            """)
            
            self.db.desconectar()
            
            categories = []
            for cat_data in categories_data:
                category_id, name, news_count = cat_data
                categories.append({
                    'id': category_id,
                    'name': name,
                    'slug': self._create_slug(name),
                    'news_count': news_count or 0,
                    'keywords': self.keywords_mapping.get(name.lower(), [])
                })
            
            return categories, "Categorias carregadas com sucesso"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao buscar categorias: {e}")
            return [], f"Erro ao buscar categorias: {str(e)}"
    
    def get_category_by_id(self, category_id: int) -> Tuple[Optional[Dict], str]:
        """Busca categoria específica por ID"""
        try:
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            category_data = self.db.buscar("""
                SELECT id, name,
                       (SELECT COUNT(*) FROM news WHERE category_id = categories.id) as news_count
                FROM categories 
                WHERE id = ?
            """, (category_id,))
            
            self.db.desconectar()
            
            if not category_data:
                return None, "Categoria não encontrada"
            
            cat_id, name, news_count = category_data[0]
            category = {
                'id': cat_id,
                'name': name,
                'slug': self._create_slug(name),
                'news_count': news_count or 0,
                'keywords': self.keywords_mapping.get(name.lower(), [])
            }
            
            return category, "Categoria encontrada"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao buscar categoria {category_id}: {e}")
            return None, f"Erro ao buscar categoria: {str(e)}"
    
    def get_category_by_name(self, name: str) -> Tuple[Optional[Dict], str]:
        """Busca categoria por nome"""
        try:
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            category_data = self.db.buscar("""
                SELECT id, name,
                       (SELECT COUNT(*) FROM news WHERE category_id = categories.id) as news_count
                FROM categories 
                WHERE LOWER(name) = LOWER(?)
            """, (name,))
            
            self.db.desconectar()
            
            if not category_data:
                return None, f"Categoria '{name}' não encontrada"
            
            cat_id, cat_name, news_count = category_data[0]
            category = {
                'id': cat_id,
                'name': cat_name,
                'slug': self._create_slug(cat_name),
                'news_count': news_count or 0,
                'keywords': self.keywords_mapping.get(cat_name.lower(), [])
            }
            
            return category, "Categoria encontrada"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao buscar categoria '{name}': {e}")
            return None, f"Erro ao buscar categoria: {str(e)}"
    
    def create_category(self, name: str) -> Tuple[Optional[int], str]:
        """Cria nova categoria"""
        try:
            if not name or len(name.strip()) < 2:
                return None, "Nome da categoria deve ter pelo menos 2 caracteres"
            
            name = name.strip().title()
            
            if not self.db.conectar():
                return None, "Erro de conexão com a base de dados"
            
            # Verificar se categoria já existe
            existing = self.db.buscar("""
                SELECT id FROM categories WHERE LOWER(name) = LOWER(?)
            """, (name,))
            
            if existing:
                self.db.desconectar()
                return None, f"Categoria '{name}' já existe"
            
            # Criar categoria
            self.db.executar("""
                INSERT INTO categories (name) VALUES (?)
            """, (name,))
            
            # Buscar ID da categoria criada
            new_category = self.db.buscar("""
                SELECT id FROM categories WHERE LOWER(name) = LOWER(?)
            """, (name,))
            
            self.db.desconectar()
            
            if new_category:
                return new_category[0][0], f"Categoria '{name}' criada com sucesso"
            else:
                return None, "Erro ao criar categoria"
                
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao criar categoria '{name}': {e}")
            return None, f"Erro ao criar categoria: {str(e)}"
    
    def categorize_article(self, title: str, description: str, content: str = "") -> str:
        """Categoriza artigo baseado no conteúdo usando palavras-chave"""
        
        # Combinar todo o texto para análise
        full_text = f"{title} {description} {content}".lower()
        
        # Remover acentos para melhor matching
        full_text = self._remove_accents(full_text)
        
        # Pontuação por categoria
        category_scores = {}
        
        for category, keywords in self.keywords_mapping.items():
            score = 0
            for keyword in keywords:
                keyword = self._remove_accents(keyword.lower())
                
                # Contar ocorrências da palavra-chave
                count = full_text.count(keyword)
                
                if count > 0:
                    # Peso maior para título
                    title_count = self._remove_accents(title.lower()).count(keyword)
                    score += title_count * 3  # Título tem peso 3x
                    
                    # Peso normal para descrição e conteúdo
                    score += count
            
            if score > 0:
                category_scores[category] = score
        
        # Retornar categoria com maior pontuação
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category
        
        return 'geral'  # Categoria padrão
    
    def auto_categorize_article(self, article_data: Dict) -> Tuple[Optional[int], str]:
        """Categoriza automaticamente um artigo e retorna o ID da categoria"""
        
        try:
            category_name = self.categorize_article(
                article_data.get('title', ''),
                article_data.get('description', ''),
                article_data.get('content', '')
            )
            
            # Normalizar nome da categoria se vier em inglês
            category_name = self.category_translations.get(category_name, category_name)
            
            # Buscar ou criar categoria
            category, message = self.get_category_by_name(category_name)
            
            if category:
                return category['id'], f"Categorizado como '{category['name']}'"
            else:
                # Tentar criar nova categoria
                category_id, create_message = self.create_category(category_name)
                if category_id:
                    return category_id, f"Nova categoria '{category_name}' criada"
                else:
                    # Fallback para categoria 'geral'
                    general_category, _ = self.get_category_by_name('geral')
                    if general_category:
                        return general_category['id'], "Categorizado como 'geral' (fallback)"
                    else:
                        return None, "Erro ao categorizar artigo"
                        
        except Exception as e:
            logger.error(f"Erro na categorização automática: {e}")
            return None, f"Erro na categorização: {str(e)}"
    
    def filter_news_by_category(self, category_id: Optional[int] = None, 
                               limit: int = 50, offset: int = 0) -> Tuple[List[Dict], str]:
        """Filtra notícias por categoria"""
        try:
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            if category_id:
                # Filtrar por categoria específica
                news_data = self.db.buscar("""
                    SELECT n.id, n.title, n.description, n.url, n.source, 
                           n.image_url, n.published_at, c.name as category_name
                    FROM news n
                    LEFT JOIN categories c ON n.category_id = c.id
                    WHERE n.category_id = ?
                    ORDER BY n.published_at DESC
                    LIMIT ? OFFSET ?
                """, (category_id, limit, offset))
            else:
                # Buscar todas as notícias
                news_data = self.db.buscar("""
                    SELECT n.id, n.title, n.description, n.url, n.source,
                           n.image_url, n.published_at, c.name as category_name
                    FROM news n
                    LEFT JOIN categories c ON n.category_id = c.id
                    ORDER BY n.published_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
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
            
            return news_list, f"{len(news_list)} notícias encontradas"
            
        except Exception as e:
            if self.db.conexao:
                self.db.desconectar()
            logger.error(f"Erro ao filtrar notícias: {e}")
            return [], f"Erro ao filtrar notícias: {str(e)}"
    
    def get_trending_categories(self, days: int = 7) -> Tuple[List[Dict], str]:
        """Busca categorias com mais notícias nos últimos dias"""
        try:
            if not self.db.conectar():
                return [], "Erro de conexão com a base de dados"
            
            trending_data = self.db.buscar("""
                SELECT c.id, c.name, COUNT(n.id) as news_count
                FROM categories c
                LEFT JOIN news n ON c.id = n.category_id
                WHERE n.published_at >= datetime('now', '-{} days')
                GROUP BY c.id, c.name
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