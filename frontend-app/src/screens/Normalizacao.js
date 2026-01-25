import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Normalizacao() {
  const [status, setStatus] = useState({});
  const [procLoading, setProcLoading] = useState(false);
  const [versaoAtual, setVersaoAtual] = useState('');

  // Sincroniza a versão salva na sessão ao carregar o componente
  useEffect(() => {
    const configSql = sessionStorage.getItem('pld_sql_config');
    if (configSql) {
      const parsed = JSON.parse(configSql);
      setVersaoAtual(parsed.versao || 'Não Detectada');
    }
  }, []);

  const verificarStatus = async () => {
    // Migrado para sessionStorage para isolamento de aba
    const configSql = sessionStorage.getItem('pld_sql_config');
    if (!configSql) return alert("⚠️ Configure o ambiente SQL nesta aba primeiro!");
    
    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/check_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      const data = await res.json();
      
      if (data.status === "ok") {
        setStatus(data.tabelas || {});
        // Se o backend detectou uma versão diferente, atualizamos a sessão
        if (data.versao) setVersaoAtual(data.versao);
      } else {
        alert("Erro: " + data.erro);
      }
    } catch (err) { 
      alert("❌ Falha na comunicação com a API. Verifique se o serviço está rodando."); 
    } finally { 
      setProcLoading(false); 
    }
  };

  const executarNormalizacao = async () => {
    const configSql = sessionStorage.getItem('pld_sql_config');
    if (!configSql) return alert("Configure o SQL antes");
    
    const conf = JSON.parse(configSql);
    const confirmacao = window.confirm(`Deseja criar a estrutura de tabelas para o Layout ${conf.versao || 'V8'}?`);
    if (!confirmacao) return;

    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/setup_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: conf })
      });
      if (res.ok) { 
        alert(`✅ Ambiente ${conf.versao || 'V8'} Normalizado com Sucesso!`); 
        verificarStatus(); 
      } else {
        const errorData = await res.json();
        alert("❌ Erro na normalização: " + errorData.erro);
      }
    } catch (err) { 
      alert("Erro técnico na normalização"); 
    } finally { 
      setProcLoading(false); 
    }
  };

  return (
    <div style={{ padding: '30px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>🛡️ Normalização do Ambiente SQL Server</h3>
        {versaoAtual && (
          <span style={{ 
            fontSize: '12px', 
            padding: '4px 10px', 
            borderRadius: '4px', 
            backgroundColor: versaoAtual === 'V9' ? '#10b981' : '#3b82f6', 
            color: 'white',
            fontWeight: 'bold' 
          }}>
            LENDO LAYOUT: {versaoAtual}
          </span>
        )}
      </div>

      <div style={{ margin: '20px 0', border: '1px solid #eee', borderRadius: '8px', padding: '15px', background: '#fcfcfc' }}>
        {Object.entries(status).length === 0 ? (
          <p style={{textAlign: 'center', color: '#888'}}>
            Clique em <b>Verificar</b> para analisar a presença das tabelas de integração nesta sessão.
          </p>
        ) : (
          Object.entries(status).map(([tab, state]) => (
            <div key={tab} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
              <code style={{fontSize: '13px', color: '#555'}}>{tab}</code>
              <span style={{ color: state === 'Criada' ? '#28a745' : '#dc3545', fontWeight: 'bold' }}>
                {state === 'Criada' ? '✅ CRIADA' : '❌ AUSENTE'}
              </span>
            </div>
          ))
        )}
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button onClick={verificarStatus} disabled={procLoading} style={btnStyle('#6c757d')}>
          {procLoading ? '⏳ Aguarde...' : '🔍 Verificar Status'}
        </button>
        <button onClick={executarNormalizacao} disabled={procLoading} style={btnStyle('#28a745')}>
          🛠️ Criar Estrutura {versaoAtual}
        </button>
      </div>
      
      <p style={{ fontSize: '11px', color: '#999', marginTop: '15px' }}>
        * O sistema utilizará os scripts de criação correspondentes à versão detectada na aba de Configuração.
      </p>
    </div>
  );
}

const btnStyle = (color) => ({ 
  padding: '10px 20px', 
  border: 'none', 
  borderRadius: '4px', 
  fontWeight: 'bold', 
  cursor: 'pointer', 
  backgroundColor: color, 
  color: 'white',
  transition: 'opacity 0.2s'
});