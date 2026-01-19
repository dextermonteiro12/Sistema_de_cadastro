import React, { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';

export default function TbFilaADSVC() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return;
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/fila-adsvc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      const result = await res.json();
      if (result.status === "ok") setData(result.dados);
    } catch (err) {
      console.error("Erro fila:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Fila atualiza mais rápido (5s)
    return () => clearInterval(interval);
  }, [fetchData]);

  const isHighLoad = data?.pendentes > 1000;

  return (
    <div style={{ ...cardStyle, borderTopColor: isHighLoad ? '#f59e0b' : '#10b981' }}>
      <div style={headerStyle}>📥 FILA ADSVC (PENDENTES)</div>
      <div style={{ ...valueStyle, color: isHighLoad ? '#d97706' : '#111827' }}>
        {data?.pendentes?.toLocaleString('pt-BR') || '0'}
      </div>
      <div style={infoContainerStyle}>
        <div style={infoRowStyle}>
          <span style={labelSmallStyle}>Processados hoje:</span>
          <span style={textSmallStyle}>{data?.processados?.toLocaleString('pt-BR') || '0'}</span>
        </div>
      </div>
    </div>
  );
}

// Reutilize os mesmos estilos do tb_pesquisas_log.js para manter o padrão
const cardStyle = { backgroundColor: '#fff', padding: '25px', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', borderTop: '4px solid', width: '350px' };
const headerStyle = { color: '#6b7280', fontSize: '12px', fontWeight: '700' };
const valueStyle = { fontSize: '42px', fontWeight: '800', margin: '12px 0' };
const infoContainerStyle = { marginTop: '10px', borderTop: '1px solid #f3f4f6', paddingTop: '10px' };
const infoRowStyle = { display: 'flex', justifyContent: 'space-between' };
const labelSmallStyle = { fontSize: '11px', color: '#9ca3af', fontWeight: '600' };
const textSmallStyle = { fontSize: '11px', color: '#4b5563', fontWeight: '500' };