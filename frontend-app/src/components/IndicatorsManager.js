/**
 * Gerenciador de Indicadores
 * Lógica para escolher qual componente renderizar baseado no sistema/base
 */

import React from 'react';
import IndicatorsCORP from './IndicatorsCORP';
import IndicatorsDefault from './IndicatorsDefault';

const IndicatorsManager = ({ 
  sistema, 
  banco, 
  saude = {}, 
  clientesPendentes = {}, 
  atualizadoEm, 
  erro,
  loading = false 
}) => {
  // Loading state
  if (loading) {
    return (
      <div style={{
        padding: '20px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        textAlign: 'center',
        color: '#6b7280'
      }}>
        <div style={{fontSize: '14px'}}>⏳ Carregando indicadores...</div>
      </div>
    );
  }

  // Props comuns para ambos os componentes
  const commonProps = {
    saude,
    banco,
    atualizadoEm,
    erro
  };

  // Seleciona o componente baseado no sistema
  if (sistema && sistema.toUpperCase() === 'CORP') {
    return (
      <IndicatorsCORP 
        {...commonProps}
        clientesPendentes={clientesPendentes}
      />
    );
  }

  // Padrão para bases que não são CORP (EGUARDIAN, manual, etc)
  return <IndicatorsDefault {...commonProps} />;
};

export default IndicatorsManager;
