#!/usr/bin/env python3
"""
Script para setup do Frontend v2.0 com suporte a configuração dinâmica
Execute: python setup_frontend_v2.py
"""

import os
from pathlib import Path

def criar_arquivo(caminho, conteudo):
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✓ {caminho}")

print("=" * 70)
print("SETUP FRONTEND v2.0 - CONFIGURAÇÃO DINÂMICA")
print("=" * 70 + "\n")

# ===== 1. SERVIÇO DE API COM CONTEXTO =====
print("[1/6] Criando frontend-app/src/services/apiService.js...")

api_service_js = '''/**
 * API Service com gerenciamento de configuração
 * Centraliza todas as requisições HTTP
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class ApiService {
  constructor() {
    this.configKey = null;
    this.config = null;
  }

  /**
   * Valida e ativa configuração SQL Server
   * @param {Object} config - { servidor, banco, usuario, senha }
   * @returns {Promise}
   */
  async validarConfiguracao(config) {
    try {
      const response = await fetch(`${API_BASE_URL}/config/validar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });

      const data = await response.json();

      if (response.ok) {
        // Salvar na sessão
        this.configKey = data.config_key;
        this.config = config;
        sessionStorage.setItem('config_key', data.config_key);
        sessionStorage.setItem('pld_config', JSON.stringify(data.detalhes));

        console.log(`✓ Config ativada: ${this.configKey}`);
        return { sucesso: true, ...data };
      } else {
        console.error('✗ Erro na validação:', data);
        return { sucesso: false, erro: data.mensagem };
      }
    } catch (error) {
      console.error('✗ Erro ao validar:', error);
      return { sucesso: false, erro: error.message };
    }
  }

  /**
   * Apenas testa a conexão sem ativar
   * @param {Object} config
   */
  async testarConexao(config) {
    try {
      const response = await fetch(`${API_BASE_URL}/config/teste`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });

      const data = await response.json();
      return data;
    } catch (error) {
      return { status: 'erro', mensagem: error.message };
    }
  }

  /**
   * Obtém status da configuração ativa
   */
  async obterStatusConfig() {
    if (!this.configKey) {
      return { erro: 'Nenhuma configuração ativa' };
    }

    try {
      const response = await fetch(`${API_BASE_URL}/config/status/${this.configKey}`);
      const data = await response.json();
      return data;
    } catch (error) {
      return { erro: error.message };
    }
  }

  /**
   * Lista todas as configurações ativas
   */
  async listarConfiguracoes() {
    try {
      const response = await fetch(`${API_BASE_URL}/config/listar`);
      const data = await response.json();
      return data;
    } catch (error) {
      return { erro: error.message };
    }
  }

  /**
   * Fecha uma configuração
   */
  async fecharConfiguracao(configKey) {
    try {
      const response = await fetch(`${API_BASE_URL}/config/fechar/${configKey}`, {
        method: 'POST'
      });
      const data = await response.json();
      return data;
    } catch (error) {
      return { erro: error.message };
    }
  }

  /**
   * Requisição genérica GET com headers de autenticação
   */
  async get(endpoint) {
    const headers = this.obterHeaders();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
    return response.json();
  }

  /**
   * Requisição genérica POST com headers de autenticação
   */
  async post(endpoint, data) {
    const headers = this.obterHeaders();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
    return response.json();
  }

  /**
   * Monta headers com config_key
   */
  obterHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.configKey) {
      headers['X-Config-Key'] = this.configKey;
    }
    return headers;
  }

  /**
   * Carrega config da sessão se existir
   */
  carregarDaSessao() {
    const configKey = sessionStorage.getItem('config_key');
    const config = sessionStorage.getItem('pld_config');

    if (configKey) {
      this.configKey = configKey;
      this.config = config ? JSON.parse(config) : null;
      console.log(`✓ Config carregada da sessão: ${configKey}`);
      return true;
    }
    return false;
  }

  /**
   * Limpa configuração
   */
  limpar() {
    this.configKey = null;
    this.config = null;
    sessionStorage.removeItem('config_key');
    sessionStorage.removeItem('pld_config');
  }
}

// Singleton global
export const apiService = new ApiService();

// Carregar config da sessão automaticamente
apiService.carregarDaSessao();
'''

criar_arquivo('frontend-app/src/services/apiService.js', api_service_js)

