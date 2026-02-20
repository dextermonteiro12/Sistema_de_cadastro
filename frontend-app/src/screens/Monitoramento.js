import React from 'react';
import { useConfig } from '../context/ConfigContext';
// Importação dos componentes modulares
import TbPesquisasLog from '../dashboard/tb_pesquisas_log'; 
import TbFilaADSVC from '../dashboard/tb_fila_adsvc'; 
import TbPerformanceWorkers from '../dashboard/tb_performance_workers';

export default function Monitoramento() {
  const { ambiente } = useConfig();

  return (
    <div style={containerStyle}>
      <h2 style={titleStyle}>
        🛰️ Painel de Monitoramento em Tempo Real
      </h2>
      <div style={contextStyle}>
        Ambiente ativo: <strong>{ambiente || '-'}</strong> | Sessão: <strong>{sessionStorage.getItem('pld_session_id') || '-'}</strong>
      </div>
      
      {/* 1. Grid superior para Cards de Resumo (KPIs) */}
      <div style={dashboardGridStyle}>
        <TbPesquisasLog />
        <TbFilaADSVC />
      </div>

      {/* 2. Seção inferior para a Tabela de Performance */}
      <div style={tableSectionStyle}>
        <TbPerformanceWorkers />
      </div>
    </div>
  );
}

// --- ESTILOS DA TELA PRINCIPAL ---

const containerStyle = { 
  padding: '30px', 
  backgroundColor: '#f0f2f5', 
  minHeight: '100vh',
  fontFamily: 'Segoe UI, Roboto, Helvetica, Arial, sans-serif',
  display: 'flex',
  flexDirection: 'column',
  gap: '10px'
};

const titleStyle = { 
  marginBottom: '20px', 
  color: '#1a1f36', 
  fontWeight: '700',
  fontSize: '24px',
  letterSpacing: '-0.02em'
};

const dashboardGridStyle = { 
  display: 'flex', 
  flexWrap: 'wrap', 
  gap: '20px',
  alignItems: 'flex-start',
  marginBottom: '10px'
};

const tableSectionStyle = {
  width: '100%',
  maxWidth: '1200px', // Limita a largura para não esticar demais em telas ultra-wide
  marginTop: '10px'
};

const contextStyle = {
  marginTop: '-8px',
  marginBottom: '10px',
  fontSize: '12px',
  color: '#4b5563'
};