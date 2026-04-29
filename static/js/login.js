    // Troca de tab
    function switchTab(tab) {
      const isLogin = tab === 'login';
      document.getElementById('formLogin').style.display    = isLogin ? 'block' : 'none';
      document.getElementById('formRegister').style.display = isLogin ? 'none'  : 'block';
      document.getElementById('tabLogin').classList.toggle('active', isLogin);
      document.getElementById('tabRegister').classList.toggle('active', !isLogin);
    }

    // Toggle visibilidade da senha
    function togglePass(id, btn) {
      const input = document.getElementById(id);
      const show  = input.type === 'password';
      input.type  = show ? 'text' : 'password';
      btn.textContent = show ? '🙈' : '👁';
    }

    // Login com suporte a AJAX e formulário tradicional
    function doLogin() {
      const email = document.getElementById('loginEmail').value.trim();
      const pass  = document.getElementById('loginPass').value;
      const rememberMe = document.querySelector('input[name="remember_me"]').checked;
      const btn   = document.getElementById('loginBtn');
      const alert = document.getElementById('loginAlert');

      alert.style.display = 'none';

      if (!email || !pass) {
        showAlert('⚠ Por favor preencha todos os campos.', 'error');
        return;
      }

      // Validar formato de email básico
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        showAlert('⚠ Por favor insira um email válido.', 'error');
        return;
      }

      btn.textContent = 'A entrar...';
      btn.classList.add('loading');
      btn.disabled = true;

      // Tentar login via AJAX primeiro
      fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          email: email,
          password: pass,
          remember_me: rememberMe
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showAlert('✓ ' + data.message, 'success');
          setTimeout(() => {
            window.location.href = data.redirect || '/painel-controle';
          }, 1000);
        } else {
          showAlert('⚠ ' + data.message, 'error');
          resetButton();
        }
      })
      .catch(error => {
        console.error('Erro AJAX, tentando submissão tradicional:', error);
        // Se AJAX falhar, usar submissão tradicional
        resetButton();
        document.getElementById('formLogin').submit();
      });
    }

    // Função auxiliar para mostrar alertas
    function showAlert(message, type) {
      const alert = document.getElementById('loginAlert');
      alert.textContent = message;
      alert.className = `alert ${type}`;
      alert.style.display = 'flex';
    }

    // Função auxiliar para resetar o botão
    function resetButton() {
      const btn = document.getElementById('loginBtn');
      btn.textContent = 'Entrar na minha conta →';
      btn.classList.remove('loading');
      btn.disabled = false;
    }

    // Simulação de registo
    function doRegister() {
      const fullName = document.querySelector('input[name="full_name"]').value.trim();
      const email = document.querySelector('input[name="email"]').value.trim();
      const password = document.querySelector('input[name="password"]').value;
      const confirmPassword = document.querySelector('input[name="confirm_password"]').value;
      const termsAccepted = document.querySelector('input[name="terms_accepted"]').checked;
      const btn = document.querySelector('.btn-primary');
      const alert = document.getElementById('registerAlert');

      alert.style.display = 'none';

      // Validações básicas
      if (!fullName || !email || !password || !confirmPassword) {
        showRegisterAlert('⚠ Por favor preencha todos os campos.', 'error');
        return;
      }

      if (!termsAccepted) {
        showRegisterAlert('⚠ Deve aceitar os termos para continuar.', 'error');
        return;
      }

      if (password !== confirmPassword) {
        showRegisterAlert('⚠ As palavras-passe não coincidem.', 'error');
        return;
      }

      btn.textContent = 'A criar conta...';
      btn.classList.add('loading');
      btn.disabled = true;

      // Tentar registro via AJAX
      fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          full_name: fullName,
          email: email,
          password: password,
          confirm_password: confirmPassword,
          terms_accepted: termsAccepted
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showRegisterAlert('✓ ' + data.message, 'success');
          setTimeout(() => {
            window.location.href = data.redirect || '/login';
          }, 2000);
        } else {
          if (data.errors && Object.keys(data.errors).length > 0) {
            const firstError = Object.values(data.errors)[0];
            showRegisterAlert('⚠ ' + firstError, 'error');
          } else {
            showRegisterAlert('⚠ ' + data.message, 'error');
          }
          resetRegisterButton();
        }
      })
      .catch(error => {
        console.error('Erro AJAX, tentando submissão tradicional:', error);
        resetRegisterButton();
        document.getElementById('formRegister').submit();
      });
    }

    // Função auxiliar para alertas de registro
    function showRegisterAlert(message, type) {
      const alert = document.getElementById('registerAlert');
      if (alert) {
        alert.textContent = message;
        alert.className = `alert ${type}`;
        alert.style.display = 'flex';
      }
    }

    // Função auxiliar para resetar botão de registro
    function resetRegisterButton() {
      const btn = document.querySelector('.btn-primary');
      btn.textContent = 'Criar conta grátis →';
      btn.classList.remove('loading');
      btn.disabled = false;
    }

    // Força da senha (apenas para o campo principal)
    function checkStrength(val) {
      const bars  = [document.getElementById('bar1'), document.getElementById('bar2'),
                     document.getElementById('bar3'), document.getElementById('bar4')];
      const label = document.getElementById('psLabel');
      
      // Verificar se os elementos existem (estamos na página de registro)
      if (!bars[0] || !label) return;
      
      let score = 0;

      if (val.length >= 8)             score++;
      if (/[A-Z]/.test(val))           score++;
      if (/[0-9]/.test(val))           score++;
      if (/[^A-Za-z0-9]/.test(val))   score++;

      const levels = ['', 'weak', 'medium', 'strong', 'strong'];
      const labels = ['', 'Fraca', 'Média', 'Forte', 'Muito forte'];
      const colors = ['', '#ff3b57', '#ffc107', '#00d68f', '#00d68f'];

      bars.forEach((b, i) => {
        if (b) {
          b.className = 'ps-bar';
          if (i < score) b.classList.add(levels[score]);
        }
      });

      if (label) {
        label.textContent = val.length > 0 ? labels[score] : '';
        label.style.color = colors[score];
      }
    }

    // Enter para login/registro
    document.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const loginForm = document.getElementById('formLogin');
        const registerForm = document.getElementById('formRegister');
        
        if (loginForm && loginForm.style.display !== 'none') {
          e.preventDefault();
          doLogin();
        } else if (registerForm && registerForm.style.display !== 'none') {
          e.preventDefault();
          doRegister();
        }
      }
    });

    // Adicionar evento de submissão para formulário de registro
    document.addEventListener('DOMContentLoaded', function() {
      const registerForm = document.getElementById('formRegister');
      if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
          e.preventDefault();
          doRegister();
        });
      }
      
      const loginForm = document.getElementById('formLogin');
      if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
          e.preventDefault();
          doLogin();
        });
      }
    });