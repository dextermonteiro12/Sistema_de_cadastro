import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Normalizacao() {
  const [status, setStatus] = useState({});
  const [procLoading, setProcLoading] = useState(false);
  const [versaoAtual, setVersaoAtual] = useState('');
  const [configKey, setConfigKey] = useState('');

  useEffect(() => {
    const key = sessionStorage.getItem('config_key');
    setConfigKey(key || '');
  }, []);

  const verificarStatus = async () => {
    const key = sessionStorage.getItem('config_key');
    if (!key) return alert('Ative a configuracao primeiro.');

    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/check_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Config-Key': key },
        body: JSON.stringify({ config_key: key })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setStatus(data.tabelas || {});
        setVersaoAtual(data.versao || '');
      } else {
        alert(data.erro || data.message || 'Erro ao verificar ambiente');
      }
    } catch {
      alert('Falha na comunicacao com API');
    } finally {
      setProcLoading(false);
    }
  };

  const executarNormalizacao = async () => {
    const key = sessionStorage.getItem('config_key');
    if (!key) return alert('Ative a configuracao antes.');
    if (!window.confirm(`Criar estrutura para layout ${versaoAtual || 'detectado'}?`)) return;

    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/setup_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Config-Key': key },
        body: JSON.stringify({ config_key: key, versao: versaoAtual || null })
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        alert(data.message || 'Estrutura criada com sucesso');
        verificarStatus();
      } else {
        alert(data.erro || data.message || 'Erro na normalizacao');
      }
    } catch {
      alert('Erro tecnico na normalizacao');
    } finally {
      setProcLoading(false);
    }
  };

  return (
    <div style={{ padding: '30px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <h3>Normalizacao do Ambiente SQL Server</h3>
      <p>Config key: <b>{configKey || 'NAO ATIVA'}</b></p>
      {versaoAtual && <p>Layout detectado: <b>{versaoAtual}</b></p>}

      <div style={{ margin: '20px 0', border: '1px solid #eee', borderRadius: '8px', padding: '15px', background: '#fcfcfc' }}>
        {Object.entries(status).length === 0 ? (
          <p>Clique em Verificar Status.</p>
        ) : (
          Object.entries(status).map(([tab, state]) => (
            <div key={tab} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
              <code>{tab}</code>
              <span style={{ color: state === 'Criada' ? '#28a745' : '#dc3545', fontWeight: 'bold' }}>
                {state === 'Criada' ? 'CRIADA' : 'AUSENTE'}
              </span>
            </div>
          ))
        )}
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button onClick={verificarStatus} disabled={procLoading}>Verificar Status</button>
        <button onClick={executarNormalizacao} disabled={procLoading}>Criar Estrutura</button>
      </div>
    </div>
  );
}
