from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from backend.auth import AuthManager, login_required
from backend.register import RegisterManager
import os

# Inicializar a aplicação
app = Flask(__name__, template_folder="frontend/templates", static_folder="static")

# Configuração da chave secreta para sessões (em produção use uma chave mais segura)
app.secret_key = os.environ.get('SECRET_KEY', 'neural_news_dev_key_2024_change_in_production')

# Instâncias dos gerenciadores
auth_manager = AuthManager()
register_manager = RegisterManager()

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

@app.route('/artigo', methods=['GET'])
@login_required
def article():
    user_info = getattr(request, 'current_user', None)
    return render_template('panel/article.html', user=user_info)

@app.route('/favoritos', methods=['GET'])
@login_required
def favourites():
    user_info = getattr(request, 'current_user', None)
    return render_template('panel/faovurites.html', user=user_info)
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


# ============= MAIN =============
if __name__ == '__main__':
    app.run(debug=True, port=5000)