# ===== 2. CONTEXTO REACT PARA CONFIG =====
print("[2/6] Criando frontend-app/src/context/ConfigContext.js...")

config_context_js = '''/**
 * React Context para compartilhar configuração entre componentes
 */

import React, { createContext, useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/apiService';

export const ConfigContext = createContext();

export function ConfigProvider({ children }) {
  const [configKey, setConfigKey] = useState(null);
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState('desconectado');
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);

  // Carregar config da sessão ao montar
  useEffect(() => {
    if (apiService.carregarDaSessao()) {
      setConfigKey(apiService.configKey);
      setConfig(apiService.config);
      setStatus('conectado');
    }
  }, []);

  const validarConfig = useCallback(async (configData) => {
    setCarregando(true);
    setErro(null);

    try {
      const resultado = await apiService.validarConfiguracao(configData);

      if (resultado.sucesso) {
        setConfigKey(resultado.config_key);
        setConfig(configData);
        setStatus('conectado');
        return { sucesso: true, ...resultado };
      } else {
        setErro(resultado.erro);
        setStatus('erro');
        return { sucesso: false, erro: resultado.erro };
      }
    } catch (e) {
      const mensagem = e.message || 'Erro desconhecido';
      setErro(mensagem);
      setStatus('erro');
      return { sucesso: false, erro: mensagem };
    } finally {
      setCarregando(false);
    }
  }, []);

  const testarConexao = useCallback(async (configData) => {
    setCarregando(true);

    try {
      const resultado = await apiService.testarConexao(configData);
      return resultado;
    } finally {
      setCarregando(false);
    }
  }, []);

  const desconectar = useCallback(async () => {
    if (configKey) {
      await apiService.fecharConfiguracao(configKey);
    }
    apiService.limpar();
    setConfigKey(null);
    setConfig(null);
    setStatus('desconectado');
    setErro(null);
  }, [configKey]);

  const value = {
    configKey,
    config,
    status,
    carregando,
    erro,
    validarConfig,
    testarConexao,
    desconectar
  };

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const context = React.useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig deve ser usado dentro de ConfigProvider');
  }
  return context;
}
'''

criar_arquivo('frontend-app/src/context/ConfigContext.js', config_context_js)

# ===== 3. COMPONENTE CONFIGURAÇÃO ATUALIZADO =====
print("[3/6] Atualizando frontend-app/src/screens/Configuracao.js...")

