import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ClientTable from './components/ClientTable'; 
import GeneratorForm from './components/GeneratorForm'; 
import './App.css';

// --- 1. COMPONENTES DAS TELAS ---

const TelaIntegracao = () => {
  const [abaAtiva, setAbaAtiva] = useState('cliente');
  
  // Estados movidos para cá: agora a geração acontece dentro da aba de Integração
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);

  const handleGenerateData = (quantidade) => {
    const URL_API = `http://127.0.0.1:5000/gerar_dados/${quantidade}`;
    setLoading(true);
    setErro(null);
    setClientes([]);

    fetch(URL_API)
      .then(response => {
        if (!response.ok) throw new Error('Falha na resposta da rede.');
        return response.json();
      })
      .then(data => setClientes(data))
      .catch(error => {
        console.error("Erro:", error);
        setErro("Erro ao carregar dados. Verifique a API Python.");
      })
      .finally(() => setLoading(false));
  };

  const menuLateral = [
    { id: 'cliente', label: 'Integração de Cliente' },
    { id: 'nacional', label: 'Movimentação Financeira Nacional' },
    { id: 'estrangeira', label: 'Movimentação Financeira Estrangeira' }
  ];

  return (
    <div style={{ display: 'flex', minHeight: '80vh', border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', backgroundColor: 'white' }}>
      {/* SIDEBAR LATERAL */}
      <div style={{ width: '300px', backgroundColor: '#f8f9fa', borderRight: '1px solid #ddd', padding: '20px' }}>
        <h4 style={{ color: '#20232a', marginBottom: '20px', borderBottom: '2px solid #61dafb', paddingBottom: '10px' }}>
          Tipos de Integração
        </h4>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {menuLateral.map((item) => (
            <li 
              key={item.id}
              onClick={() => setAbaAtiva(item.id)}
              style={{
                padding: '12px 15px',
                cursor: 'pointer',
                borderRadius: '4px',
                marginBottom: '5px',
                backgroundColor: abaAtiva === item.id ? '#61dafb' : 'transparent',
                color: abaAtiva === item.id ? '#20232a' : '#555',
                fontWeight: abaAtiva === item.id ? 'bold' : 'normal',
                transition: 'all 0.2s'
              }}
            >
              {item.label}
            </li>
          ))}
        </ul>
      </div>

      {/* ÁREA DE CONTEÚDO DINÂMICO */}
      <div style={{ flex: 1, padding: '30px', textAlign: 'left', overflowY: 'auto' }}>
        {abaAtiva === 'cliente' && (
          <div>
            <h3>📁 Integração de Cliente (Sandbox)</h3>
            <p>Utilize o gerador abaixo para simular a carga de dados no seu sistema de PLD.</p>
            
            {/* O GERADOR AGORA VIVE AQUI */}
            <div style={{ backgroundColor: '#f0f7ff', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
              <GeneratorForm onGenerate={handleGenerateData} />
            </div>

            {loading && <p>Carregando dados da API Python...</p>}
            {erro && <p style={{ color: 'red' }}>Erro: {erro}</p>}
            
            {!loading && !erro && clientes.length > 0 && (
              <ClientTable clientes={clientes} />
            )}

            {clientes.length === 0 && !loading && (
               <div className="codigo-box">Endpoint de Teste: <code>/api/v1/pld/clientes</code></div>
            )}
          </div>
        )}
        {abaAtiva === 'nacional' && (
          <div>
            <h3>🇧🇷 Movimentação Financeira Nacional</h3>
            <p>Monitoramento de transações em Reais (BRL), PIX, TED e DOC.</p>
            <div className="codigo-box">Endpoint: <code>/api/v1/pld/transacoes/nacional</code></div>
          </div>
        )}
        {abaAtiva === 'estrangeira' && (
          <div>
            <h3>🌐 Movimentação Financeira Estrangeira</h3>
            <p>Monitoramento de câmbio, Swift e remessas internacionais.</p>
            <div className="codigo-box">Endpoint: <code>/api/v1/pld/transacoes/estrangeira</code></div>
          </div>
        )}
      </div>
    </div>
  );
};

const TelaMonitoramento = () => {
  const [status, setStatus] = useState("Verificando...");
  const [detalhes, setDetalhes] = useState(null);

  useEffect(() => {
    const checarSaude = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/health');
        if (response.ok) {
          const data = await response.json();
          setStatus("Online");
          setDetalhes(data.service);
        } else {
          setStatus("Erro no Servidor");
        }
      } catch (error) {
        setStatus("Offline");
      }
    };
    checarSaude();
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h2>Painel de Monitoramento</h2>
      <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', backgroundColor: status === "Online" ? "#e6fffa" : "#fff5f5" }}>
        <p><strong>Status do Backend:</strong> <span style={{ color: status === "Online" ? "green" : "red" }}>● {status}</span></p>
        {status === "Online" && <p><small>Serviço identificado: {detalhes}</small></p>}
      </div>
    </div>
  );
};

// Nova Página Inicial
const Home = () => (
  <div style={{ padding: '50px', textAlign: 'center' }}>
    <h1>Bem-vindo ao Gerador Ágil PLD</h1>
    <p>Ferramenta de simulação para Prevenção à Lavagem de Dinheiro.</p>
    <div style={{ marginTop: '30px' }}>
      <Link to="/integracao">
        <button style={{ padding: '15px 30px', fontSize: '1.1rem', cursor: 'pointer' }}>Acessar Sandbox de Integração</button>
      </Link>
    </div>
  </div>
);

// --- 2. APP PRINCIPAL ---

function App() {
  return (
    <Router>
      <div className="container">
        <nav style={{ 
          background: '#20232a', 
          padding: '15px', 
          display: 'flex', 
          gap: '25px',
          marginBottom: '20px',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <Link to="/" style={{ color: 'white', textDecoration: 'none' }}>Início</Link>
          <Link to="/integracao" style={{ color: '#61dafb', textDecoration: 'none', fontWeight: 'bold' }}>Integrações</Link>
          <Link to="/monitoramento" style={{ color: 'white', textDecoration: 'none' }}>Monitoramento</Link>
        </nav>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/integracao" element={<TelaIntegracao />} />
          <Route path="/monitoramento" element={<TelaMonitoramento />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;