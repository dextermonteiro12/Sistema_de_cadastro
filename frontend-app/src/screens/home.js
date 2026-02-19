import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Home = () => {
  const [saude, setSaude] = useState(null);
  const [clientesPendentes, setClientesPendentes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(null);
  const [configKey, setConfigKey] = useState(null);

  useEffect(() => {
    const key = sessionStorage.getItem('config_key');
    console.log('Config Key from session:', key);
    setConfigKey(key);
  }, []);

  const fetchSaude = async () => {
    if (!configKey) {
      console.warn('Config key não disponível');
      return;
    }
    
    try {
      console.log('Buscando saúde com config_key:', configKey);
      const res = await fetch(`${API_BASE_URL}/api/saude-servidor`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'X-Config-Key': configKey 
        },
        body: JSON.stringify({ config_key: configKey })
      });
      
      console.log('Response status:', res.status);
      if (!res.ok) throw new Error(`Status ${res.status}`);
      
      const data = await res.json();
      console.log('Saúde data:', data);
      setSaude(data);
      setErro(null);
      setLoading(false);
    } catch (err) {
      console.error('Erro ao buscar saúde:', err);
      setErro('API de Saúde Offline ou erro de conexão.');
      setLoading(false);
    }
  };

  const fetchClientesPendentes = async () => {
    if (!configKey) {
      console.warn('Config key não disponível para clientes pendentes');
      return;
    }
    
    try {
      console.log('Buscando clientes pendentes com config_key:', configKey);
      const res = await fetch(`${API_BASE_URL}/api/clientes-pendentes`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'X-Config-Key': configKey 
        },
        body: JSON.stringify({ config_key: configKey })
      });
      
      console.log('Clientes pendentes response status:', res.status);
      if (res.ok) {
        const data = await res.json();
        console.log('Clientes pendentes data:', data);
        setClientesPendentes(data);
      } else {
        console.error('Erro na resposta:', res.status);
      }
    } catch (e) {
      console.error('Erro ao buscar clientes pendentes:', e);
    }
  };

  useEffect(() => {
    if (!configKey) return;
    
    fetchSaude();
    fetchClientesPendentes();
    
    const interval = setInterval(() => {
      fetchSaude();
      fetchClientesPendentes();
    }, 10000);
    
    return () => clearInterval(interval);
  }, [configKey]);

  if (loading) return <div style={msgStyle}>Consultando telemetria...</div>;
  if (erro) return <div style={{...msgStyle, color:'#dc3545'}}>⚠️ {erro}</div>;
  if (!saude) return <div style={{...msgStyle, color:'#dc3545'}}>❌ Nenhum dado disponível</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ marginBottom: '25px', color: '#1a1f36' }}>Saúde do Sistema</h2>
      <div style={kpiGridStyle}>
        <div style={{ ...cardStyle, borderTop: `5px solid ${saude.status_geral === 'ESTÁVEL' ? '#2ecc71' : '#e74c3c'}` }}>
          <h4 style={cardTitleStyle}>STATUS DO AMBIENTE</h4>
          <p style={{ ...valueStyle, color: saude.status_geral === 'ESTÁVEL' ? '#27ae60' : '#c0392b' }}>{saude.status_geral}</p>
          <span style={subValueStyle}>Tempo de atividade</span>
        </div>
        <div style={{ ...cardStyle, borderTop: '5px solid #3498db' }}>
          <h4 style={cardTitleStyle}>CARGA NA FILA ADSVC</h4>
          <p style={valueStyle}>{(saude.cards?.fila_pendente || 0).toLocaleString()}</p>
          <span style={subValueStyle}>Requisições aguardando</span>
        </div>
        <div style={{ ...cardStyle, borderTop: '5px solid #f1c40f' }}>
          <h4 style={cardTitleStyle}>ERROS DE SERVIÇO (24H)</h4>
          <p style={valueStyle}>{saude.cards?.erros_servicos || 0}</p>
          <span style={subValueStyle}>Falhas registradas</span>
        </div>
        <div style={{ ...cardStyle, borderTop: `5px solid ${clientesPendentes?.quantidade > 0 ? '#e67e22' : '#2ecc71'}` }}>
          <h4 style={cardTitleStyle}>CLIENTES SEM INTEGRAR</h4>
          <p style={{ ...valueStyle, color: clientesPendentes?.quantidade > 0 ? '#d35400' : '#27ae60' }}>
            {clientesPendentes?.quantidade ?? 'N/A'}
          </p>
          <span style={subValueStyle}>VIEW_CLIENTES_AUX → VIEW_CLIENTES</span>
        </div>
      </div>
      <div style={chartContainerStyle}>
        <h4 style={{ ...cardTitleStyle, marginBottom: '20px' }}>LATÊNCIA / CARGA</h4>
        <div style={{ height: '300px' }}>
          <Bar
            options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }}
            data={{
              labels: (saude.performance_ms || []).map(p => p.Fila),
              datasets: [{ label: 'Tempo/Carga', data: (saude.performance_ms || []).map(p => p.Media), backgroundColor: ['#3498db', '#9b59b6'], borderRadius: 5 }]
            }}
          />
        </div>
      </div>
    </div>
  );
};

const kpiGridStyle = { display: 'flex', gap: '20px', marginBottom: '30px', flexWrap: 'wrap' };
const cardStyle = { background: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', flex: '1 1 calc(25% - 15px)', minWidth: '200px', display: 'flex', flexDirection: 'column' };
const cardTitleStyle = { fontSize: '11px', color: '#8898aa', letterSpacing: '1px', margin: '0 0 10px 0' };
const valueStyle = { fontSize: '32px', fontWeight: 'bold', margin: '0', color: '#32325d' };
const subValueStyle = { fontSize: '12px', color: '#525f7f', marginTop: '5px' };
const chartContainerStyle = { background: 'white', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', border: '1px solid #e6e9f0' };
const msgStyle = { padding: '50px', textAlign: 'center', fontSize: '18px', fontWeight: '500' };
export default Home;