configuracao_js = '''import React, { useState } from 'react';
import { useConfig } from '../context/ConfigContext';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Configuracao() {
  const { configKey, config, status, carregando, erro, validarConfig, testarConexao, desconectar } = useConfig();

  const [formData, setFormData] = useState({
    servidor: config?.servidor || '',
    banco: config?.banco || '',
    usuario: config?.usuario || '',
    senha: config?.senha || ''
  });

  const [testando, setTestando] = useState(false);
  const [statusTeste, setStatusTeste] = useState(null);

  // Handle form change
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Validar configuração
  const handleValidar = async (e) => {
    e.preventDefault();
    
    if (!formData.servidor || !formData.banco || !formData.usuario || !formData.senha) {
      alert('⚠️ Preencha todos os campos');
      return;
    }

    const resultado = await validarConfig(formData);
    
    if (resultado.sucesso) {
      alert(`✅ Configuração ativada com sucesso!\\nVersão: ${resultado.detalhes.versao_sistema}`);
    } else {
      alert(`❌ Erro: ${resultado.erro}`);
    }
  };

  // Apenas testar conexão
  const handleTestar = async () => {
    if (!formData.servidor || !formData.banco || !formData.usuario || !formData.senha) {
      alert('⚠️ Preencha todos os campos');
      return;
    }

    setTestando(true);
    setStatusTeste(null);

    try {
      const resultado = await testarConexao(formData);
      setStatusTeste(resultado);
    } finally {
      setTestando(false);
    }
  };

  // Desconectar
  const handleDesconectar = async () => {
    if (window.confirm('Tem certeza que deseja desconectar?')) {
      await desconectar();
      setFormData({ servidor: '', banco: '', usuario: '', senha: '' });
      alert('✓ Desconectado');
    }
  };

  return (
    <div style={containerStyle}>
      <h2>⚙️ Configuração de Banco de Dados</h2>

      {/* Status Card */}
      <div style={statusCardStyle(status)}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong style={{ fontSize: '14px' }}>Status da Conexão</strong>
            <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>
              {status === 'conectado' && (
                <>
                  ✅ Conectado como: <code>{config?.usuario}@{config?.servidor}</code>
                  <br/>
                  Config Key: <code style={{ fontSize: '10px' }}>{configKey}</code>
                </>
              )}
              {status === 'desconectado' && '❌ Desconectado - Nenhuma configuração ativa'}
              {status === 'erro' && `⚠️ Erro: ${erro}`}
            </p>
          </div>
          {status === 'conectado' && (
            <button onClick={handleDesconectar} style={btnDangerStyle}>
              🔌 Desconectar
            </button>
          )}
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleValidar} style={formStyle}>
        <div style={fieldGroupStyle}>
          <label>Servidor SQL Server</label>
          <input
            type="text"
            name="servidor"
            placeholder="ex: localhost ou 192.168.1.10"
            value={formData.servidor}
            onChange={handleChange}
            disabled={carregando || testando}
            style={inputStyle}
          />
          <small style={helpTextStyle}>IP ou nome do servidor SQL Server</small>
        </div>

        <div style={fieldGroupStyle}>
          <label>Banco de Dados</label>
          <input
            type="text"
            name="banco"
            placeholder="ex: PLD"
            value={formData.banco}
            onChange={handleChange}
            disabled={carregando || testando}
            style={inputStyle}
          />
          <small style={helpTextStyle}>Nome do banco de dados PLD</small>
        </div>

        <div style={fieldGroupStyle}>
          <label>Usuário SQL</label>
          <input
            type="text"
            name="usuario"
            placeholder="ex: sa"
            value={formData.usuario}
            onChange={handleChange}
            disabled={carregando || testando}
            style={inputStyle}
          />
          <small style={helpTextStyle}>Usuário de autenticação SQL</small>
        </div>

        <div style={fieldGroupStyle}>
          <label>Senha</label>
          <input
            type="password"
            name="senha"
            placeholder="Sua senha"
            value={formData.senha}
            onChange={handleChange}
            disabled={carregando || testando}
            style={inputStyle}
          />
          <small style={helpTextStyle}>Senha do usuário SQL</small>
        </div>

        <div style={buttonGroupStyle}>
          <button
            type="button"
            onClick={handleTestar}
            disabled={carregando || testando}
            style={btnSecondaryStyle}
          >
            {testando ? '⌛ Testando...' : '🔍 Testar Conexão'}
          </button>
          <button
            type="submit"
            disabled={carregando || testando}
            style={btnPrimaryStyle}
          >
            {carregando ? '⌛ Validando...' : '✅ Validar e Ativar'}
          </button>
        </div>
      </form>

      {/* Resultado do teste */}
      {statusTeste && (
        <div style={resultadoStyle(statusTeste.status)}>
          <strong>{statusTeste.status === 'ok' ? '✅ Sucesso' : '❌ Erro'}</strong>
          <p>{statusTeste.mensagem}</p>
          {statusTeste.detalhes && (
            <pre style={{ fontSize: '11px', color: '#666', margin: '10px 0 0 0' }}>
              {JSON.stringify(statusTeste.detalhes, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Info Box */}
      <div style={infoBoxStyle}>
        <strong>ℹ️ Como funciona:</strong>
        <ul style={{ margin: '10px 0 0 0', fontSize: '12px', paddingLeft: '20px' }}>
          <li>Configure suas credenciais SQL Server</li>
          <li>Clique "Testar Conexão" para validar (opcional)</li>
          <li>Clique "Validar e Ativar" para conectar ao banco</li>
          <li>Uma vez conectado, todas as operações usarão essa conexão</li>
          <li>Você pode desconectar e conectar a outro servidor quando quiser</li>
        </ul>
      </div>
    </div>
  );
}

// ===== ESTILOS =====
const containerStyle = {
  padding: '30px',
  backgroundColor: '#f8f9fa',
  minHeight: '100vh'
};

const statusCardStyle = (status) => ({
  padding: '20px',
  marginBottom: '30px',
  borderRadius: '8px',
  border: '2px solid',
  borderColor: status === 'conectado' ? '#10b981' : status === 'erro' ? '#ef4444' : '#d1d5db',
  backgroundColor: status === 'conectado' ? '#ecfdf5' : status === 'erro' ? '#fef2f2' : '#f9fafb'
});

const formStyle = {
  backgroundColor: 'white',
  padding: '20px',
  borderRadius: '8px',
  marginBottom: '20px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
};

const fieldGroupStyle = {
  marginBottom: '15px'
};

const inputStyle = {
  width: '100%',
  padding: '10px',
  border: '1px solid #d1d5db',
  borderRadius: '4px',
  fontSize: '14px',
  marginTop: '5px',
  boxSizing: 'border-box'
};

const helpTextStyle = {
  display: 'block',
  marginTop: '4px',
  color: '#6b7280',
  fontSize: '11px'
};

const buttonGroupStyle = {
  display: 'flex',
  gap: '10px',
  marginTop: '20px'
};

const btnPrimaryStyle = {
  flex: 1,
  padding: '10px',
  backgroundColor: '#007bff',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontSize: '14px',
  fontWeight: 'bold',
  cursor: 'pointer',
  transition: 'background-color 0.2s'
};

const btnSecondaryStyle = {
  flex: 1,
  padding: '10px',
  backgroundColor: '#6c757d',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontSize: '14px',
  fontWeight: 'bold',
  cursor: 'pointer'
};

const btnDangerStyle = {
  padding: '8px 12px',
  backgroundColor: '#ef4444',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontSize: '12px',
  cursor: 'pointer'
};

const resultadoStyle = (status) => ({
  padding: '15px',
  marginBottom: '20px',
  borderRadius: '8px',
  backgroundColor: status === 'ok' ? '#ecfdf5' : '#fef2f2',
  border: `1px solid ${status === 'ok' ? '#10b981' : '#ef4444'}`,
  color: status === 'ok' ? '#065f46' : '#7f1d1d'
});

const infoBoxStyle = {
  padding: '15px',
  backgroundColor: '#eff6ff',
  border: '1px solid #93c5fd',
  borderRadius: '8px',
  fontSize: '13px',
  color: '#1e40af'
};
'''

