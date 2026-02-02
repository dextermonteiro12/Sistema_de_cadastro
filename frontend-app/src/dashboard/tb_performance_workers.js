import React, { useState, useEffect, useCallback } from 'react';

// O endpoint agora aponta para o registro que fizemos no app.py
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';

export default function TbPerformanceWorkers() {
  const [workers, setWorkers] = useState([]);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const configSql = sessionStorage.getItem('pld_sql_config');
    if (!configSql) return;
    
    try {
      // Endpoint ajustado para bater com o registro do Blueprint no backend
      const res = await fetch(`${API_BASE_URL}/api/dashboard/performance-workers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      
      if (!res.ok) throw new Error('Erro na API');
      
      const result = await res.json();
      if (result.status === "ok") {
        setWorkers(result.dados || []);
        setError(false);
      }
    } catch (err) { 
      console.error("Erro performance:", err); 
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000); // Atualiza a cada 8 segundos
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div style={tableContainerStyle}>
      <div style={headerTitleStyle}>
        <div style={iconPulseStyle}></div>
        Performance dos Workers (Tempo Real)
      </div>
      
      {error && (
        <div style={errorBannerStyle}>
          ⚠️ Falha ao carregar performance. Verifique a conexão com o banco.
        </div>
      )}

      <div style={tableWrapperStyle}>
        <table style={tableStyle}>
          <thead style={stickyHeaderStyle}>
            <tr>
              <th style={{ ...thStyle, width: '140px' }}>Data Execução</th>
              <th style={{ ...thStyle, width: '150px' }}>Worker</th>
              <th style={{ ...thStyle }}>Comando SQL</th>
              <th style={{ ...thStyle, width: '110px', textAlign: 'right' }}>Latência</th>
            </tr>
          </thead>
          <tbody>
            {workers.length > 0 ? (
              workers.map((w, idx) => (
                <tr key={idx} style={rowStyle}>
                  <td style={{ ...tdStyle, fontSize: '11px', color: '#64748b' }}>
                    {w.data_exec}
                  </td>
                  <td style={tdStyle}>
                    <span style={workerBadgeStyle(w.worker)}>
                        {w.worker}
                    </span>
                  </td>
                  <td style={{ ...tdStyle, fontStyle: 'italic', color: '#475569' }} title={w.exec}>
                     {w.exec || '---'}
                  </td>
                  <td style={{ 
                    ...tdStyle, 
                    fontWeight: '800', 
                    color: w.qtd_tempo > 3000 ? '#ef4444' : '#10b981',
                    textAlign: 'right'
                  }}>
                    {Number(w.qtd_tempo).toLocaleString('pt-BR')} ms
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" style={emptyStateStyle}>
                  {loading ? "Sincronizando com os workers..." : "Nenhuma execução registrada no momento."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- ESTILOS ADICIONAIS E AJUSTADOS ---

const tableContainerStyle = { 
  backgroundColor: '#fff', 
  padding: '20px', 
  borderRadius: '12px', 
  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', 
  width: '100%',
  boxSizing: 'border-box',
};

const iconPulseStyle = {
    width: '10px',
    height: '10px',
    backgroundColor: '#10b981',
    borderRadius: '50%',
    marginRight: '10px',
    boxShadow: '0 0 0 0 rgba(16, 185, 129, 1)',
    animation: 'pulse 2s infinite'
};

const workerBadgeStyle = (name) => ({
    backgroundColor: name.includes('MF') ? '#eff6ff' : '#f5f3ff',
    color: name.includes('MF') ? '#1e40af' : '#5b21b6',
    padding: '4px 8px',
    borderRadius: '6px',
    fontSize: '11px',
    fontWeight: 'bold',
    border: name.includes('MF') ? '1px solid #dbeafe' : '1px solid #ede9fe'
});

const headerTitleStyle = {
  fontSize: '16px',
  fontWeight: '700',
  color: '#0f172a',
  marginBottom: '16px',
  display: 'flex',
  alignItems: 'center'
};

const tableWrapperStyle = {
  width: '100%',
  maxHeight: '400px', 
  overflowY: 'auto', 
  borderRadius: '8px',
  border: '1px solid #e2e8f0'
};

const tableStyle = { 
  width: '100%', 
  borderCollapse: 'collapse',
  tableLayout: 'fixed' 
};

const stickyHeaderStyle = {
  position: 'sticky',
  top: 0,
  zIndex: 10,
  backgroundColor: '#f8fafc'
};

const thStyle = { 
  padding: '12px', 
  fontSize: '11px', 
  color: '#475569', 
  textTransform: 'uppercase',
  textAlign: 'left',
  borderBottom: '2px solid #f1f5f9',
  letterSpacing: '0.05em'
};

const rowStyle = {
  borderBottom: '1px solid #f1f5f9',
  transition: 'background-color 0.2s'
};

const tdStyle = { 
  padding: '12px', 
  fontSize: '13px', 
  color: '#334155',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis'
};

const errorBannerStyle = {
  color: '#b91c1c', 
  fontSize: '12px', 
  backgroundColor: '#fef2f2',
  padding: '10px',
  borderRadius: '8px',
  marginBottom: '15px',
  border: '1px solid #fee2e2'
};

const emptyStateStyle = {
  textAlign: 'center', 
  padding: '40px', 
  color: '#94a3b8',
  fontSize: '13px'
};