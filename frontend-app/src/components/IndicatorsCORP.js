/**
 * Componente de Indicadores para CORP
 * Mostra KPIs específicos do CORP
 * 
 * KPIs: Fila, Status, Erros, Clientes sem integrar
 */

import React from 'react';

const IndicatorsCORP = ({ saude, clientesPendentes, banco, atualizadoEm, erro }) => {
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
    borderBottom: '2px solid #3b82f6'
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
    fila: {
      valor: saude?.fila || 0,
      status: (saude?.fila || 0) < 100 ? 'ok' : (saude?.fila || 0) < 500 ? 'warning' : 'error',
      label: 'Fila de Processamento'
    },
    status: {
      valor: saude?.status === 'ok' ? '✓ Online' : '✗ Offline',
      status: saude?.status === 'ok' ? 'ok' : 'error',
      label: 'Status do Servidor'
    },
    erros: {
      valor: saude?.erros || 0,
      status: (saude?.erros || 0) === 0 ? 'ok' : (saude?.erros || 0) < 10 ? 'warning' : 'error',
      label: 'Erros Registrados'
    },
    clientes: {
      valor: clientesPendentes?.quantidade || 0,
      status: (clientesPendentes?.quantidade || 0) === 0 ? 'ok' : 'warning',
      label: 'Clientes Pendentes'
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
        📊 Indicadores CORP - {banco}
      </div>

      <div style={kpiGridStyle}>
        {/* KPI: Fila */}
        <div style={kpiCardStyle(dados.fila.status)}>
          <div style={kpiLabelStyle}>{dados.fila.label}</div>
          <div style={kpiValueStyle}>{dados.fila.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.fila.status === 'ok' ? '✓ Normal' : dados.fila.status === 'warning' ? '⚠ Atenção' : '✗ Crítico'}
          </div>
        </div>

        {/* KPI: Status */}
        <div style={kpiCardStyle(dados.status.status)}>
          <div style={kpiLabelStyle}>{dados.status.label}</div>
          <div style={kpiValueStyle}>{dados.status.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.status.status === 'ok' ? 'Operacional' : 'Indisponível'}
          </div>
        </div>

        {/* KPI: Erros */}
        <div style={kpiCardStyle(dados.erros.status)}>
          <div style={kpiLabelStyle}>{dados.erros.label}</div>
          <div style={kpiValueStyle}>{dados.erros.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.erros.status === 'ok' ? 'Sem erros' : `${dados.erros.valor} erro(s)`}
          </div>
        </div>

        {/* KPI: Clientes */}
        <div style={kpiCardStyle(dados.clientes.status)}>
          <div style={kpiLabelStyle}>{dados.clientes.label}</div>
          <div style={kpiValueStyle}>{dados.clientes.valor}</div>
          <div style={{fontSize: '12px', color: '#6b7280'}}>
            {dados.clientes.status === 'ok' ? 'Nenhum' : `${dados.clientes.valor} pendente(s)`}
          </div>
        </div>
      </div>

      <div style={metadataStyle}>
        <span>Atualizado: {atualizadoEm ? new Date(atualizadoEm).toLocaleTimeString('pt-BR') : 'N/A'}</span>
        <span style={{fontSize: '10px'}}>CORP</span>
      </div>
    </div>
  );
};

export default IndicatorsCORP;