criar_arquivo('frontend-app/src/screens/Configuracao.js', configuracao_js)

# ===== 4. HOOK CUSTOM useApi =====
print("[4/6] Criando frontend-app/src/hooks/useApi.js...")

use_api_js = '''/**
 * Hook customizado para requisições com config_key automático
 */

import { useState, useCallback } from 'react';
import { useConfig } from '../context/ConfigContext';

export function useApi() {
  const { configKey } = useConfig();
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState(null);

  const fazer_requisicao = useCallback(async (endpoint, options = {}) => {
    if (!configKey) {
      setErro('Nenhuma configuração ativa');
      return null;
    }

    setCarregando(true);
    setErro(null);

    try {
      const headers = {
        'Content-Type': 'application/json',
        'X-Config-Key': configKey,
        ...options.headers
      };

      const response = await fetch(endpoint, {
        ...options,
        headers
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.message || 'Erro na requisição');
      }

      return await response.json();
    } catch (e) {
      setErro(e.message);
      console.error('Erro API:', e);
      return null;
    } finally {
      setCarregando(false);
    }
  }, [configKey]);

  return { fazer_requisicao, carregando, erro };
}
'''

criar_arquivo('frontend-app/src/hooks/useApi.js', use_api_js)

# ===== 5. ATUALIZAR APP.JS =====
print("[5/6] Atualizando frontend-app/src/App.js...")

