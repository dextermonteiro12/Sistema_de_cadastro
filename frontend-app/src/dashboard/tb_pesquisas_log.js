import React, { useState, useEffect, useCallback } from 'react';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function TbPesquisasLog() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const configKey = sessionStorage.getItem('config_key');
    if (!configKey) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/log-pesquisas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Config-Key': configKey },
        body: JSON.stringify({ config_key: configKey })
      });
      const result = await res.json();
      if (result.status === 'ok') { setData(result.dados); setError(false); } else { setError(true); }
    } catch { setError(true); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i); }, [fetchData]);

  if (loading && !data) return <div style={{...cardStyle, borderTopColor:'#e5e7eb', color:'#64748b'}}>Carregando Logs...</div>;

  return (
    <div style={cardStyle}>
      <div style={headerStyle}>LOG DE PESQUISAS</div>
      <div style={valueStyle}>{data?.total?.toLocaleString('pt-BR') || '0'}</div>
      <div style={infoContainerStyle}>
        <div style={infoRowStyle}><span style={labelSmallStyle}>Início:</span><span style={textSmallStyle}>{data?.data_inicio || '---'}</span></div>
        <div style={infoRowStyle}><span style={labelSmallStyle}>Fim:</span><span style={textSmallStyle}>{data?.data_fim || '---'}</span></div>
      </div>
      {error && <div style={errorStyle}>Erro ao sincronizar dados</div>}
    </div>
  );
}
const cardStyle = { backgroundColor:'#fff', padding:'25px', borderRadius:'12px', boxShadow:'0 10px 15px -3px rgba(0,0,0,0.1)', borderTop:'4px solid #6366f1', width:'350px', display:'flex', flexDirection:'column' };
const headerStyle = { color:'#6b7280', fontSize:'12px', fontWeight:'700', letterSpacing:'0.05em' };
const valueStyle = { fontSize:'42px', fontWeight:'800', color:'#111827', margin:'12px 0' };
const infoContainerStyle = { marginTop:'10px', borderTop:'1px solid #f3f4f6', paddingTop:'10px' };
const infoRowStyle = { display:'flex', justifyContent:'space-between', marginBottom:'4px' };
const labelSmallStyle = { fontSize:'11px', color:'#9ca3af', fontWeight:'600' };
const textSmallStyle = { fontSize:'11px', color:'#4b5563', fontWeight:'500' };
const errorStyle = { color:'#ef4444', fontSize:'10px', fontWeight:'bold', marginTop:'10px', textAlign:'center', backgroundColor:'#fef2f2', padding:'5px', borderRadius:'4px' };
