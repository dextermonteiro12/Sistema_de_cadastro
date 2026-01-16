import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ClientTable from './components/ClientTable'; 
import GeneratorForm from './components/GeneratorForm'; 
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// --- 1. COMPONENTE DE AUTENTICAÇÃO ---
const AuthSystem = ({ onLogin, onRegister, onRecover }) => {
  const [modo, setModo] = useState('login'); 
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (modo === 'login') onLogin(user, pass);
    else if (modo === 'cadastro') { onRegister(user, pass, email, 'VISUALIZADOR'); setModo('login'); }
    else { onRecover(email); setModo('login'); }
  };

  return (
    <div style={authContainerStyle}>
      <div style={authBoxStyle}>
        <h2 style={{ color: '#20232a' }}>Gerador Ágil PLD</h2>
        <form onSubmit={handleSubmit}>
          {modo === 'recuperar' ? (
            <input type="email" placeholder="E-mail cadastrado" value={email} onChange={(e) => setEmail(e.target.value)} style={inputStyle} required />
          ) : (
            <>
              <input type="text" placeholder="Usuário" value={user} onChange={(e) => setUser(e.target.value)} style={inputStyle} required />
              <input type="password" placeholder="Senha" value={pass} onChange={(e) => setPass(e.target.value)} style={inputStyle} required />
              {modo === 'cadastro' && <input type="email" placeholder="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} style={inputStyle} required />}
            </>
          )}
          <button type="submit" style={{...buttonStyle, backgroundColor: '#007bff', color: 'white', width: '100%', marginTop: '10px'}}>
            {modo === 'login' ? 'Entrar' : modo === 'cadastro' ? 'Cadastrar' : 'Enviar Link'}
          </button>
        </form>
        <div style={{ marginTop: '15px', fontSize: '14px' }}>
          {modo === 'login' ? (
            <><span onClick={() => setModo('cadastro')} style={linkStyle}>Criar conta</span> | <span onClick={() => setModo('recuperar')} style={linkStyle}> Esqueci a senha</span></>
          ) : <span onClick={() => setModo('login')} style={linkStyle}>Voltar ao Login</span>}
        </div>
      </div>
    </div>
  );
};

