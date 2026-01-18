import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';

export default function Monitoramento() {
  const [stats, setStats] = useState([]); // Agora é um array conforme o backend novo
  const [dbInfo, setDbInfo] = useState({ servidor: '', banco: '' });
  const [statusAPI, setStatusAPI] = useState("Verificando...");

  const fetchStats = async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return;
    
    try {
      // Ajustado para a nova rota do monitoramento.py
      const res = await fetch(`${API_BASE_URL}/status_dashboard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      
      const data = await res.json();
      
      if (data.status === "ok") { 
        setStats(data.dados); 
        setDbInfo({ servidor: data.servidor, banco: data.banco });
        setStatusAPI("Online"); 
      }
    } catch (err) { 
        setStatusAPI("Offline"); 
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000); // Polling mais rápido para tempo real (3s)
    return () => clearInterval(interval);
  }, []);

  if (stats.length === 0 && statusAPI === "Verificando...") {
    return <div style={{padding: '40px', textAlign: 'center'}}>Carregando estatísticas do banco...</div>;
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#f4f7f6', minHeight: '100vh' }}>
      
      {/* Header do Dashboard */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <div>
            <h2 style={{ color: '#333', margin: 0 }}>📊 Dashboard Operacional PLD</h2>
            <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
                Conectado: <strong>{dbInfo.servidor}</strong> | Banco: <strong>{dbInfo.banco}</strong>
            </p>
        </div>
        <div style={{ fontSize: '12px', color: statusAPI === 'Online' ? '#28a745' : '#dc3545', background: '#fff', padding: '5px 12px', borderRadius: '15px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          ● API {statusAPI}
        </div>
      </div>

      {/* Container de Blocos SQL */}
      <div style={sqlContainerStyle}>
        {stats.map((item, index) => (
          <div key={index} style={{ marginBottom: index !== stats.length - 1 ? '30px' : '0' }}>
            <div style={sqlBlockStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={sqlHeaderStyle}>SELECT COUNT(*) FROM {item.tabela}</div>
                <span style={{ 
                    fontSize: '10px', 
                    color: item.status === 'Ativa' ? '#28a745' : '#dc3545',
                    fontWeight: 'bold'
                }}>
                   [{item.status.toUpperCase()}]
                </span>
              </div>
              
              <div style={{ ...sqlValueStyle, color: item.status === 'Ativa' ? '#2c3e50' : '#ccc' }}>
                {item.total_registros.toLocaleString('pt-BR')}
              </div>
              
              <div style={sqlAffectedStyle}>(1 row affected)</div>
            </div>
            
            {index !== stats.length - 1 && (
                <div style={{ height: '1px', background: '#eee', margin: '20px 0' }}></div>
            )}
          </div>
        ))}
      </div>

      {statusAPI === "Offline" && (
          <div style={{ textAlign: 'center', marginTop: '20px', color: '#dc3545', fontWeight: 'bold' }}>
              ⚠️ Sem conexão com o backend. Verifique o servidor Flask.
          </div>
      )}
    </div>
  );
}

// Estilos mantidos e aprimorados
const sqlContainerStyle = { backgroundColor: '#ffffff', borderRadius: '10px', padding: '25px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', border: '1px solid #e0e0e0', maxWidth: '800px', margin: '0 auto' };
const sqlBlockStyle = { fontFamily: '"Roboto Mono", monospace' };
const sqlHeaderStyle = { fontSize: '12px', color: '#007bff', letterSpacing: '1px', marginBottom: '10px', fontWeight: '600' };
const sqlValueStyle = { fontSize: '36px', fontWeight: 'bold', marginBottom: '5px', transition: 'all 0.3s ease' };
const sqlAffectedStyle = { fontSize: '11px', color: '#999', fontStyle: 'italic', marginTop: '8px' };