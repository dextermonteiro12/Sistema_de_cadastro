import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Configuracao() {
  const [config, setConfig] = useState({ servidor: '', banco: '', usuario: '', senha: '' });

  useEffect(() => {
    const savedConfig = localStorage.getItem('pld_sql_config');
    if (savedConfig) setConfig(JSON.parse(savedConfig));
  }, []);

  const handleSave = (e) => {
    e.preventDefault();
    localStorage.setItem('pld_sql_config', JSON.stringify(config));
    alert("✅ Configurações salvas localmente!");
  };

  const handleTestarConexao = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/check_ambiente`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });
      const data = await res.json();
      alert(data.status === "ok" ? "✅ Conexão SQL OK!" : "❌ Erro: " + data.erro);
    } catch (err) { alert("❌ Erro de rede."); }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <h3>⚙️ Ambiente SQL Server</h3>
      <form onSubmit={handleSave} style={{ display: 'grid', gap: '15px', maxWidth: '450px' }}>
        <input type="text" placeholder="Servidor" value={config.servidor} onChange={e => setConfig({...config, servidor: e.target.value})} style={inputStyle} />
        <input type="text" placeholder="Banco" value={config.banco} onChange={e => setConfig({...config, banco: e.target.value})} style={inputStyle} />
        <input type="text" placeholder="Usuário" value={config.usuario} onChange={e => setConfig({...config, usuario: e.target.value})} style={inputStyle} />
        <input type="password" placeholder="Senha" value={config.senha} onChange={e => setConfig({...config, senha: e.target.value})} style={inputStyle} />
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" style={{ ...btnStyle, backgroundColor: '#007bff' }}>Salvar</button>
          <button type="button" onClick={handleTestarConexao} style={{ ...btnStyle, backgroundColor: '#6c757d' }}>Testar Conexão</button>
        </div>
      </form>
    </div>
  );
}

const inputStyle = { padding: '10px', border: '1px solid #ddd', borderRadius: '4px', width: '100%' };
const btnStyle = { padding: '10px 20px', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', color: 'white' };