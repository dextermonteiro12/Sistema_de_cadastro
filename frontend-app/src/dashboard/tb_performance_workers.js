import React, { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';

export default function TbPerformanceWorkers() {
  const [workers, setWorkers] = useState([]);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return;
    
    try {
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
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div style={tableContainerStyle}>
      <div style={headerTitleStyle}>
        <span style={{ marginRight: '8px' }}>⚡</span>
        Performance dos Workers (Top 100 Histórico)
      </div>
      
      {error && (
        <div style={errorBannerStyle}>
          ⚠️ Falha ao carregar performance.
        </div>
      )}

      <div style={tableWrapperStyle}>
        <table style={tableStyle}>
          <thead style={stickyHeaderStyle}>
            <tr>
              {/* Larguras fixas para manter o painel no quadro */}
              <th style={{ ...thStyle, width: '130px' }}>Data Execução</th>
              <th style={{ ...thStyle, width: '220px' }}>Worker / Comando</th>
              <th style={{ ...thStyle }}>EXEC (SQL)</th>
              <th style={{ ...thStyle, width: '100px', textAlign: 'right' }}>Tempo</th>
            </tr>
          </thead>
          <tbody>
            {workers.length > 0 ? (
              workers.map((w, idx) => (
                <tr key={idx} style={rowStyle}>
                  <td style={{ ...tdStyle, fontSize: '11px', color: '#64748b' }}>{w.data_exec}</td>
                  <td style={{ ...tdStyle, fontWeight: '600' }}>{w.worker}</td>
                  <td style={{ ...tdStyle, fontStyle: 'italic', color: '#94a3b8' }}>
                     {w.exec || '---'}
                  </td>
                  <td style={{ 
                    ...tdStyle, 
                    fontWeight: '800', 
                    color: w.qtd_tempo > 5000 ? '#ef4444' : '#10b981',
                    textAlign: 'right'
                  }}>
                    {Number(w.qtd_tempo).toLocaleString('pt-BR')} ms
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" style={emptyStateStyle}>
                  {loading ? "Buscando dados..." : "Nenhum registro encontrado."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- ESTILOS PARA AJUSTE DE QUADRO ---

const tableContainerStyle = { 
  backgroundColor: '#fff', 
  padding: '15px', 
  borderRadius: '12px', 
  boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', 
  width: '100%',
  boxSizing: 'border-box',
  marginTop: '10px'
};

const headerTitleStyle = {
  fontSize: '14px',
  fontWeight: '700',
  color: '#1e293b',
  marginBottom: '12px',
  display: 'flex',
  alignItems: 'center'
};

const tableWrapperStyle = {
  width: '100%',
  maxHeight: '350px', 
  overflowY: 'auto', 
  overflowX: 'hidden', // Remove a barra de rolagem horizontal da imagem
  borderRadius: '8px',
  border: '1px solid #f1f5f9'
};

const tableStyle = { 
  width: '100%', 
  borderCollapse: 'collapse',
  tableLayout: 'fixed' // Impede que o texto estique a tabela para fora do quadro
};

const stickyHeaderStyle = {
  position: 'sticky',
  top: 0,
  zIndex: 10,
  backgroundColor: '#f8fafc'
};

const thStyle = { 
  padding: '10px 12px', 
  fontSize: '10px', 
  color: '#64748b', 
  textTransform: 'uppercase',
  textAlign: 'left',
  borderBottom: '2px solid #e2e8f0'
};

const rowStyle = {
  borderBottom: '1px solid #f1f5f9'
};

const tdStyle = { 
  padding: '10px 12px', 
  fontSize: '12px', 
  color: '#334155',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis' // Adiciona "..." em textos muito longos
};

const errorBannerStyle = {
  color: '#b91c1c', 
  fontSize: '11px', 
  backgroundColor: '#fef2f2',
  padding: '8px',
  borderRadius: '6px',
  marginBottom: '10px',
  border: '1px solid #fee2e2'
};

const emptyStateStyle = {
  textAlign: 'center', 
  padding: '30px', 
  color: '#94a3b8',
  fontSize: '12px'
};