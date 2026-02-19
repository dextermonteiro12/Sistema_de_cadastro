import React, { useState, useEffect, useCallback } from 'react';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function TbPerformanceWorkers() {
  const [workers, setWorkers] = useState([]);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const configKey = sessionStorage.getItem('config_key');
    if (!configKey) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/performance-workers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Config-Key': configKey },
        body: JSON.stringify({ config_key: configKey })
      });
      if (!res.ok) throw new Error('Erro na API');
      const result = await res.json();
      if (result.status === 'ok') { setWorkers(result.dados || []); setError(false); }
    } catch { setError(true); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 8000); return () => clearInterval(i); }, [fetchData]);

  return (
    <div style={tableContainerStyle}>
      <div style={headerTitleStyle}>Performance dos Workers (Tempo Real)</div>
      {error && <div style={errorBannerStyle}>Falha ao carregar performance.</div>}
      <div style={tableWrapperStyle}>
        <table style={tableStyle}>
          <thead style={stickyHeaderStyle}>
            <tr>
              <th style={{ ...thStyle, width: '170px' }}>Data</th>
              <th style={{ ...thStyle, width: '150px' }}>Worker</th>
              <th style={{ ...thStyle }}>Comando</th>
              <th style={{ ...thStyle, width: '110px', textAlign: 'right' }}>Latência</th>
            </tr>
          </thead>
          <tbody>
            {workers.length ? workers.map((w, idx) => (
              <tr key={idx} style={rowStyle}>
                <td style={{ ...tdStyle, fontSize:'11px', color:'#64748b' }}>{w.data_exec}</td>
                <td style={tdStyle}>{w.worker}</td>
                <td style={{ ...tdStyle, fontStyle:'italic', color:'#475569' }} title={w.exec}>{w.exec || '---'}</td>
                <td style={{ ...tdStyle, fontWeight:'800', textAlign:'right' }}>{Number(w.qtd_tempo || 0).toLocaleString('pt-BR')} ms</td>
              </tr>
            )) : (
              <tr><td colSpan="4" style={emptyStateStyle}>{loading ? 'Sincronizando...' : 'Nenhuma execução registrada.'}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
const tableContainerStyle = { backgroundColor:'#fff', padding:'20px', borderRadius:'12px', boxShadow:'0 10px 15px -3px rgba(0,0,0,0.1)', width:'100%', boxSizing:'border-box' };
const headerTitleStyle = { fontSize:'16px', fontWeight:'700', color:'#0f172a', marginBottom:'16px' };
const tableWrapperStyle = { width:'100%', maxHeight:'400px', overflowY:'auto', borderRadius:'8px', border:'1px solid #e2e8f0' };
const tableStyle = { width:'100%', borderCollapse:'collapse', tableLayout:'fixed' };
const stickyHeaderStyle = { position:'sticky', top:0, zIndex:10, backgroundColor:'#f8fafc' };
const thStyle = { padding:'12px', fontSize:'11px', color:'#475569', textTransform:'uppercase', textAlign:'left', borderBottom:'2px solid #f1f5f9', letterSpacing:'0.05em' };
const rowStyle = { borderBottom:'1px solid #f1f5f9' };
const tdStyle = { padding:'12px', fontSize:'13px', color:'#334155', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' };
const errorBannerStyle = { color:'#b91c1c', fontSize:'12px', backgroundColor:'#fef2f2', padding:'10px', borderRadius:'8px', marginBottom:'15px', border:'1px solid #fee2e2' };
const emptyStateStyle = { textAlign:'center', padding:'40px', color:'#94a3b8', fontSize:'13px' };
