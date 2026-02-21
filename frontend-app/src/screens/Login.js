import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Login({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isRegister, setIsRegister] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (!formData.username || !formData.password) {
      setError('Usuário e senha são obrigatórios');
      setLoading(false);
      return;
    }

    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login';
      const apiUrl = `${API_BASE_URL}${endpoint}`;
      
      console.log(`🔄 Enviando ${isRegister ? 'registro' : 'login'} para:`, apiUrl);

      const payload = {
        username: formData.username,
        password: formData.password
      };
      
      if (isRegister) {
        payload.email = `${formData.username}@example.com`;
      }

      console.log('📋 Payload:', { ...payload, password: '***' });

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      console.log('📡 Response Status:', response.status, response.statusText);

      const data = await response.json();
      console.log('📦 Response Data:', { ...data, access_token: data.access_token?.substring(0, 20) + '...' });

      if (!response.ok) {
        const errorMsg = data.detail || data.message || 'Erro ao autenticar';
        console.error('❌ Erro do servidor:', errorMsg);
        setError(errorMsg);
        setLoading(false);
        return;
      }

      // Validar estrutura da resposta
      if (!data.access_token || !data.user || !data.user.id) {
        console.error('❌ Resposta inválida - campos faltando:', data);
        setError('Resposta inválida do servidor. Tente novamente.');
        setLoading(false);
        return;
      }

      // Salvar token e dados do usuário
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_id', data.user.id);
      localStorage.setItem('username', data.user.username);

      console.log(`✅ ${isRegister ? 'Registrado' : 'Login'} bem-sucedido:`, data.user.username);

      // Callback para notificar app
      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }

      // Redirecionar para tela de configuração
      navigate('/configuracao');
    } catch (err) {
      console.error('❌ Erro na autenticação:', err);
      console.error('📍 Stack:', err.stack);
      
      let errorMsg = 'Erro ao conectar com o servidor';
      if (err instanceof TypeError && err.message === 'Failed to fetch') {
        errorMsg = `Não consegui conectar ao servidor. Verifique se o backend está rodando em ${API_BASE_URL}`;
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h1 style={{ textAlign: 'center', color: '#1f2937', marginBottom: '30px' }}>
          {isRegister ? '📝 Criar Conta' : '🔐 Login'}
        </h1>

        <form onSubmit={handleSubmit}>
          <div style={fieldGroupStyle}>
            <label htmlFor="username">Usuário</label>
            <input
              id="username"
              type="text"
              name="username"
              placeholder="Digite seu usuário"
              value={formData.username}
              onChange={handleChange}
              disabled={loading}
              style={inputStyle}
              autoFocus
            />
          </div>

          <div style={fieldGroupStyle}>
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              name="password"
              placeholder="Digite sua senha"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
              style={inputStyle}
            />
          </div>

          {error && (
            <div style={errorStyle}>
              <strong>❌ Erro</strong>
              <p>{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={buttonStyle}
          >
            {loading ? '⌛ Processando...' : (isRegister ? '📝 Criar Conta' : '🔓 Entrar')}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
              setFormData({ username: '', password: '' });
            }}
            style={toggleStyle}
          >
            {isRegister ? 'Já tem conta? Faça login' : 'Novo? Crie uma conta'}
          </button>
        </div>
      </div>

      {/* Info Box */}
      <div style={infoBoxStyle}>
        <strong>ℹ️ Demo Credentials:</strong>
        <p style={{ margin: '8px 0 0 0', fontSize: '12px' }}>
          Usuário: <code>admin</code><br/>
          Senha: <code>admin123</code>
        </p>
      </div>
    </div>
  );
}

// ===== ESTILOS =====

const containerStyle = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '100vh',
  backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  padding: '20px',
  fontFamily: 'system-ui, -apple-system, sans-serif'
};

const cardStyle = {
  backgroundColor: 'white',
  padding: '40px',
  borderRadius: '12px',
  boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  width: '100%',
  maxWidth: '400px'
};

const fieldGroupStyle = {
  marginBottom: '20px'
};

const inputStyle = {
  width: '100%',
  padding: '12px',
  border: '2px solid #e5e7eb',
  borderRadius: '6px',
  fontSize: '14px',
  marginTop: '8px',
  boxSizing: 'border-box',
  transition: 'border-color 0.2s',
};

const buttonStyle = {
  width: '100%',
  padding: '12px',
  backgroundColor: '#667eea',
  color: 'white',
  border: 'none',
  borderRadius: '6px',
  fontSize: '16px',
  fontWeight: 'bold',
  cursor: 'pointer',
  transition: 'background-color 0.2s'
};

const toggleStyle = {
  background: 'none',
  border: 'none',
  color: '#667eea',
  cursor: 'pointer',
  fontSize: '14px',
  textDecoration: 'underline',
  padding: 0
};

const errorStyle = {
  backgroundColor: '#fef2f2',
  border: '1px solid #fca5a5',
  borderRadius: '6px',
  padding: '12px',
  marginBottom: '20px',
  color: '#7f1d1d',
  fontSize: '14px'
};

const infoBoxStyle = {
  marginTop: '30px',
  backgroundColor: 'rgba(255,255,255,0.2)',
  padding: '15px',
  borderRadius: '8px',
  color: 'white',
  fontSize: '13px',
  textAlign: 'center'
};
