/**
 * Componente de Indicadores Genérico
 * Mostra KPIs padrão para bases não-CORP (EGUARDIAN, manual, etc)
 * 
 * KPIs: Conexão, Disponibilidade, Latência, Taxa de Erro
 */

import React from 'react';

const IndicatorsDefault = ({ saude, banco, atualizadoEm, erro }) => {
  // Estilos
  const containerStyle = {
    padding: '20px',
    backgroundColor: '#fff',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    marginBottom: '20px'
  };

  const headerStyle = {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: '15px',
    paddingBottom: '10px',
    borderBottom: '2px solid #8b5cf6'
  };

  const kpiGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '15px',
    marginBottom: '20px'
  };

  const kpiCardStyle = (status = 'normal') => ({
    padding: '15px',
    borderRadius: '6px',
    backgroundColor: status === 'ok' ? '#ecfdf5' : status === 'warning' ? '#fef3c7' : status === 'error' ? '#fef2f2' : '#f9fafb',
    borderLeft: `4px solid ${status === 'ok' ? '#10b981' : status === 'warning' ? '#f59e0b' : status === 'error' ? '#ef4444' : '#d1d5db'}`,
    textAlign: 'center'
  });

  const kpiValueStyle = {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: '10px 0'
  };

  const kpiLabelStyle = {
    fontSize: '12px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  };

  const metadataStyle = {
    fontSize: '11px',
    color: '#9ca3af',
    marginTop: '10px',
    paddingTop: '10px',
    borderTop: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  };

  // Geração de dados mock (será substituída com dados reais)
  const getMockData = () => ({
    conexao: {
      valor: saude?.conexao ? '✓ Ativa' : '✗ Inativa',
      status: saude?.conexao ? 'ok' : 'error',
      label: 'Status da Conexão'
    },
    disponibilidade: {
      valor: `${saude?.disponibilidade || 100}%`,
      status: (saude?.disponibilidade || 100) >= 95 ? 'ok' : (saude?.disponibilidade || 100) >= 80 ? 'warning' : 'error',
      label: 'Disponibilidade'
    },
    latencia: {
      valor: `${saude?.latencia || 0}ms`,
      status: (saude?.latencia || 0) < 100 ? 'ok' : (saude?.latencia || 0) < 500 ? 'warning' : 'error',
      label: 'Latência Média'
    },
    erros: {
      valor: `${saude?.erros || 0}`,
      status: (saude?.erros || 0) === 0 ? 'ok' : (saude?.erros || 0) < 5 ? 'warning' : 'error',
      label: 'Taxa de Erro'
    }
  });

  const dados = getMockData();

  if (erro) {
    return (
      <div style={{...containerStyle, backgroundColor: '#fef2f2', borderLeft: '4px solid #ef4444'}}>
        <div style={{color: '#7f1d1d', fontSize: '14px'}}>
          <strong>❌ Erro ao carregar indicadores</strong>
          <p style={{margin: '8px 0 0 0', fontSize: '12px'}}>{erro}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        📈 Indicadores - {banco}
      </div>

      <div style={kpiGridStyle}>
        {/* KPI: Conexão */}
        <div style={kpiCardStyle(dados.conexao.status)}>
          <div style={kpiLabelStyle}>{dados.conexao.label}</div>
          <div style={kpiValueStyle}>{dados.conexao.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.conexao.status === 'ok' ? 'Conectado' : 'Desconectado'}
          </div>
        </div>

        {/* KPI: Disponibilidade */}
        <div style={kpiCardStyle(dados.disponibilidade.status)}>
          <div style={kpiLabelStyle}>{dados.disponibilidade.label}</div>
          <div style={kpiValueStyle}>{dados.disponibilidade.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.disponibilidade.status === 'ok' ? 'Excelente' : dados.disponibilidade.status === 'warning' ? 'Boa' : 'Baixa'}
          </div>
        </div>

        {/* KPI: Latência */}
        <div style={kpiCardStyle(dados.latencia.status)}>
          <div style={kpiLabelStyle}>{dados.latencia.label}</div>
          <div style={kpiValueStyle}>{dados.latencia.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.latencia.status === 'ok' ? 'Ótima' : dados.latencia.status === 'warning' ? 'Aceitável' : 'Alta'}
          </div>
        </div>

        {/* KPI: Taxa de Erro */}
        <div style={kpiCardStyle(dados.erros.status)}>
          <div style={kpiLabelStyle}>{dados.erros.label}</div>
          <div style={kpiValueStyle}>{dados.erros.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.erros.status === 'ok' ? 'Zero erros' : `${dados.erros.valor} erro(s)`}
          </div>
        </div>
      </div>

      <div style={metadataStyle}>
        <span>Atualizado: {atualizadoEm ? new Date(atualizadoEm).toLocaleTimeString('pt-BR') : 'N/A'}</span>
        <span style={{fontSize: '10px'}}>PADRÃO</span>
      </div>
    </div>
  );
};

export default IndicatorsDefault;