// --- 2. TELA DE MONITORAMENTO ---
const TelaMonitoramento = () => {
  const [stats, setStats] = useState(null);
  const [statusAPI, setStatusAPI] = useState("Verificando...");

  const fetchStats = async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return;
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard_stats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      const data = await res.json();
      if (data.status === "ok") { 
        setStats(data.dados); 
        setStatusAPI("Online"); 
      }
    } catch (err) { 
        setStatusAPI("Offline"); 
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return <div style={{padding: '40px', textAlign: 'center'}}>Carregando estatísticas do banco...</div>;

  return (
    <div style={{ padding: '20px', backgroundColor: '#f4f7f6', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h2 style={{ color: '#333', margin: 0 }}>📊 Dashboard Operacional</h2>
        <div style={{ fontSize: '12px', color: statusAPI === 'Online' ? '#28a745' : '#dc3545', background: '#fff', padding: '5px 12px', borderRadius: '15px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          ● Status: {statusAPI}
        </div>
      </div>

      {stats["LOG_PESQUISA"] && (
        <div style={sqlContainerStyle}>
          <div style={sqlBlockStyle}>
            <div style={sqlHeaderStyle}>COUNT TB_LISTA_PESQUISAS_LOG</div>
            <div style={sqlValueStyle}>{stats["LOG_PESQUISA"].count.toLocaleString('pt-BR')}</div>
            <div style={sqlAffectedStyle}>(1 row affected)</div>
          </div>
          <div style={{ height: '1px', background: '#eee', margin: '20px 0' }}></div>
          <div style={sqlBlockStyle}>
            <div style={{ display: 'flex', gap: '40px' }}>
              <div>
                <div style={sqlHeaderStyle}>DATA MAIS ANTIGA</div>
                <div style={sqlDateValueStyle}>{stats["LOG_PESQUISA"].antiga}</div>
              </div>
              <div>
                <div style={sqlHeaderStyle}>DATA MAIS RECENTE</div>
                <div style={sqlDateValueStyle}>{stats["LOG_PESQUISA"].recente}</div>
              </div>
            </div>
            <div style={sqlAffectedStyle}>(1 row affected)</div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- 3. TELA DE NORMALIZAÇÃO ---
const TelaNormalizacao = () => {
  const [status, setStatus] = useState({});
  const [procLoading, setProcLoading] = useState(false);

  const verificarStatus = async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return alert("⚠️ Configure o ambiente SQL Server primeiro!");
    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/check_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      const data = await res.json();
      if (data.status === "ok") setStatus(data.tabelas || {});
    } catch (err) { alert("Erro ao conectar"); }
    finally { setProcLoading(false); }
  };

  const executarNormalizacao = async () => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return alert("Configure o SQL antes");
    setProcLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/setup_ambiente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.parse(configSql) })
      });
      if (res.ok) { alert("✅ Ambiente Normalizado!"); verificarStatus(); } 
    } catch (err) { alert("Erro na normalização"); }
    finally { setProcLoading(false); }
  };

  return (
    <div style={{ padding: '30px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <h3>🛡️ Normalização do Ambiente SQL Server</h3>
      <div style={{ margin: '20px 0', border: '1px solid #eee', borderRadius: '8px', padding: '15px', background: '#fcfcfc' }}>
        {Object.entries(status).length === 0 ? (
          <p style={{textAlign: 'center', color: '#888'}}>Clique em verificar para analisar o banco de dados.</p>
        ) : (
          Object.entries(status).map(([tab, state]) => (
            <div key={tab} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
              <code style={{fontSize: '13px'}}>{tab}</code>
              <span style={{ color: state === 'Criada' ? '#28a745' : '#dc3545', fontWeight: 'bold' }}>
                {state === 'Criada' ? '✅ CRIADA' : '❌ AUSENTE'}
              </span>
            </div>
          ))
        )}
      </div>
      <div style={{ display: 'flex', gap: '10px' }}>
        <button onClick={verificarStatus} disabled={procLoading} style={{ ...buttonStyle, backgroundColor: '#6c757d', color: 'white', width: 'auto' }}>🔍 Verificar Status</button>
        <button onClick={executarNormalizacao} disabled={procLoading} style={{ ...buttonStyle, backgroundColor: '#28a745', color: 'white', width: 'auto' }}>🛠️ Criar Tabelas</button>
      </div>
    </div>
  );
};

// --- 4. TELA DE CONFIGURAÇÃO ---
const TelaConfiguracao = () => {
  const [config, setConfig] = useState({ servidor: '', banco: '', usuario: '', senha: '' });

  useEffect(() => {
    const savedConfig = localStorage.getItem('pld_sql_config');
    if (savedConfig) setConfig(JSON.parse(savedConfig));
  }, []);

  const handleSave = (e) => { e.preventDefault(); localStorage.setItem('pld_sql_config', JSON.stringify(config)); alert("✅ Salvo!"); };

  const handleTestarConexao = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/check_ambiente`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config })
      });
      const data = await res.json();
      alert(data.status === "ok" ? "✅ Conexão SQL OK!" : "❌ Erro: " + data.erro);
    } catch (err) { alert("❌ Erro de rede."); }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px', border: '1px solid #ddd' }}>
      <h3>⚙️ Ambiente SQL Server</h3>
      <form onSubmit={handleSave} style={{ display: 'grid', gap: '15px', maxWidth: '450px' }}>
        <input type="text" placeholder="Servidor" value={config.servidor} onChange={e => setConfig({...config, servidor: e.target.value})} style={inputTableStyle} />
        <input type="text" placeholder="Banco" value={config.banco} onChange={e => setConfig({...config, banco: e.target.value})} style={inputTableStyle} />
        <input type="text" placeholder="Usuário" value={config.usuario} onChange={e => setConfig({...config, usuario: e.target.value})} style={inputTableStyle} />
        <input type="password" placeholder="Senha" value={config.senha} onChange={e => setConfig({...config, senha: e.target.value})} style={inputTableStyle} />
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" style={{ ...buttonStyle, backgroundColor: '#007bff', color: 'white' }}>Salvar</button>
          <button type="button" onClick={handleTestarConexao} style={{ ...buttonStyle, backgroundColor: '#6c757d', color: 'white' }}>Testar</button>
        </div>
      </form>
    </div>
  );
};

// --- 5. TELA DE USUÁRIOS ---
const TelaUsuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  useEffect(() => { fetch(`${API_BASE_URL}/usuarios`).then(res => res.json()).then(setUsuarios).catch(() => {}); }, []);
  return (
    <div style={{ padding: '20px' }}>
      <h3>👥 Usuários</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr style={{borderBottom: '2px solid #ddd'}}><th style={tHeader}>Usuário</th><th style={tHeader}>Nível</th></tr></thead>
        <tbody>{usuarios.map(u => (<tr key={u.id}><td style={tCell}>{u.username}</td><td style={tCell}>{u.tipo}</td></tr>))}</tbody>
      </table>
    </div>
  );
};

// --- 6. TELA DE INTEGRAÇÃO ---
const TelaIntegracao = () => {
  const [integracaoAtiva, setIntegracaoAtiva] = useState('CLIENTES');
  const [dataMovimento, setDataMovimento] = useState(new Date().toISOString().split('T')[0]);

  const handleGenerateData = async (quantidade) => {
    const configSql = localStorage.getItem('pld_sql_config');
    if (!configSql) return alert("⚠️ Configure o Ambiente primeiro!");
    
    try {
      const res = await fetch(`${API_BASE_URL}/gerar_e_injetar`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          quantidade, 
          config: JSON.parse(configSql), 
          tipo: integracaoAtiva,
          data_referencia: dataMovimento // Garante o envio da data
        })
      });
      const data = await res.json();
      alert(data.message);
    } catch (err) { alert("Erro ao iniciar carga."); }
  };

  return (
    <div style={{ display: 'flex', minHeight: '80vh', border: '1px solid #ddd', borderRadius: '8px' }}>
      {/* Menu Lateral limpo apenas com botões de tipo */}
      <div style={{ width: '250px', backgroundColor: '#f8f9fa', padding: '20px', borderRight: '1px solid #ddd' }}>
        <button onClick={() => setIntegracaoAtiva('CLIENTES')} style={btnMenuSide}>👥 Clientes</button>
        <button onClick={() => setIntegracaoAtiva('MOVFIN')} style={btnMenuSide}>💰 MOVFIN</button>
        <button onClick={() => setIntegracaoAtiva('MOVFIN_ME')} style={btnMenuSide}>🏢 MOVFIN_ME</button>
        <button onClick={() => setIntegracaoAtiva('MOVFIN_INTERMEDIADOR')} style={btnMenuSide}>🤝 INTERMEDIADOR</button>
      </div>

      {/* Área de Ação Única para cada Integração */}
      <div style={{ flex: 1, padding: '30px' }}>
        <h3>Configuração: <span style={{color: '#007bff'}}>{integracaoAtiva}</span></h3>
        
        <div style={{ backgroundColor: '#fcfcfc', padding: '20px', borderRadius: '8px', border: '1px solid #eee', marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
            📅 Definir Data de Referência para {integracaoAtiva}:
          </label>
          <input 
            type="date" 
            value={dataMovimento} 
            onChange={(e) => setDataMovimento(e.target.value)}
            style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ddd', width: '200px', marginBottom: '15px' }}
          />
          
          <p style={{ fontSize: '12px', color: '#666' }}>
            * Todos os registros gerados nesta ação usarão a data selecionada acima.
          </p>
          
          <hr style={{ border: '0.5px solid #eee', margin: '20px 0' }} />
          
          {/* O GeneratorForm agora parece parte de cada ação específica */}
          <GeneratorForm onGenerate={handleGenerateData} />
        </div>
        
        <ClientTable clientes={[]} />
      </div>
    </div>
  );
};

// --- 7. APP PRINCIPAL ---
function App() {
  const [autenticado, setAutenticado] = useState(false);
  const [userTipo, setUserTipo] = useState('VISUALIZADOR');

  useEffect(() => {
    const logado = localStorage.getItem('pld_autenticado');
    if (logado === 'true') {
      setAutenticado(true);
      setUserTipo(localStorage.getItem('pld_tipo') || 'VISUALIZADOR');
    }
  }, []);

  const handleLogin = async (usuario, senha) => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: usuario, password: senha })
      });
      const data = await response.json();
      if (response.ok) {
        setAutenticado(true); setUserTipo(data.tipo);
        localStorage.setItem('pld_autenticado', 'true'); localStorage.setItem('pld_tipo', data.tipo);
      } else alert(data.message);
    } catch { alert("Erro ao conectar com API."); }
  };

  if (!autenticado) return <AuthSystem onLogin={handleLogin} onRegister={() => {}} onRecover={() => {}} />;

  return (
    <Router>
      <div className="container" style={{padding: '20px'}}>
        <nav style={navStyle}>
          <Link to="/" style={linkNav}>Início</Link>
          <Link to="/integracao" style={linkNav}>Integração</Link>
          <Link to="/normalizacao" style={linkNav}>🛡️ Normalização</Link>
          <Link to="/monitoramento" style={linkNav}>📊 Monitoramento</Link>
          <Link to="/configuracao" style={linkNav}>Ambiente</Link>
          <Link to="/usuarios" style={linkNav}>Usuários</Link>
          <button onClick={() => { localStorage.clear(); window.location.reload(); }} style={btnLogout}>Sair</button>
        </nav>

        <Routes>
          <Route path="/" element={<div style={{textAlign:'center', marginTop: '50px'}}><h1>🛡️ Painel PLD</h1><p>Nível: {userTipo}</p></div>} />
          <Route path="/integracao" element={<TelaIntegracao />} />
          <Route path="/normalizacao" element={<TelaNormalizacao />} />
          <Route path="/configuracao" element={<TelaConfiguracao />} />
          <Route path="/usuarios" element={<TelaUsuarios isAdmin={userTipo === 'ADMIN'} />} />
          <Route path="/monitoramento" element={<TelaMonitoramento />} />
        </Routes>
      </div>
    </Router>
  );
}

// --- ESTILOS RECENTES ---
const sqlContainerStyle = { backgroundColor: '#ffffff', borderRadius: '10px', padding: '25px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', border: '1px solid #e0e0e0', maxWidth: '900px', margin: '0 auto' };
const sqlBlockStyle = { fontFamily: '"Roboto Mono", monospace' };
const sqlHeaderStyle = { fontSize: '12px', color: '#666', letterSpacing: '1px', marginBottom: '10px', fontWeight: '600' };
const sqlValueStyle = { fontSize: '36px', color: '#2c3e50', fontWeight: 'bold', marginBottom: '5px' };
const sqlDateValueStyle = { fontSize: '16px', color: '#444', backgroundColor: '#f8f9fa', padding: '8px 12px', borderRadius: '4px', border: '1px solid #eee', display: 'inline-block' };
const sqlAffectedStyle = { fontSize: '11px', color: '#999', fontStyle: 'italic', marginTop: '8px' };

const btnMenuSide = { width: '100%', marginBottom: '10px', padding: '10px', cursor: 'pointer', backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '4px' };
const navStyle = { background: '#20232a', padding: '15px', display: 'flex', gap: '20px', justifyContent: 'center', borderRadius: '8px', marginBottom: '20px' };
const linkNav = { color: 'white', textDecoration: 'none', fontSize: '14px' };
const btnLogout = { background: '#ff4d4d', color: 'white', border: 'none', padding: '5px 12px', borderRadius: '4px', cursor: 'pointer' };
const tHeader = { padding: '12px', textAlign: 'left', color: '#444' };
const tCell = { padding: '12px' };
const inputTableStyle = { padding: '10px', border: '1px solid #ddd', borderRadius: '4px', width: '100%', marginBottom: '10px' };
const authContainerStyle = { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#20232a' };
const authBoxStyle = { backgroundColor: 'white', padding: '40px', borderRadius: '10px', width: '320px', textAlign: 'center' };
const inputStyle = { width: '100%', padding: '10px', margin: '5px 0', borderRadius: '4px', border: '1px solid #ddd' };
const buttonStyle = { padding: '10px 20px', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' };
const linkStyle = { color: '#007bff', cursor: 'pointer', fontSize: '12px' };

export default App;