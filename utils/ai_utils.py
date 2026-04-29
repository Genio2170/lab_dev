#!/usr/bin/env python3
"""
AI Utils - Módulo para funcionalidades inteligentes
Integração com APIs de IA para resumos automáticos e recomendações
"""

import os
import requests
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import time

class AIService:
    """Serviço de IA para resumos e recomendações"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.claude_api_key = os.getenv('CLAUDE_API_KEY', '')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        
        # Cache para evitar chamadas desnecessárias
        self.cache = {}
        self.cache_duration = 3600  # 1 hora
        
    def _get_cache_key(self, text: str, operation: str) -> str:
        """Gera chave de cache baseada no texto e operação"""
        combined = f"{operation}:{text[:500]}"  # Primeiros 500 chars
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Verifica se o cache ainda é válido"""
        if not cache_entry:
            return False
        
        cached_time = cache_entry.get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_duration
    
    def _call_openai_api(self, prompt: str, max_tokens: int = 150) -> Optional[str]:
        """Chama API do OpenAI (GPT)"""
        if not self.api_key:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'Você é um assistente especializado em resumir notícias em português brasileiro.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"OpenAI API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro na chamada OpenAI: {e}")
            return None
    
    def _call_claude_api(self, prompt: str, max_tokens: int = 150) -> Optional[str]:
        """Chama API do Claude (Anthropic)"""
        if not self.claude_api_key:
            return None
            
        try:
            headers = {
                'x-api-key': self.claude_api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': max_tokens,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text'].strip()
            else:
                print(f"Claude API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro na chamada Claude: {e}")
            return None
    
    def _fallback_summary(self, article_text: str, max_length: int = 150) -> str:
        """Resumo básico sem IA (fallback)"""
        # Remove quebras de linha e espaços extra
        clean_text = ' '.join(article_text.split())
        
        # Se o texto é curto, retorna como está
        if len(clean_text) <= max_length:
            return clean_text
        
        # Procura por pontos para cortar no final de frases
        truncated = clean_text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.7:  # Se tem ponto após 70% do tamanho
            return clean_text[:last_period + 1]
        else:
            # Corta na última palavra completa
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return clean_text[:last_space] + "..."
            else:
                return truncated + "..."
    
    def generate_summary(self, article_text: str, title: str = "", max_length: int = 150) -> Tuple[str, str]:
        """
        Gera resumo automático de um artigo
        
        Args:
            article_text: Texto completo do artigo
            title: Título do artigo (opcional)
            max_length: Tamanho máximo do resumo
            
        Returns:
            Tuple[summary, source] - Resumo e fonte ("ai" ou "fallback")
        """
        if not article_text or len(article_text.strip()) < 50:
            return "Artigo muito curto para resumir.", "fallback"
        
        # Verifica cache
        cache_key = self._get_cache_key(article_text, "summary")
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            cached = self.cache[cache_key]
            return cached['result'], cached['source']
        
        # Prepara o prompt
        context = f"Título: {title}\n\n" if title else ""
        prompt = f"""
        {context}Texto do artigo:
        {article_text[:2000]}  

        Por favor, crie um resumo conciso deste artigo em português brasileiro, 
        focando nos pontos principais e informações mais importantes. 
        O resumo deve ter no máximo {max_length} caracteres.
        """
        
        # Tenta diferentes APIs de IA
        summary = None
        source = "fallback"
        
        # 1. Tenta OpenAI primeiro
        if self.api_key:
            summary = self._call_openai_api(prompt, max_tokens=80)
            if summary:
                source = "openai"
        
        # 2. Se falhou, tenta Claude
        if not summary and self.claude_api_key:
            summary = self._call_claude_api(prompt, max_tokens=80)
            if summary:
                source = "claude"
        
        # 3. Fallback manual
        if not summary:
            summary = self._fallback_summary(article_text, max_length)
            source = "fallback"
        
        # Garante que não ultrapassa o limite
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        # Salva no cache
        self.cache[cache_key] = {
            'result': summary,
            'source': source,
            'timestamp': time.time()
        }
        
        return summary, source
    
    def generate_recommendations(self, user_preferences: List[str], 
                               recent_articles: List[Dict], 
                               available_articles: List[Dict]) -> List[Dict]:
        """
        Gera recomendações personalizadas de artigos
        
        Args:
            user_preferences: Lista de categorias/tópicos preferidos
            recent_articles: Artigos lidos recentemente pelo usuário
            available_articles: Artigos disponíveis para recomendação
            
        Returns:
            Lista de artigos recomendados com pontuação
        """
        if not available_articles:
            return []
        
        recommendations = []
        
        # Score baseado em preferências
        preference_keywords = [pref.lower() for pref in user_preferences]
        
        # Palavras dos artigos recentes (para diversificar)
        recent_keywords = set()
        for article in recent_articles[-5:]:  # Últimos 5 artigos
            if 'title' in article:
                recent_keywords.update(article['title'].lower().split())
            if 'content' in article and article['content']:
                recent_keywords.update(article['content'][:200].lower().split())
        
        for article in available_articles:
            score = 0
            title = article.get('title', '').lower()
            content = article.get('description', '').lower()
            category = article.get('category', '').lower()
            
            # Score por preferências (peso 40%)
            for pref in preference_keywords:
                if pref in title:
                    score += 3
                elif pref in content:
                    score += 2
                elif pref in category:
                    score += 1
            
            # Score por categoria (peso 30%)
            if category in preference_keywords:
                score += 5
            
            # Penaliza artigos similares aos recentes (diversificação)
            similarity_penalty = 0
            title_words = set(title.split())
            overlap = len(title_words.intersection(recent_keywords))
            if overlap > 2:
                similarity_penalty = overlap * 0.5
            
            score = max(0, score - similarity_penalty)
            
            # Score por recência (peso 20%)
            published = article.get('published_at')
            if published:
                try:
                    pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    days_old = (datetime.now() - pub_date.replace(tzinfo=None)).days
                    if days_old <= 1:
                        score += 2
                    elif days_old <= 3:
                        score += 1
                except:
                    pass
            
            # Score por engajamento (peso 10%)
            if article.get('view_count', 0) > 1000:
                score += 1
            
            if score > 0:
                recommendations.append({
                    **article,
                    'recommendation_score': round(score, 2),
                    'recommendation_reasons': self._get_recommendation_reasons(
                        article, user_preferences, score
                    )
                })
        
        # Ordena por score e retorna top 10
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return recommendations[:10]
    
    def _get_recommendation_reasons(self, article: Dict, preferences: List[str], score: float) -> List[str]:
        """Gera razões para a recomendação"""
        reasons = []
        title = article.get('title', '').lower()
        content = article.get('description', '').lower()
        category = article.get('category', '').lower()
        
        for pref in preferences:
            pref_lower = pref.lower()
            if pref_lower in title:
                reasons.append(f"Relacionado ao seu interesse em {pref}")
                break
            elif pref_lower in content:
                reasons.append(f"Contém informações sobre {pref}")
                break
            elif pref_lower in category:
                reasons.append(f"Da categoria {pref} que você segue")
                break
        
        if score > 5:
            reasons.append("Alta relevância para seu perfil")
        elif score > 3:
            reasons.append("Boa correspondência com suas preferências")
        
        # Recência
        published = article.get('published_at')
        if published:
            try:
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                days_old = (datetime.now() - pub_date.replace(tzinfo=None)).days
                if days_old <= 1:
                    reasons.append("Artigo recente")
            except:
                pass
        
        return reasons[:3]  # Máximo 3 razões
    
    def analyze_reading_patterns(self, user_id: int, reading_history: List[Dict]) -> Dict:
        """
        Analisa padrões de leitura do usuário
        
        Args:
            user_id: ID do usuário
            reading_history: Histórico de leitura
            
        Returns:
            Análise dos padrões de leitura
        """
        if not reading_history:
            return {"message": "Dados insuficientes para análise"}
        
        # Análise por categorias
        categories = {}
        reading_times = []
        sources = {}
        
        for item in reading_history:
            # Categorias
            cat = item.get('category', 'Geral')
            categories[cat] = categories.get(cat, 0) + 1
            
            # Tempos de leitura (se disponível)
            read_time = item.get('reading_time_minutes')
            if read_time:
                reading_times.append(read_time)
            
            # Fontes
            source = item.get('source', 'Desconhecida')
            sources[source] = sources.get(source, 0) + 1
        
        # Categoria favorita
        favorite_category = max(categories.items(), key=lambda x: x[1]) if categories else None
        
        # Tempo médio de leitura
        avg_reading_time = sum(reading_times) / len(reading_times) if reading_times else None
        
        # Fonte favorita
        favorite_source = max(sources.items(), key=lambda x: x[1]) if sources else None
        
        analysis = {
            "total_articles_read": len(reading_history),
            "favorite_category": favorite_category[0] if favorite_category else None,
            "category_distribution": categories,
            "average_reading_time": round(avg_reading_time, 1) if avg_reading_time else None,
            "favorite_source": favorite_source[0] if favorite_source else None,
            "reading_frequency": self._calculate_reading_frequency(reading_history),
            "engagement_level": self._calculate_engagement_level(reading_history),
            "recommendations": self._generate_pattern_based_recommendations(categories, sources)
        }
        
        return analysis
    
    def _calculate_reading_frequency(self, history: List[Dict]) -> str:
        """Calcula frequência de leitura"""
        if len(history) < 7:
            return "Baixa"
        elif len(history) < 20:
            return "Moderada"
        else:
            return "Alta"
    
    def _calculate_engagement_level(self, history: List[Dict]) -> str:
        """Calcula nível de engajamento"""
        if not history:
            return "Baixo"
        
        # Considera artigos favoritados, compartilhados, comentados
        engagement_actions = 0
        for item in history:
            if item.get('is_favorite'):
                engagement_actions += 1
            if item.get('shared'):
                engagement_actions += 1
            if item.get('has_comments'):
                engagement_actions += 1
        
        engagement_rate = engagement_actions / len(history)
        
        if engagement_rate > 0.3:
            return "Alto"
        elif engagement_rate > 0.1:
            return "Moderado"
        else:
            return "Baixo"
    
    def _generate_pattern_based_recommendations(self, categories: Dict, sources: Dict) -> List[str]:
        """Gera recomendações baseadas nos padrões"""
        recommendations = []
        
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])[0]
            recommendations.append(f"Explore mais artigos da categoria {top_category}")
        
        if len(categories) == 1:
            recommendations.append("Tente diversificar suas leituras explorando novas categorias")
        
        if sources:
            top_source = max(sources.items(), key=lambda x: x[1])[0]
            if sources[top_source] / sum(sources.values()) > 0.8:
                recommendations.append("Considere diversificar suas fontes de notícias")
        
        return recommendations

# Instância global do serviço
ai_service = AIService()

# Funções de conveniência
def summarize_article(text: str, title: str = "", max_length: int = 150) -> Tuple[str, str]:
    """Função de conveniência para gerar resumo"""
    return ai_service.generate_summary(text, title, max_length)

def get_recommendations(user_id: int, preferences: List[str], 
                       recent_articles: List[Dict], 
                       available_articles: List[Dict]) -> List[Dict]:
    """Função de conveniência para obter recomendações"""
    return ai_service.generate_recommendations(preferences, recent_articles, available_articles)

def analyze_user_patterns(user_id: int, reading_history: List[Dict]) -> Dict:
    """Função de conveniência para análise de padrões"""
    return ai_service.analyze_reading_patterns(user_id, reading_history)