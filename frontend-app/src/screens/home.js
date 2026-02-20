import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { apiService } from '../services/apiService';
import { useConfig } from '../context/ConfigContext';
import IndicatorsManager from '../components/IndicatorsManager';
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Home = () => {
  const { configKey, ambiente } = useConfig();
  const [basesDisponiveis, setBasesDisponiveis] = useState([]);
  const [baseSelecionada, setBaseSelecionada] = useState('');
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(null);
  const [indicadoresBaseAtual, setIndicadoresBaseAtual] = useState(null);
  const [comboAberto, setComboAberto] = useState(false);
  const [filtroBase, setFiltroBase] = useState('');
  const comboRef = useRef(null);

  const carregarBases = useCallback(async () => {
    try {
      // Carregar bases do usuário do banco SQLite
      const resultado = await apiService.carregarBases();
      
      let lista = [];
      
      if (resultado.total > 0 && resultado.bases) {
        // Usar as bases do usuário
        lista = resultado.bases.map(base => ({
          id: base.id,
          label: base.label,
          sistema: base.sistema,
          banco: base.banco
        }));
      }

      setBasesDisponiveis(lista);
      
      // Selecionar a primeira base se houver
      if (lista.length > 0) {
        setBaseSelecionada(lista[0].id);
      } else {
        setBaseSelecionada('');
      }
    } catch (e) {
      console.error('Erro ao carregar bases:', e);
      setBasesDisponiveis([]);
      setBaseSelecionada('');
    }
  }, []);

  const buscarIndicadoresBase = useCallback(async (base) => {
    const headers = {
      'Content-Type': 'application/json',
      'X-Config-Key': base
    };

    const [saudeRes, pendentesRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/saude-servidor`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ config_key: base })
      }),
      fetch(`${API_BASE_URL}/api/clientes-pendentes`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ config_key: base })
      })
    ]);

    if (!saudeRes.ok) {
      throw new Error(`Base ${base}: falha ao consultar saúde (${saudeRes.status})`);
    }

    const saude = await saudeRes.json();
    const clientesPendentes = pendentesRes.ok ? await pendentesRes.json() : { quantidade: null };

    return {
      saude,
      clientesPendentes,
      atualizadoEm: new Date().toISOString(),
      erro: null
    };
  }, []);

  const carregarIndicadores = useCallback(async () => {
    if (!baseSelecionada) {
      setIndicadoresBaseAtual(null);
      setLoading(false);
      return;
    }

    try {
      const dados = await buscarIndicadoresBase(baseSelecionada);
      setIndicadoresBaseAtual(dados);
      setErro(null);
    } catch (e) {
      setIndicadoresBaseAtual({
        saude: null,
        clientesPendentes: null,
        atualizadoEm: new Date().toISOString(),
        erro: e.message
      });
    } finally {
      setLoading(false);
    }
  }, [baseSelecionada, buscarIndicadoresBase]);

  useEffect(() => {
    setLoading(true);
    carregarBases();
  }, [carregarBases]);

  useEffect(() => {
    setLoading(true);
    carregarIndicadores();

    const interval = setInterval(() => {
      carregarIndicadores();
    }, 10000);

    return () => clearInterval(interval);
  }, [carregarIndicadores]);

  useEffect(() => {
    const handleClickFora = (event) => {
      if (comboRef.current && !comboRef.current.contains(event.target)) {
        setComboAberto(false);
      }
    };

    document.addEventListener('mousedown', handleClickFora);
    return () => {
      document.removeEventListener('mousedown', handleClickFora);
    };
  }, []);

  const totalBasesDisponiveis = useMemo(() => basesDisponiveis.length, [basesDisponiveis]);
  const basesFiltradas = useMemo(() => {
    const termo = filtroBase.trim().toLowerCase();
    if (!termo) {
      return basesDisponiveis;
    }
    return basesDisponiveis.filter((base) => {
      const label = typeof base === 'string' ? base : (base.label || base.banco || '');
      return label.toLowerCase().includes(termo);
    });
  }, [basesDisponiveis, filtroBase]);

  const selecionarBase = (base) => {
    setBaseSelecionada(base);
    setComboAberto(false);
    setFiltroBase('');
  };

  const limparSelecaoBase = () => {
    setBaseSelecionada('');
    setComboAberto(false);
    setFiltroBase('');
  };

  if (loading && !indicadoresBaseAtual) {
    return <div style={msgStyle}>Consultando telemetria...</div>;
  }

  if (erro) {
    return <div style={{ ...msgStyle, color: '#dc3545' }}>⚠️ {erro}</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ marginBottom: '8px', color: '#1a1f36' }}>Dashboard de Saúde das Bases</h2>
      <p style={{ marginTop: 0, color: '#5b6783', marginBottom: '20px' }}>
        Selecione uma base para visualizar os indicadores em tempo real.
      </p>
      <div style={sessionInfoStyle}>
        Ambiente ativo: <strong>{ambiente || baseSelecionada || '-'}</strong> | Sessão: <strong>{sessionStorage.getItem('pld_session_id') || '-'}</strong>
      </div>

      <div style={selectorContainerStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <strong style={{ color: '#1a1f36', fontSize: '14px' }}>Bases para monitorar</strong>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={limparSelecaoBase} style={selectorButtonStyle} type="button">Limpar seleção</button>
          </div>
        </div>

        {basesDisponiveis.length === 0 ? (
          <div style={{ ...msgStyle, padding: '10px', fontSize: '14px' }}>Nenhuma base ativa encontrada.</div>
        ) : (
          <div style={comboWrapperStyle} ref={comboRef}>
            <button
              type="button"
              style={comboToggleStyle}
              onClick={() => setComboAberto((valor) => !valor)}
            >
              <span style={comboToggleTextStyle}>
                {baseSelecionada 
                  ? (() => {
                      const base = basesDisponiveis.find(b => (typeof b === 'string' ? b : b.id) === baseSelecionada);
                      return typeof base === 'string' ? base : (base?.label || base?.banco || baseSelecionada);
                    })()
                  : 'Selecione a base'}
              </span>
              <span style={comboArrowStyle}>{comboAberto ? '▴' : '▾'}</span>
            </button>

            {comboAberto && (
              <div style={comboMenuStyle}>
                <div style={comboSearchRowStyle}>
                  <input
                    type="text"
                    placeholder="Buscar base..."
                    value={filtroBase}
                    onChange={(e) => setFiltroBase(e.target.value)}
                    style={comboSearchInputStyle}
                  />
                </div>
                <div style={comboListStyle}>
                  {basesFiltradas.length === 0 ? (
                    <div style={comboEmptyStyle}>Nenhuma base encontrada</div>
                  ) : (
                    basesFiltradas.map((base) => {
                      const baseId = typeof base === 'string' ? base : base.id;
                      const baseLabel = typeof base === 'string' ? base : (base.label || base.banco);
                      return (
                        <button
                          key={baseId}
                          type="button"
                          style={{
                            ...baseOptionButtonStyle,
                            background: baseSelecionada === baseId ? '#3b82c4' : '#fff',
                            color: baseSelecionada === baseId ? '#fff' : '#1f2a44'
                          }}
                          onClick={() => selecionarBase(baseId)}
                        >
                          {baseLabel}
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div style={{ marginTop: '10px', fontSize: '12px', color: '#5b6783' }}>
          {totalBasesDisponiveis} base(s) disponível(is)
        </div>
      </div>

      {!baseSelecionada ? (
        <div style={msgStyle}>Selecione uma base para visualizar os indicadores.</div>
      ) : (
        <section key={baseSelecionada} style={basePanelStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, color: '#1a1f36' }}>Base: {baseSelecionada}</h3>
            <span style={{ fontSize: '12px', color: '#7b879d' }}>
              Atualizado: {indicadoresBaseAtual?.atualizadoEm ? new Date(indicadoresBaseAtual.atualizadoEm).toLocaleTimeString() : '-'}
            </span>
          </div>

          {/* Renderizar o componente de indicadores com base no sistema */}
          {indicadoresBaseAtual && (
            <IndicatorsManager
              sistema={
                basesDisponiveis.find(b => (typeof b === 'string' ? b : b.id) === baseSelecionada)?.sistema
              }
              banco={
                basesDisponiveis.find(b => (typeof b === 'string' ? b : b.id) === baseSelecionada)?.banco || baseSelecionada
              }
              saude={indicadoresBaseAtual?.saude}
              clientesPendentes={indicadoresBaseAtual?.clientesPendentes}
              atualizadoEm={indicadoresBaseAtual?.atualizadoEm}
              erro={indicadoresBaseAtual?.erro}
              loading={loading}
            />
          )}

          {/* Renderizar o gráfico original de performance se houver dados */}
          {!indicadoresBaseAtual?.erro && indicadoresBaseAtual?.saude?.performance_ms && (
            <div style={chartContainerStyle}>
              <h4 style={{ ...cardTitleStyle, marginBottom: '20px' }}>LATÊNCIA / CARGA</h4>
              <div style={{ height: '260px' }}>
                <Bar
                  options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }}
                  data={{
                    labels: (indicadoresBaseAtual.saude.performance_ms || []).map((p) => p.Fila),
                    datasets: [{
                      label: 'Tempo/Carga',
                      data: (indicadoresBaseAtual.saude.performance_ms || []).map((p) => p.Media),
                      backgroundColor: ['#3498db', '#9b59b6'],
                      borderRadius: 5
                    }]
                  }}
                />
              </div>
            </div>
          )}
        </section>
      )}
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
const selectorContainerStyle = { background: '#ffffff', border: '1px solid #e6e9f0', borderRadius: '12px', padding: '16px', marginBottom: '20px' };
const selectorButtonStyle = { border: '1px solid #d0d7e2', background: '#f8fafc', color: '#1a1f36', borderRadius: '6px', padding: '6px 10px', fontSize: '12px', cursor: 'pointer' };
const comboWrapperStyle = { position: 'relative' };
const comboToggleStyle = { width: '100%', background: '#ffffff', border: '1px solid #c9d4e3', borderRadius: '8px', minHeight: '38px', padding: '8px 10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' };
const comboToggleTextStyle = { fontSize: '13px', color: '#1f2a44' };
const comboArrowStyle = { fontSize: '11px', color: '#6b7b95' };
const comboMenuStyle = { position: 'absolute', top: '42px', left: 0, right: 0, zIndex: 5, background: '#fff', border: '1px solid #c9d4e3', borderRadius: '8px', boxShadow: '0 6px 20px rgba(0,0,0,0.08)' };
const comboSearchRowStyle = { padding: '8px', borderBottom: '1px solid #eef2f7' };
const comboSearchInputStyle = { width: '100%', height: '32px', border: '1px solid #d5deea', borderRadius: '6px', padding: '0 10px', fontSize: '13px', boxSizing: 'border-box' };
const comboListStyle = { maxHeight: '180px', overflowY: 'auto', padding: '6px 8px' };
const comboEmptyStyle = { fontSize: '12px', color: '#7b879d', padding: '8px 6px' };
const baseOptionButtonStyle = { width: '100%', textAlign: 'left', border: 'none', borderRadius: '6px', padding: '8px 10px', fontSize: '13px', cursor: 'pointer', marginBottom: '4px' };
const basePanelStyle = { marginBottom: '28px', background: '#f8fbff', border: '1px solid #dde7f3', borderRadius: '12px', padding: '16px' };
const sessionInfoStyle = { marginTop: '-8px', marginBottom: '14px', fontSize: '12px', color: '#4b5563' };
export default Home;