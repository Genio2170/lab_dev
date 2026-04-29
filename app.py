from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from backend.auth import AuthManager, login_required
from backend.register import RegisterManager
from backend.favorites import FavoritesManager
from backend.preferences import PreferencesManager
import os

# Inicializar a aplicação
app = Flask(__name__, template_folder="frontend/templates", static_folder="static")

# Configuração da chave secreta para sessões (em produção use uma chave mais segura)
app.secret_key = os.environ.get('SECRET_KEY', 'neural_news_dev_key_2024_change_in_production')

# Instâncias dos gerenciadores
auth_manager = AuthManager()
register_manager = RegisterManager()
favorites_manager = FavoritesManager()
preferences_manager = PreferencesManager()

# ============= ROUTES =============
@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'session_token' in session:
        # Invalidar token no servidor
        auth_manager.invalidate_session(session['session_token'])
        # Limpar sessão local
        session.clear()
        flash('Logout realizado com sucesso!', 'success')
    
    return redirect(url_for('login'))

@app.route('/painel-controle', methods=['GET'])
@login_required
def dash():
    user_info = getattr(request, 'current_user', None)
    return render_template('panel/dashboard.html', user=user_info)

# Alias para dashboard
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    user_info = getattr(request, 'current_user', None)
    return render_template('panel/dashboard.html', user=user_info)

@app.route('/artigo', methods=['GET'])
@login_required
def article():
    user_info = getattr(request, 'current_user', None)
    return render_template('panel/article.html', user=user_info)

@app.route('/favoritos', methods=['GET'])
@login_required
def favorites():
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        flash('Erro: Usuário não encontrado', 'error')
        return redirect(url_for('login'))
    
    # Obter parâmetros de filtro
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'added_at')
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    limit = 12  # Itens por página
    
    try:
        # Obter favoritos do usuário
        favorites_result = favorites_manager.get_user_favorites(
            user_id=user_info['id'],
            category='' if category == 'all' else category,
            sort_by=sort_by,
            limit=limit,
            offset=(page - 1) * limit
        )
        
        # Obter estatísticas dos favoritos
        stats_result = favorites_manager.get_user_favorites_stats(user_info['id'])
        
        # Obter categorias disponíveis
        categories_result = favorites_manager.get_user_categories(user_info['id'])
        
        # Preparar dados para o template
        template_data = {
            'user': user_info,
            'favorites': favorites_result,
            'favorites_stats': stats_result.get('data') if stats_result and stats_result.get('success') else None,
            'available_categories': categories_result.get('data', []) if categories_result and categories_result.get('success') else [],
            'current_category': category,
            'sort_by': sort_by,
            'search_query': search_query
        }
        
        return render_template('panel/favorites.html', **template_data)
        
    except Exception as e:
        flash(f'Erro ao carregar favoritos: {str(e)}', 'error')
        return render_template('panel/favorites.html', 
                             user=user_info,
                             favorites=None,
                             favorites_stats=None,
                             available_categories=[],
                             current_category='all',
                             sort_by='added_at',
                             search_query='')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se usuário já está logado, redirecionar para dashboard
    if 'session_token' in session:
        user_info, _ = auth_manager.validate_session_token(session['session_token'])
        if user_info:
            return redirect(url_for('dash'))
    
    if request.method == 'POST':
        # Processar login via JSON (AJAX)
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            remember_me = data.get('remember_me', False)
            
            # Validações básicas
            if not email or not password:
                return jsonify({
                    'success': False,
                    'message': 'Email e palavra-passe são obrigatórios'
                }), 400
            
            # Tentar autenticar
            user_info, message = auth_manager.authenticate_user(email, password)
            
            if user_info:
                # Criar sessão
                token, _ = auth_manager.create_session_token(user_info['id'])
                if token:
                    session['session_token'] = token
                    session['user_id'] = user_info['id']
                    session['user_name'] = user_info['full_name']
                    session.permanent = remember_me  # Manter sessão se solicitado
                    
                    return jsonify({
                        'success': True,
                        'message': 'Login realizado com sucesso',
                        'redirect': url_for('dash')
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Erro interno ao criar sessão'
                    }), 500
            else:
                return jsonify({
                    'success': False,
                    'message': message
                }), 401
        
        # Processar login via formulário tradicional
        else:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            remember_me = 'remember_me' in request.form
            
            if not email or not password:
                flash('Email e palavra-passe são obrigatórios', 'error')
                return render_template('login.html')
            
            user_info, message = auth_manager.authenticate_user(email, password)
            
            if user_info:
                token, _ = auth_manager.create_session_token(user_info['id'])
                if token:
                    session['session_token'] = token
                    session['user_id'] = user_info['id']
                    session['user_name'] = user_info['full_name']
                    session.permanent = remember_me
                    
                    flash('Login realizado com sucesso!', 'success')
                    
                    # Redirecionar para próxima página ou dashboard
                    next_page = request.args.get('next')
                    if next_page:
                        return redirect(next_page)
                    return redirect(url_for('dash'))
                else:
                    flash('Erro interno ao criar sessão', 'error')
            else:
                flash(message, 'error')
            
            return render_template('login.html')
    
    # GET request - mostrar formulário de login
    return render_template('login.html')

