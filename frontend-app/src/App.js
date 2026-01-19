import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

// CORREÇÃO 1: Nome do arquivo em minúsculo conforme o erro no disco
import Home from './screens/home'; 
import Clientes from './screens/Clientes'; 
import Movimentacoes from './screens/Movimentacoes'; 
import Monitoramento from './screens/Monitoramento';
import Normalizacao from './screens/Normalizacao';
import Configuracao from './screens/Configuracao';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';

// --- ESTILOS (Definidos antes de serem usados) ---
const navStyle = { background: '#20232a', padding: '15px', display: 'flex', gap: '20px', justifyContent: 'center', borderRadius: '8px', marginBottom: '20px' };
const linkNav = { color: 'white', textDecoration: 'none', fontSize: '14px', fontWeight: 'bold' };
const btnLogout = { background: '#ff4d4d', color: 'white', border: 'none', padding: '5px 12px', borderRadius: '4px', cursor: 'pointer' };
const authContainerStyle = { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#20232a' };
const authBoxStyle = { backgroundColor: 'white', padding: '40px', borderRadius: '10px', textAlign: 'center' };
const inputStyle = { width: '100%', padding: '10px', margin: '5px 0', borderRadius: '4px', border: '1px solid #ddd' };
const btnSubmitStyle = { ...inputStyle, backgroundColor: '#007bff', color: 'white', cursor: 'pointer', fontWeight: 'bold' };

// --- COMPONENTE DE LOGIN ---
const AuthSystem = ({ onLogin }) => {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');

  return (
    <div style={authContainerStyle}>
      <div style={authBoxStyle}>
        <h2 style={{color: '#333'}}>Gerador Ágil PLD</h2>
        <form onSubmit={(e) => { e.preventDefault(); onLogin(user, pass); }}>
          <input type="text" placeholder="Usuário" value={user} onChange={(e) => setUser(e.target.value)} style={inputStyle} required />
          <input type="password" placeholder="Senha" value={pass} onChange={(e) => setPass(e.target.value)} style={inputStyle} required />
          <button type="submit" style={btnSubmitStyle}>Entrar</button>
        </form>
      </div>
    </div>
  );
};

// --- COMPONENTE PRINCIPAL ---
function App() {
  const [autenticado, setAutenticado] = useState(false);
  const [userTipo, setUserTipo] = useState('VISUALIZADOR');

  useEffect(() => {
    if (localStorage.getItem('pld_autenticado') === 'true') {
      setAutenticado(true);
      setUserTipo(localStorage.getItem('pld_tipo') || 'VISUALIZADOR');
    }
  }, []);

  const handleLogin = async (usuario, senha) => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: usuario, password: senha })
      });
      const data = await response.json();
      if (response.ok) {
        setAutenticado(true); 
        setUserTipo(data.tipo);
        localStorage.setItem('pld_autenticado', 'true'); 
        localStorage.setItem('pld_tipo', data.tipo);
      } else {
        alert(data.message);
      }
    } catch { 
      alert("Erro ao conectar com API."); 
    }
  };

  if (!autenticado) {
    return <AuthSystem onLogin={handleLogin} />;
  }

  return (
    <Router>
      <div className="container" style={{padding: '20px'}}>
        <nav style={navStyle}>
          <Link to="/" style={linkNav}>🏠 Início</Link>
          <Link to="/clientes" style={linkNav}>👥 Clientes</Link>
          <Link to="/movimentacoes" style={linkNav}>💰 Movimentações</Link>
          <Link to="/normalizacao" style={linkNav}>🛡️ Normalização</Link>
          <Link to="/monitoramento" style={linkNav}>📊 Monitoramento</Link>
          <Link to="/configuracao" style={linkNav}>⚙️ Ambiente</Link>
          <button onClick={() => { localStorage.clear(); window.location.reload(); }} style={btnLogout}>Sair</button>
        </nav>

        <Routes>
          <Route path="/" element={<Home userTipo={userTipo} />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/movimentacoes" element={<Movimentacoes />} />
          <Route path="/monitoramento" element={<Monitoramento />} />
          <Route path="/normalizacao" element={<Normalizacao />} />
          <Route path="/configuracao" element={<Configuracao />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;