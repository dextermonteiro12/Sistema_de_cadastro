/**
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
