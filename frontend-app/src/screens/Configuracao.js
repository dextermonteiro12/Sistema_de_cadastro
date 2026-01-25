import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Configuracao() {
  const [config, setConfig] = useState({ servidor: '', banco: '', usuario: '', senha: '', versao: '' });
  const [loading, setLoading] = useState(false);

  // Carrega as configurações APENAS desta aba (sessão)
  useEffect(() => {
    const savedConfig = sessionStorage.getItem('pld_sql_config');
    if (savedConfig) setConfig(JSON.parse(savedConfig));
  }, []);

  const handleSave = (e) => {
    e.preventDefault();
    // Salva no sessionStorage para isolar de outras abas
    sessionStorage.setItem('pld_sql_config', JSON.stringify(config));
    alert("✅ Configurações salvas para esta aba!");
    
    // Opcional: remover o reload se quiser manter o estado do React vivo
    // window.location.reload(); 
  };

  const handleTestarConexao = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/check_ambiente`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });
      
      const data = await res.json();
      
      if (data.status === "ok") {
        const configComVersao = { ...config, versao: data.versao };
        setConfig(configComVersao);
        
        // Salva a detecção automática na sessão atual
        sessionStorage.setItem('pld_sql_config', JSON.stringify(configComVersao));
        
        alert(`✅ Conexão SQL OK!\nAmbiente Detectado: ${data.versao}`);
      } else {
        alert("❌ Erro: " + data.erro);
      }
    } catch (err) { 
      alert("❌ Erro de rede ou servidor ocupado (Timeout)."); 
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h3 style={{ margin: 0 }}>⚙️ Ambiente SQL Server (Sessão Isolada)</h3>
        
        {config.versao && (
          <span style={{
            padding: '5px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            backgroundColor: config.versao === 'V9' ? '#10b981' : '#3b82f6',
            color: 'white'
          }}>
            LAYOUT: {config.versao}
          </span>
        )}
      </div>

      <form onSubmit={handleSave} style={{ display: 'grid', gap: '15px', maxWidth: '450px' }}>
        <input type="text" placeholder="Servidor (ex: localhost\SQLEXPRESS)" value={config.servidor} onChange={e => setConfig({...config, servidor: e.target.value})} style={inputStyle} />
        <input type="text" placeholder="Nome do Banco de Dados" value={config.banco} onChange={e => setConfig({...config, banco: e.target.value})} style={inputStyle} />
        <input type="text" placeholder="Usuário SQL (sa)" value={config.usuario} onChange={e => setConfig({...config, usuario: e.target.value})} style={inputStyle} />
        <input type="password" placeholder="Senha" value={config.senha} onChange={e => setConfig({...config, senha: e.target.value})} style={inputStyle} />
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" style={{ ...btnStyle, backgroundColor: '#007bff' }}>
            💾 Salvar nesta Aba
          </button>
          <button 
            type="button" 
            onClick={handleTestarConexao} 
            disabled={loading}
            style={{ ...btnStyle, backgroundColor: '#6c757d', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? "⌛ Detectando..." : "🔍 Testar Conexão"}
          </button>
        </div>
      </form>
      
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#fff3cd', border: '1px solid #ffeeba', borderRadius: '4px' }}>
        <p style={{ fontSize: '12px', color: '#856404', margin: 0 }}>
          <strong>Dica de Isolamento:</strong> Usamos <code>sessionStorage</code>. Você pode configurar a V8 aqui e abrir uma <b>Nova Aba</b> para configurar a V9. Uma carga iniciada em uma aba não impedirá a navegação na outra.
        </p>
      </div>
    </div>
  );
}

const inputStyle = { padding: '10px', border: '1px solid #ddd', borderRadius: '4px', width: '100%' };
const btnStyle = { padding: '10px 20px', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', color: 'white' };