app_js = '''import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

import Home from './screens/home';
import Clientes from './screens/Clientes';
import Movimentacoes from './screens/Movimentacoes';
import Monitoramento from './screens/Monitoramento';
import Normalizacao from './screens/Normalizacao';
import Configuracao from './screens/Configuracao';
import CargaCoTit from './screens/Cargacotit';

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

const authContainerStyle = { 
  display: 'flex', 
  justifyContent: 'center', 
  alignItems: 'center', 
  height: '100vh', 
  backgroundColor: '#20232a' 
};

const authBoxStyle = { 
  backgroundColor: 'white', 
  padding: '40px', 
  borderRadius: '10px', 
  textAlign: 'center',
  maxWidth: '400px'
};

const inputStyle = { 
  width: '100%', 
  padding: '10px', 
  margin: '5px 0', 
  borderRadius: '4px', 
  border: '1px solid #ddd',
  boxSizing: 'border-box'
};

const btnSubmitStyle = { 
  ...inputStyle, 
  backgroundColor: '#007bff', 
  color: 'white', 
  cursor: 'pointer', 
  fontWeight: 'bold'
};

// ===== COMPONENTE LOGIN =====
const AuthSystem = ({ onLogin, carregando }) => {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');

  return (
    <div style={authContainerStyle}>
      <div style={authBoxStyle}>
        <h2 style={{ color: '#333', marginBottom: '20px' }}>
          🚀 Gerador Ágil PLD v2.0
        </h2>
        <form onSubmit={(e) => { e.preventDefault(); onLogin(user, pass); }}>
          <input
            type="text"
            placeholder="Usuário"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            style={inputStyle}
            required
          />
          <input
            type="password"
            placeholder="Senha"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            style={inputStyle}
            required
          />
          <button
            type="submit"
            style={btnSubmitStyle}
            disabled={carregando}
          >
            {carregando ? '⌛ Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
};

// ===== COMPONENTE NAVBAR COM STATUS =====
function NavBar({ userTipo, onLogout }) {
  const { configKey, config, status } = useConfig();

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
            <span>✓ {config?.usuario}@{config?.servidor?.split('\\\\')[0]}</span>
          ) : (
            <span>✗ Sem conexão</span>
          )}
        </div>
        <button onClick={onLogout} style={btnLogout}>
          Sair
        </button>
      </div>
    </nav>
  );
}

// ===== COMPONENTE PRINCIPAL =====
function AppContent() {
  const [autenticado, setAutenticado] = useState(false);
  const [userTipo, setUserTipo] = useState('VISUALIZADOR');
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    if (localStorage.getItem('pld_autenticado') === 'true') {
      setAutenticado(true);
      setUserTipo(localStorage.getItem('pld_tipo') || 'VISUALIZADOR');
    }
  }, []);

  const handleLogin = async (usuario, senha) => {
    setCarregando(true);
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
        alert('❌ ' + (data.message || 'Erro ao fazer login'));
      }
    } catch (e) {
      alert('❌ Erro ao conectar com API');
    } finally {
      setCarregando(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setAutenticado(false);
    window.location.reload();
  };

  if (!autenticado) {
    return <AuthSystem onLogin={handleLogin} carregando={carregando} />;
  }

  return (
    <Router>
      <div style={{ padding: '20px' }}>
        <NavBar userTipo={userTipo} onLogout={handleLogout} />

        <Routes>
          <Route path="/" element={<Home userTipo={userTipo} />} />
          <Route path="/configuracao" element={<Configuracao />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/Cargacotit" element={<CargaCoTit />} />
          <Route path="/movimentacoes" element={<Movimentacoes />} />
          <Route path="/normalizacao" element={<Normalizacao />} />
          <Route path="/monitoramento" element={<Monitoramento />} />
        </Routes>
      </div>
    </Router>
  );
}

// ===== APP WRAPPER COM CONTEXT =====
export default function App() {
  return (
    <ConfigProvider>
      <AppContent />
    </ConfigProvider>
  );
}
'''

criar_arquivo('frontend-app/src/App.js', app_js)

# ===== 6. EXEMPLO DE COMPONENTE COM HOOK =====
print("[6/6] Criando exemplo - frontend-app/src/screens/Clientes_v2.js...")

