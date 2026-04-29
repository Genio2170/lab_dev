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

    // Simulação de login
    function doLogin() {
      const email = document.getElementById('loginEmail').value.trim();
      const pass  = document.getElementById('loginPass').value;
      const rememberMe = document.querySelector('input[type="checkbox"]').checked;
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

      // Enviar requisição AJAX para o servidor
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
            window.location.href = data.redirect || '/artigos';
          }, 1000);
        } else {
          showAlert('⚠ ' + data.message, 'error');
          resetButton();
        }
      })
      .catch(error => {
        console.error('Erro na requisição:', error);
        showAlert('⚠ Erro de conexão. Tente novamente.', 'error');
        resetButton();
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
      const terms = document.getElementById('termsCheck').checked;
      if (!terms) {
        alert('Por favor aceite os termos para continuar.');
        return;
      }
      const successAlert = document.getElementById('registerAlert');
      successAlert.style.display = 'flex';
      setTimeout(() => { window.location.href = 'index.html'; }, 2000);
    }

    // Força da senha
    function checkStrength(val) {
      const bars  = [document.getElementById('bar1'), document.getElementById('bar2'),
                     document.getElementById('bar3'), document.getElementById('bar4')];
      const label = document.getElementById('psLabel');
      let score   = 0;

      if (val.length >= 8)             score++;
      if (/[A-Z]/.test(val))           score++;
      if (/[0-9]/.test(val))           score++;
      if (/[^A-Za-z0-9]/.test(val))   score++;

      const levels = ['', 'weak', 'medium', 'strong', 'strong'];
      const labels = ['', 'Fraca', 'Média', 'Forte', 'Muito forte'];
      const colors = ['', '#ff3b57', '#ffc107', '#00d68f', '#00d68f'];

      bars.forEach((b, i) => {
        b.className = 'ps-bar';
        if (i < score) b.classList.add(levels[score]);
      });

      label.textContent = val.length > 0 ? labels[score] : '';
      label.style.color = colors[score];
    }

    // Enter para login
    document.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        const isLogin = document.getElementById('formLogin').style.display !== 'none';
        if (isLogin) doLogin();
      }
    });