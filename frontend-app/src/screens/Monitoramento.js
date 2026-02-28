import React from 'react';
import { apiService } from '../services/apiService';
// Importação dos componentes modulares
import TbPesquisasLog from '../dashboard/tb_pesquisas_log'; 
import TbFilaADSVC from '../dashboard/tb_fila_adsvc'; 
import TbPerformanceWorkers from '../dashboard/tb_performance_workers';

export default function Monitoramento() {
  const baseAtiva = apiService.carregarBaseAtiva();

  return (
    <div style={containerStyle}>
      <div style={contextStyle}>
        Base ativa: <strong>{baseAtiva?.label || baseAtiva?.banco || '-'}</strong>
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