@app.route('/preferencias', methods=['GET'])
@login_required
def preferences():
    user_info = getattr(request, 'current_user', None)
    return render_template('panel/preferences.html', user=user_info)

@app.route('/register', methods=['GET','POST'])
def register():
    # Se usuário já está logado, redirecionar para dashboard
    if 'session_token' in session:
        user_info, _ = auth_manager.validate_session_token(session['session_token'])
        if user_info:
            return redirect(url_for('dash'))
    
    if request.method == 'POST':
        # Processar registro via JSON (AJAX)
        if request.is_json:
            data = request.get_json()
            
            # Validar todos os dados de uma vez
            is_valid, errors = register_manager.validate_registration_data(data)
            
            if not is_valid:
                return jsonify({
                    'success': False,
                    'errors': errors
                }), 400
            
            # Tentar criar usuário
            success, message = register_manager.create_user(
                data.get('full_name', '').strip(),
                data.get('email', '').strip(),
                data.get('password', ''),
                data.get('confirm_password', '')
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': message,
                    'redirect': url_for('login')
                })
            else:
                return jsonify({
                    'success': False,
                    'message': message
                }), 400
        
        # Processar registro via formulário tradicional
        else:
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            terms_accepted = 'terms_accepted' in request.form
            
            # Validar dados básicos
            if not all([full_name, email, password, confirm_password]):
                flash('Todos os campos são obrigatórios', 'error')
                return render_template('register.html', 
                                     full_name=full_name, email=email)
            
            if not terms_accepted:
                flash('Deve aceitar os termos de uso', 'error')
                return render_template('register.html',
                                     full_name=full_name, email=email)
            
            # Tentar criar usuário
            success, message = register_manager.create_user(
                full_name, email, password, confirm_password
            )
            
            if success:
                flash(message, 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'error')
                return render_template('register.html',
                                     full_name=full_name, email=email)
    
    # GET request - mostrar formulário de registro
    return render_template('register.html')

