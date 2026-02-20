import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';

import Home from './screens/home';
import Clientes from './screens/Clientes';
import Movimentacoes from './screens/Movimentacoes';
import Monitoramento from './screens/Monitoramento';
import Normalizacao from './screens/Normalizacao';
import Configuracao from './screens/Configuracao';
import CargaCoTit from './screens/Cargacotit';
import Login from './screens/Login';

import { ConfigProvider, useConfig } from './context/ConfigContext';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// ===== ESTILOS =====
const navStyle = { 
  background: '#20232a', 
  padding: '15px', 
  display: 'flex', 
  gap: '20px', 
  justifyContent: 'center', 
  borderRadius: '8px', 
  marginBottom: '20px',
  flexWrap: 'wrap',
  alignItems: 'center'
};

const linkNav = { 
  color: 'white', 
  textDecoration: 'none', 
  fontSize: '14px', 
  fontWeight: 'bold',
  cursor: 'pointer'
};

const statusIndicator = (status) => ({
  display: 'inline-block',
  width: '12px',
  height: '12px',
  borderRadius: '50%',
  backgroundColor: status === 'conectado' ? '#10b981' : '#ef4444',
  marginRight: '5px'
});

const btnLogout = { 
  background: '#ff4d4d', 
  color: 'white', 
  border: 'none', 
  padding: '5px 12px', 
  borderRadius: '4px', 
  cursor: 'pointer',
  fontSize: '12px'
};

// ===== COMPONENTE NAVBAR COM STATUS =====
function NavBar() {
  const navigate = useNavigate();
  const { config, status } = useConfig();

  const handleLogout = async () => {
    const token = localStorage.getItem('auth_token');
    
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (e) {
      console.error('Erro ao fazer logout:', e);
    }

    // Limpar localStorage e redirecionar para login
    localStorage.clear();
    sessionStorage.clear();
    navigate('/login');
    window.location.reload();
  };

  return (
    <nav style={navStyle}>
      <Link to="/" style={linkNav}>🏠 Início</Link>
      <Link to="/configuracao" style={linkNav}>⚙️ Config</Link>
      <Link to="/clientes" style={linkNav}>👥 Clientes</Link>
      <Link to="/Cargacotit" style={linkNav}>👶 Dependentes</Link>
      <Link to="/movimentacoes" style={linkNav}>💰 Movimentações</Link>
      <Link to="/normalizacao" style={linkNav}>🛡️ Normalização</Link>
      <Link to="/monitoramento" style={linkNav}>📊 Monitoramento</Link>

      <div style={{ marginLeft: 'auto', display: 'flex', gap: '15px', alignItems: 'center' }}>
        <div style={{ fontSize: '12px', color: '#aaa', display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={statusIndicator(status)}></span>
          {status === 'conectado' ? (
            <span>✓ {config?.usuario}@{config?.servidor?.split('\\')[0]}</span>
          ) : (
            <span>✗ Sem conexão</span>
          )}
        </div>
        <button onClick={handleLogout} style={btnLogout}>
          Sair
        </button>
      </div>
    </nav>
  );
}

// ===== COMPONENTE PRINCIPAL COM ROTAS =====
function AppContent() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Verificar se tem token válido ao iniciar
    const token = localStorage.getItem('auth_token');
    if (token) {
      validateToken(token);
    } else {
      setLoading(false);
      navigate('/login');
    }
  }, [navigate]);

  const validateToken = async (token) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/validate-token`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();

      if (data.valid) {
        setIsLoggedIn(true);
      } else {
        localStorage.removeItem('auth_token');
        navigate('/login');
      }
    } catch (e) {
      console.error('Erro ao validar token:', e);
      localStorage.removeItem('auth_token');
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (user) => {
    setIsLoggedIn(true);
    navigate('/');
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <h2>⌛ Carregando...</h2>
      </div>
    );
  }

  if (!isLoggedIn) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={{ padding: '20px' }}>
      <NavBar />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/configuracao" element={<Configuracao />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/Cargacotit" element={<CargaCoTit />} />
        <Route path="/movimentacoes" element={<Movimentacoes />} />
        <Route path="/normalizacao" element={<Normalizacao />} />
        <Route path="/monitoramento" element={<Monitoramento />} />
        <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />
      </Routes>
    </div>
  );
}

// ===== APP WRAPPER COM CONTEXT E ROUTER =====
export default function App() {
  return (
    <Router>
      <ConfigProvider>
        <AppContent />
      </ConfigProvider>
    </Router>
  );
}
