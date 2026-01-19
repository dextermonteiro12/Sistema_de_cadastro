import React, { useState, useEffect, useCallback } from 'react';

// URL base da sua API
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';

export default function TbPesquisasLog() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) {
      console.warn("Configuração SQL não encontrada");
      return;
    }
    
    try {
      // CORREÇÃO: URL ajustada para minúsculo para bater com a rota do Flask
      const res = await fetch(`${API_BASE_URL}/api/dashboard/log-pesquisas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      
      const result = await res.json();
      
      if (result.status === "ok") {
        setData(result.dados);
        setError(false);
      } else {
        console.error("Erro retornado pela API:", result.message || result.erro);
        setError(true);
      }
    } catch (err) {
      console.error("Erro na requisição fetch:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Atualiza a cada 10s
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div style={{...cardStyle, borderTopColor: '#e5e7eb', color: '#64748b'}}>
        ⏳ Carregando Logs...
      </div>
    );
  }

  return (
    <div style={cardStyle}>
      <div style={headerStyle}>
        <span style={{ marginRight: '8px' }}>🔍</span>
        LOG DE PESQUISAS
      </div>
      
      <div style={valueStyle}>
        {data?.total !== undefined ? data.total.toLocaleString('pt-BR') : '0'}
      </div>
      
      <div style={infoContainerStyle}>
        <div style={infoRowStyle}>
          <span style={labelSmallStyle}>Início:</span>
          <span style={textSmallStyle}>{data?.data_inicio || '---'}</span>
        </div>
        <div style={infoRowStyle}>
          <span style={labelSmallStyle}>Fim:</span>
          <span style={textSmallStyle}>{data?.data_fim || '---'}</span>
        </div>
      </div>

      {error && (
        <div style={errorStyle}>
          ⚠️ Erro ao sincronizar dados
        </div>
      )}
    </div>
  );
}

// --- ESTILOS ---
const cardStyle = {
  backgroundColor: '#fff',
  padding: '25px',
  borderRadius: '12px',
  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
  borderTop: '4px solid #6366f1',
  width: '350px',
  display: 'flex',
  flexDirection: 'column'
};

const headerStyle = { 
  color: '#6b7280', fontSize: '12px', fontWeight: '700', 
  letterSpacing: '0.05em', display: 'flex', alignItems: 'center' 
};

const valueStyle = { 
  fontSize: '42px', fontWeight: '800', color: '#111827', margin: '12px 0' 
};

const infoContainerStyle = { 
  marginTop: '10px', borderTop: '1px solid #f3f4f6', paddingTop: '10px' 
};

const infoRowStyle = { display: 'flex', justifyContent: 'space-between', marginBottom: '4px' };
const labelSmallStyle = { fontSize: '11px', color: '#9ca3af', fontWeight: '600' };
const textSmallStyle = { fontSize: '11px', color: '#4b5563', fontWeight: '500' };
const errorStyle = { 
  color: '#ef4444', fontSize: '10px', fontWeight: 'bold', 
  marginTop: '10px', textAlign: 'center', backgroundColor: '#fef2f2', 
  padding: '5px', borderRadius: '4px' 
};