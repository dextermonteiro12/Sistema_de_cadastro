import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';

// Registrar componentes do Chart.js
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';

const Home = () => {
    const [saude, setSaude] = useState(null);
    const [loading, setLoading] = useState(true);
    const [erro, setErro] = useState(null);

    const fetchSaude = async () => {
        const configSql = sessionStorage.getItem('pld_sql_config');
        if (!configSql) {
            setErro("Configuração de banco de dados não encontrada.");
            setLoading(false);
            return;
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/saude-servidor`, {
                method: 'POST', // Usando POST para enviar a config do banco como no monitoramento
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: JSON.parse(configSql) })
            });

            if (!res.ok) throw new Error("Falha ao obter dados do servidor.");

            const data = await res.json();
            setSaude(data);
            setErro(null);
        } catch (err) {
            setErro("API de Saúde Offline ou erro de conexão.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSaude();
        const interval = setInterval(fetchSaude, 10000); // Atualiza saúde a cada 10s
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div style={msgStyle}>🛰️ Consultando telemetria do servidor...</div>;
    if (erro) return <div style={{...msgStyle, color: '#dc3545'}}>⚠️ {erro}</div>;

    return (
        <div style={{ padding: '20px', fontFamily: 'Segoe UI, sans-serif' }}>
            <h2 style={{ marginBottom: '25px', color: '#1a1f36' }}>🚀 Saúde do Sistema</h2>

            {/* Grid de KPIs de Infraestrutura */}
            <div style={kpiGridStyle}>
                <div style={{ ...cardStyle, borderTop: `5px solid ${saude.status_geral === 'ESTÁVEL' ? '#2ecc71' : '#e74c3c'}` }}>
                    <h4 style={cardTitleStyle}>STATUS DO AMBIENTE</h4>
                    <p style={{ ...valueStyle, color: saude.status_geral === 'ESTÁVEL' ? '#27ae60' : '#c0392b' }}>
                        {saude.status_geral}
                    </p>
                    <span style={subValueStyle}>Tempo de atividade: 99.9%</span>
                </div>

                <div style={{ ...cardStyle, borderTop: '5px solid #3498db' }}>
                    <h4 style={cardTitleStyle}>CARGA NA FILA ADSVC</h4>
                    <p style={valueStyle}>{saude.cards.fila_pendente.toLocaleString()}</p>
                    <span style={subValueStyle}>Requisições aguardando</span>
                </div>

                <div style={{ ...cardStyle, borderTop: '5px solid #f1c40f' }}>
                    <h4 style={cardTitleStyle}>ERROS DE SERVIÇO (24H)</h4>
                    <p style={valueStyle}>{saude.cards.erros_servicos}</p>
                    <span style={subValueStyle}>Falhas registradas no log</span>
                </div>
            </div>

            {/* Gráfico de Performance */}
            <div style={chartContainerStyle}>
                <h4 style={{ ...cardTitleStyle, marginBottom: '20px' }}>LATÊNCIA DE PROCESSAMENTO (MS)</h4>
                <div style={{ height: '300px' }}>
                    <Bar 
                        options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } }
                        }}
                        data={{
                            labels: saude.performance_ms.map(p => p.Fila),
                            datasets: [{
                                label: 'Tempo Médio (ms)',
                                data: saude.performance_ms.map(p => p.Media),
                                backgroundColor: ['#3498db', '#9b59b6'],
                                borderRadius: 5
                            }]
                        }} 
                    />
                </div>
            </div>
        </div>
    );
};

// --- Estilos Internos ---
const kpiGridStyle = { display: 'flex', gap: '20px', marginBottom: '30px' };
const cardStyle = { 
    background: 'white', 
    padding: '20px', 
    borderRadius: '12px', 
    boxShadow: '0 4px 12px rgba(0,0,0,0.05)', 
    flex: 1,
    display: 'flex',
    flexDirection: 'column'
};
const cardTitleStyle = { fontSize: '11px', color: '#8898aa', letterSpacing: '1px', margin: '0 0 10px 0' };
const valueStyle = { fontSize: '32px', fontWeight: 'bold', margin: '0', color: '#32325d' };
const subValueStyle = { fontSize: '12px', color: '#525f7f', marginTop: '5px' };
const chartContainerStyle = { 
    background: 'white', 
    padding: '25px', 
    borderRadius: '12px', 
    boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
    border: '1px solid #e6e9f0'
};
const msgStyle = { padding: '50px', textAlign: 'center', fontSize: '18px', fontWeight: '500' };

export default Home;