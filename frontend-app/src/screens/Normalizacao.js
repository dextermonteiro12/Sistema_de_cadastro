import React, { useState } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Normalizacao() {
  const [status, setStatus] = useState({});
  const [procLoading, setProcLoading] = useState(false);

  const verificarStatus = async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return alert("⚠️ Configure o ambiente SQL Server primeiro!");
    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/check_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      const data = await res.json();
      if (data.status === "ok") setStatus(data.tabelas || {});
    } catch (err) { alert("Erro ao conectar"); }
    finally { setProcLoading(false); }
  };

  const executarNormalizacao = async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return alert("Configure o SQL antes");
    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/setup_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      if (res.ok) { alert("✅ Ambiente Normalizado!"); verificarStatus(); } 
    } catch (err) { alert("Erro na normalização"); }
    finally { setProcLoading(false); }
  };

  return (
    <div style={{ padding: '30px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <h3>🛡️ Normalização do Ambiente SQL Server</h3>
      <div style={{ margin: '20px 0', border: '1px solid #eee', borderRadius: '8px', padding: '15px', background: '#fcfcfc' }}>
        {Object.entries(status).length === 0 ? (
          <p style={{textAlign: 'center', color: '#888'}}>Clique em verificar para analisar o banco de dados.</p>
        ) : (
          Object.entries(status).map(([tab, state]) => (
            <div key={tab} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
              <code style={{fontSize: '13px'}}>{tab}</code>
              <span style={{ color: state === 'Criada' ? '#28a745' : '#dc3545', fontWeight: 'bold' }}>
                {state === 'Criada' ? '✅ CRIADA' : '❌ AUSENTE'}
              </span>
            </div>
          ))
        )}
      </div>
      <div style={{ display: 'flex', gap: '10px' }}>
        <button onClick={verificarStatus} disabled={procLoading} style={btnStyle('#6c757d')}>🔍 Verificar Status</button>
        <button onClick={executarNormalizacao} disabled={procLoading} style={btnStyle('#28a745')}>🛠️ Criar Tabelas</button>
      </div>
    </div>
  );
}

const btnStyle = (color) => ({ padding: '10px 20px', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', backgroundColor: color, color: 'white' });