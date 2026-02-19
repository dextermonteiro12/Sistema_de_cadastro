import React, { useState, useEffect, useCallback } from 'react';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function TbFilaADSVC() {
  const [data, setData] = useState(null);

  const fetchData = useCallback(async () => {
    const configKey = sessionStorage.getItem('config_key');
    if (!configKey) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/fila-adsvc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Config-Key': configKey },
        body: JSON.stringify({ config_key: configKey })
      });
      const result = await res.json();
      if (result.status === 'ok') setData(result.dados);
    } catch {}
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 5000); return () => clearInterval(i); }, [fetchData]);

  const isHighLoad = (data?.pendentes || 0) > 1000;
  return (
    <div style={{ ...cardStyle, borderTopColor: isHighLoad ? '#f59e0b' : '#10b981' }}>
      <div style={headerStyle}>FILA ADSVC (PENDENTES)</div>
      <div style={{ ...valueStyle, color: isHighLoad ? '#d97706' : '#111827' }}>{data?.pendentes?.toLocaleString('pt-BR') || '0'}</div>
      <div style={infoContainerStyle}>
        <div style={infoRowStyle}><span style={labelSmallStyle}>Processados:</span><span style={textSmallStyle}>{data?.processados?.toLocaleString('pt-BR') || '0'}</span></div>
      </div>
    </div>
  );
}
const cardStyle = { backgroundColor:'#fff', padding:'25px', borderRadius:'12px', boxShadow:'0 10px 15px -3px rgba(0,0,0,0.1)', borderTop:'4px solid', width:'350px' };
const headerStyle = { color:'#6b7280', fontSize:'12px', fontWeight:'700' };
const valueStyle = { fontSize:'42px', fontWeight:'800', margin:'12px 0' };
const infoContainerStyle = { marginTop:'10px', borderTop:'1px solid #f3f4f6', paddingTop:'10px' };
const infoRowStyle = { display:'flex', justifyContent:'space-between' };
const labelSmallStyle = { fontSize:'11px', color:'#9ca3af', fontWeight:'600' };
const textSmallStyle = { fontSize:'11px', color:'#4b5563', fontWeight:'500' };