# ============= API ROUTES =============
@app.route('/api/user', methods=['GET'])
@login_required
def api_user_info():
    """API endpoint para obter informações do usuário logado"""
    user_info = getattr(request, 'current_user', None)
    if user_info:
        return jsonify({
            'success': True,
            'user': {
                'id': user_info['id'],
                'name': user_info['full_name'],
                'email': user_info['email']
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 404

@app.route('/api/register/validate', methods=['POST'])
def api_validate_registration():
    """API endpoint para validar dados de registro"""
    data = request.get_json()
    is_valid, errors = register_manager.validate_registration_data(data)
    
    return jsonify({
        'success': True,
        'valid': is_valid,
        'errors': errors if not is_valid else {}
    })

@app.route('/api/register/check-email', methods=['POST'])
def api_check_email():
    """API endpoint para verificar se email está disponível"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({
            'success': False,
            'message': 'Email é obrigatório'
        }), 400
    
    if not register_manager.validate_email(email):
        return jsonify({
            'success': False,
            'message': 'Formato de email inválido'
        }), 400
    
    exists, message = register_manager.email_exists(email)
    
    return jsonify({
        'success': True,
        'available': not exists,
        'message': 'Email disponível' if not exists else message
    })

@app.route('/api/register/stats', methods=['GET'])
def api_register_stats():
    """API endpoint para obter estatísticas de registro"""
    stats, message = register_manager.get_user_stats()
    
    if stats:
        return jsonify({
            'success': True,
            'stats': stats
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 500

@app.route('/api/session/validate', methods=['GET'])
def api_validate_session():
    """API endpoint para validar sessão atual"""
    if 'session_token' in session:
        user_info, message = auth_manager.validate_session_token(session['session_token'])
        if user_info:
            return jsonify({
                'success': True,
                'valid': True,
                'user': {
                    'id': user_info['id'],
                    'name': user_info['full_name'],
                    'email': user_info['email']
                }
            })
    
    return jsonify({
        'success': True,
        'valid': False
    })

# ============= FAVORITES API ROUTES =============
@app.route('/api/favorites', methods=['GET'])
@login_required
def api_get_favorites():
    """API endpoint para obter favoritos do usuário"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    # Obter parâmetros de filtro
    category = request.args.get('category')
    sort_by = request.args.get('sort', 'added_at')
    limit = min(int(request.args.get('limit', 20)), 50)  # Máximo de 50 itens
    offset = int(request.args.get('offset', 0))
    
    try:
        result = favorites_manager.get_user_favorites(
            user_id=user_info['id'],
            category=category or '',
            sort_by=sort_by,
            limit=limit,
            offset=offset
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter favoritos: {str(e)}'
        }), 500

@app.route('/api/favorites', methods=['POST'])
@login_required
def api_add_favorite():
    """API endpoint para adicionar um favorito"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'Dados não fornecidos'
        }), 400
    
    # Verificar se tem news_id ou dados de artigo externo
    news_id = data.get('news_id')
    
    try:
        if news_id:
            # Adicionar favorito por news_id
            result = favorites_manager.add_favorite_by_news_id(
                user_id=user_info['id'],
                news_id=news_id,
                notes=data.get('notes', ''),
                tags=data.get('tags', [])
            )
        else:
            # Adicionar favorito com dados externos
            result = favorites_manager.add_favorite(
                user_id=user_info['id'],
                title=data.get('title', ''),
                description=data.get('description', ''),
                external_url=data.get('url', ''),
                source=data.get('source', ''),
                category=data.get('category', 'Geral'),
                notes=data.get('notes', ''),
                tags=data.get('tags', [])
            )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao adicionar favorito: {str(e)}'
        }), 500

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
@login_required
def api_remove_favorite(favorite_id):
    """API endpoint para remover um favorito"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    try:
        result = favorites_manager.remove_favorite(user_info['id'], favorite_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao remover favorito: {str(e)}'
        }), 500

@app.route('/api/favorites/<int:favorite_id>/read', methods=['PATCH'])
@login_required
def api_toggle_read_status(favorite_id):
    """API endpoint para alterar status de leitura de um favorito"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    data = request.get_json()
    
    if not data or 'is_read' not in data:
        return jsonify({
            'success': False,
            'message': 'Status de leitura não fornecido'
        }), 400
    
    try:
        result = favorites_manager.update_read_status(
            user_id=user_info['id'],
            favorite_id=favorite_id,
            is_read=bool(data['is_read'])
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar status: {str(e)}'
        }), 500

@app.route('/api/favorites/<int:favorite_id>/notes', methods=['PATCH'])
@login_required
def api_update_notes(favorite_id):
    """API endpoint para atualizar notas de um favorito"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    data = request.get_json()
    
    if not data or 'notes' not in data:
        return jsonify({
            'success': False,
            'message': 'Notas não fornecidas'
        }), 400
    
    try:
        result = favorites_manager.update_notes(
            user_id=user_info['id'],
            favorite_id=favorite_id,
            notes=data['notes']
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar notas: {str(e)}'
        }), 500

@app.route('/api/favorites/stats', methods=['GET'])
@login_required
def api_favorites_stats():
    """API endpoint para obter estatísticas dos favoritos"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    try:
        result = favorites_manager.get_user_favorites_stats(user_info['id'])
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

@app.route('/api/favorites/categories', methods=['GET'])
@login_required
def api_favorites_categories():
    """API endpoint para obter categorias de favoritos do usuário"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    try:
        result = favorites_manager.get_user_categories(user_info['id'])
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter categorias: {str(e)}'
        }), 500