clientes_v2_js = '''/**
 * Exemplo de como usar useApi hook com config dinâmica
 * Este é um modelo para atualizar Clientes.js
 */

import React, { useState } from 'react';
import { useConfig } from '../context/ConfigContext';
import { useApi } from '../hooks/useApi';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function ClientesV2() {
  const { configKey, status } = useConfig();
  const { fazer_requisicao, carregando, erro } = useApi();

  const [quantidade, setQuantidade] = useState(100);
  const [progresso, setProgresso] = useState(null);

  // Verificar se está conectado
  if (status !== 'conectado') {
    return (
      <div style={{ padding: '20px', backgroundColor: '#fff3cd', borderRadius: '8px' }}>
        <strong>⚠️ Configuração necessária</strong>
        <p>Você precisa configurar uma conexão SQL Server na aba "Configuração" antes de gerar clientes.</p>
      </div>
    );
  }

  const handleGerar = async () => {
    // Usar Server-Sent Events para monitorar progresso
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/gerar_clientes/stream?quantidade=${quantidade}&config_key=${configKey}`
    );

    eventSource.onmessage = (e) => {
      try {
        const status = JSON.parse(e.data);
        setProgresso(status);
      } catch (err) {
        console.error('Erro ao parsear evento:', err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setProgresso(null);
    };
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <h2>👥 Gerador de Clientes</h2>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px' }}>
        <div style={{ marginBottom: '15px' }}>
          <label>Quantidade de Clientes</label>
          <input
            type="number"
            value={quantidade}
            onChange={(e) => setQuantidade(parseInt(e.target.value))}
            disabled={carregando}
            style={{ width: '100%', padding: '10px', marginTop: '5px' }}
          />
        </div>

        <button
          onClick={handleGerar}
          disabled={carregando}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {carregando ? '⌛ Gerando...' : '🚀 Gerar Clientes'}
        </button>

        {erro && (
          <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px' }}>
            ❌ {erro}
          </div>
        )}

        {progresso && (
          <div style={{ marginTop: '15px' }}>
            <div style={{ marginBottom: '10px' }}>
              <strong>{progresso.percentual}%</strong>
              <div style={{
                width: '100%',
                height: '20px',
                backgroundColor: '#e0e0e0',
                borderRadius: '10px',
                overflow: 'hidden',
                marginTop: '5px'
              }}>
                <div style={{
                  width: `${progresso.percentual}%`,
                  height: '100%',
                  backgroundColor: '#28a745',
                  transition: 'width 0.3s'
                }} />
              </div>
            </div>
            <p>{progresso.mensagem}</p>
            <small>Registros inseridos: {progresso.registros_inseridos}</small>
          </div>
        )}
      </div>
    </div>
  );
}
'''

criar_arquivo('frontend-app/src/screens/Clientes_v2.js', clientes_v2_js)

# ===== CRIAR PASTAS =====
print("[Bônus] Criando estrutura de pastas...")
criar_arquivo('frontend-app/src/services/.gitkeep', '')
criar_arquivo('frontend-app/src/context/.gitkeep', '')
criar_arquivo('frontend-app/src/hooks/.gitkeep', '')

print()
print("=" * 70)
print("✅ FRONTEND v2.0 IMPLEMENTADO COM SUCESSO")
print("=" * 70)
print()
print("📁 Arquivos criados:")
print()
print("  Services:")
print("    ✓ frontend-app/src/services/apiService.js")
print()
print("  Context (Estado Global):")
print("    ✓ frontend-app/src/context/ConfigContext.js")
print()
print("  Hooks Customizados:")
print("    ✓ frontend-app/src/hooks/useApi.js")
print()
print("  Componentes Atualizados:")
print("    ✓ frontend-app/src/screens/Configuracao.js")
print("    ✓ frontend-app/src/App.js")
print()
print("  Exemplos:")
print("    ✓ frontend-app/src/screens/Clientes_v2.js")
print()
print("=" * 70)
print()
print("🔄 Fluxo de funcionamento:")
print()
print("  1. Usuário acessa app (App.js)")
print("  2. Faz login")
print("  3. Vai para Configuração")
print("  4. Preenche credenciais SQL")
print("  5. Clica 'Validar e Ativar'")
print("     → POST /config/validar")
print("     → Backend cria engine dinâmico")
print("     → config_key retornado ao frontend")
print("  6. config_key armazenado em sessão (ConfigContext)")
print("  7. Todos componentes acessam via useConfig()")
print("  8. useApi() automaticamente inclui X-Config-Key nos headers")
print("  9. Backend usa config_key para saber qual engine usar")
print()
print("=" * 70)
print()
print("📋 Próximos passos:")
print()
print("  1. npm install (no frontend-app/)")
print("  2. Atualizar outros componentes (Clientes.js, Movimentacoes.js)")
print("     → Use useApi() em vez de sessionStorage")
print("  3. Testar fluxo completo:")
print("     → npm start (frontend)")
print("     → uvicorn api-gateway.main:app --reload (backend)")
print("     → Login → Config → Gerar Clientes")
print()
print("=" * 70)

