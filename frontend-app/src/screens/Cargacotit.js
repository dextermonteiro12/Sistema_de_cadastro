import React, { useState } from 'react';
import { apiService } from '../services/apiService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function CargaCoTit() {
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState([]);

  const adicionarLog = (msg) => {
    setLog(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);
  };

  const executarCarga = async () => {
    const conf = apiService.carregarSqlConfig();
    const baseAtiva = apiService.carregarBaseAtiva();
    if (!conf || !baseAtiva?.banco) return alert("⚠️ Configure o ambiente SQL e selecione a base primeiro!");

    const configFinal = {
      ...conf,
      banco: baseAtiva.banco
    };
    const confirmacao = window.confirm(`Inicia carga CO_TIT para o Layout ${conf.versao}? Isso irá resetar a tabela TAB_CLIENTES_CO_TIT_PLD.`);
    
    if (!confirmacao) return;

    setLoading(true);
    adicionarLog("Iniciando processo de carga...");

    try {
      const res = await fetch(`${API_BASE_URL}/executar_carga_cotit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: configFinal })
      });

      const data = await res.json();

      if (res.ok) {
        adicionarLog(`✅ Sucesso: ${data.mensagem}`);
        adicionarLog(`📊 Registros processados: ${data.total_processado}`);
      } else {
        adicionarLog(`❌ Erro: ${data.erro}`);
      }
    } catch (err) {
      adicionarLog("❌ Falha crítica na comunicação com a API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '30px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <h3>🚀 Carga de Dados: Co-Titularidade (CO_TIT)</h3>
      <p style={{ color: '#666', fontSize: '14px' }}>
        Este processo lê a <b>TB_CLIENTE</b> e gera 3 registros na <b>TAB_CLIENTES_CO_TIT_PLD</b>:
        <br />- 1 Registro baseado no titular real.
        <br />- 2 Registros com dados fictícios automáticos.
      </p>

      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <button 
          onClick={executarCarga} 
          disabled={loading} 
          style={btnStyle(loading ? '#ccc' : '#007bff')}
        >
          {loading ? '⚙️ Processando Carga...' : 'Gerar Dados Fictícios'}
        </button>
      </div>

      <div style={{ 
        marginTop: '25px', 
        padding: '15px', 
        backgroundColor: '#1e1e1e', 
        color: '#00ff00', 
        borderRadius: '5px',
        fontFamily: 'monospace',
        height: '200px',
        overflowY: 'auto',
        fontSize: '12px'
      }}>
        <strong>Console de Saída:</strong>
        <hr style={{ borderColor: '#333' }} />
        {log.length === 0 && <div>Aguardando comando...</div>}
        {log.map((item, idx) => <div key={idx}>{item}</div>)}
      </div>
    </div>
  );
}

const btnStyle = (color) => ({ 
  padding: '12px 24px', 
  border: 'none', 
  borderRadius: '4px', 
  fontWeight: 'bold', 
  cursor: 'pointer', 
  backgroundColor: color, 
  color: 'white' 
});