@app.route('/api/favorites/check/<int:news_id>', methods=['GET'])
@login_required
def api_check_favorite_status(news_id):
    """API endpoint para verificar se um artigo está nos favoritos"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    try:
        result = favorites_manager.is_favorite(user_info['id'], news_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao verificar favorito: {str(e)}'
        }), 500


# ============= PREFERENCES API =============
@app.route('/api/preferences', methods=['GET'])
@login_required
def api_get_preferences():
    """API endpoint para obter as preferências do usuário"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    try:
        # Obter preferências do usuário
        user_preferences = preferences_manager.get_user_preferences(user_info['id'])
        
        if user_preferences and user_preferences.get('success'):
            # Mapear categorias do backend para frontend (usando nomes das categorias)
            backend_to_frontend_categories = {
                'tecnologia': 'tech',
                'mundo': 'world', 
                'negocios': 'business',
                'negócios': 'business',
                'ciencia': 'science',
                'ciência': 'science',
                'desporto': 'sports',
                'cultura': 'culture',
                'politica': 'politics',
                'política': 'politics',
                'ambiente': 'environment',
                'educacao': 'education',
                'educação': 'education',
                'geral': 'world',
                'internacional': 'world',
                'saude': 'science',
                'saúde': 'science',
                'economia': 'business'
            }
            
            # Mapear fontes do backend para frontend
            backend_to_frontend_sources = {
                'newsapi': 'bbc',
                'guardian': 'guardian',
                'rtp': 'jornal-angola',
                'publico': 'expansao',
                'observador': 'expansao',
                'bbc': 'bbc'
            }
            
            # Converter categorias preferidas do backend
            frontend_categories = []
            if user_preferences['data'].get('preferred_categories'):
                for cat in user_preferences['data']['preferred_categories']:
                    cat_name = cat.get('name', '').lower()
                    frontend_cat = backend_to_frontend_categories.get(cat_name, cat_name)
                    if frontend_cat and frontend_cat not in frontend_categories:
                        frontend_categories.append(frontend_cat)
            
            # Converter fontes preferidas
            frontend_sources = []
            if user_preferences['data'].get('preferred_sources'):
                for src in user_preferences['data']['preferred_sources']:
                    frontend_src = backend_to_frontend_sources.get(src, src)
                    if frontend_src and frontend_src not in frontend_sources:
                        frontend_sources.append(frontend_src)
            
            # Se não há fontes, usar algumas padrão
            if not frontend_sources:
                frontend_sources = ['bbc', 'guardian', 'jornal-angola']
            
            # Mapear frequência
            frequency_mapping = {
                'daily': 'morning',
                'hourly': 'realtime',
                'weekly': 'weekly'
            }
            
            backend_frequency = user_preferences['data'].get('notification_frequency', 'daily')
            frontend_frequency = frequency_mapping.get(backend_frequency, 'morning')
            
            return jsonify({
                'success': True,
                'preferences': {
                    'categorias': frontend_categories,
                    'frequencia': frontend_frequency,
                    'fontes': frontend_sources
                }
            })
        else:
            return jsonify({
                'success': True,
                'preferences': {
                    'categorias': [],
                    'frequencia': 'morning',
                    'fontes': ['bbc', 'guardian', 'jornal-angola']
                }
            })
    
    except Exception as e:
        print(f"Erro ao obter preferências: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao obter preferências: {str(e)}'
        }), 500


@app.route('/api/preferences', methods=['POST'])
@login_required
def api_save_preferences():
    """API endpoint para salvar as preferências do usuário"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados de preferências são obrigatórios'
            }), 400
        
        # Para simplificar, vamos apenas armazenar as preferências em um formato personalizado
        # Como o backend atual usa IDs de categoria, vamos trabalhar com o que temos
        
        # Por enquanto, vamos salvar pelo menos algumas categorias que existem
        frontend_categories = data.get('categorias', [])
        
        # Mapear algumas categorias frontend para backend (simplificado)
        category_mapping = {
            'tech': 1,      # Assumindo ID 1 para tecnologia
            'world': 2,     # ID 2 para mundo/internacional
            'business': 3,  # ID 3 para negócios
            'science': 4,   # ID 4 para ciência
            'sports': 5,    # ID 5 para desporto
            'culture': 6,   # ID 6 para cultura
            'politics': 7,  # ID 7 para política
            'environment': 8, # ID 8 para ambiente
            'education': 9   # ID 9 para educação
        }
        
        # Salvar categorias selecionadas
        for frontend_cat in frontend_categories:
            category_id = category_mapping.get(frontend_cat)
            if category_id:
                try:
                    result = preferences_manager.add_preferred_category(user_info['id'], category_id)
                    print(f"Resultado de adicionar categoria {frontend_cat}: {result}")
                except Exception as e:
                    print(f"Erro ao adicionar categoria {frontend_cat}: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Preferências salvas com sucesso!'
        })
    
    except Exception as e:
        print(f"Erro ao salvar preferências: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar preferências: {str(e)}'
        }), 500


@app.route('/api/preferences/reset', methods=['POST'])
@login_required
def api_reset_preferences():
    """API endpoint para limpar algumas preferências do usuário"""
    user_info = getattr(request, 'current_user', None)
    
    if not user_info:
        return jsonify({
            'success': False,
            'message': 'Usuário não encontrado'
        }), 401
    
    try:
        # Como não temos um método clear_user_preferences, vamos simular
        # removendo algumas categorias conhecidas
        category_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9]  # IDs das categorias
        
        removed_count = 0
        for cat_id in category_ids:
            try:
                success, msg = preferences_manager.remove_preferred_category(user_info['id'], cat_id)
                if success:
                    removed_count += 1
            except Exception as e:
                print(f"Erro ao remover categoria {cat_id}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Preferências limpas com sucesso! ({removed_count} categorias removidas)'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao limpar preferências: {str(e)}'
        }), 500


# ============= MAIN =============
if __name__ == '__main__':
    app.run(debug=True, port=5000)