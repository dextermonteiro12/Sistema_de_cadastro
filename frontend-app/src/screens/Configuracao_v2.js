import React, { useCallback, useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConfig } from '../context/ConfigContext';
import { apiService } from '../services/apiService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Configuracao() {
  const navigate = useNavigate();
  const { validarConfig } = useConfig();

  const [step, setStep] = useState(1); // 1: XML, 2: SQL, 3: Validar, 4: Sucesso
  const folderPathRef = useRef('');
  const basesDaPastaRef = useRef([]);
  const baseSelecionadaIdRef = useRef('');
  const servidorRef = useRef('');
  const usuarioRef = useRef('');
  const senhaRef = useRef('');
  
  const [basesDaPasta, setBasesDaPasta] = useState([]);
  const [baseSelecionadaId, setBaseSelecionadaId] = useState('');
  const [carregandoXml, setCarregandoXml] = useState(false);
  const [erroXml, setErroXml] = useState(null);
  const [mensagemXml, setMensagemXml] = useState(null);

  const [testando, setTestando] = useState(false);
  const [statusTeste, setStatusTeste] = useState(null);
  const [basesSalvas, setBasesSalvas] = useState(null);

  // 🔍 Debug: monitorar mudanças no estado basesDaPasta
  useEffect(() => {
    console.log('🔵 [ESTADO] basesDaPasta mudou:', basesDaPasta);
    console.log('🔵 [ESTADO] Total de bases no estado:', basesDaPasta.length);
    console.log('🔵 [ESTADO] Ref tem:', basesDaPastaRef.current.length, 'bases');
    
    // 🔧 FALLBACK: Se estado ficar vazio mas ref tem dados, restaurar
    if (basesDaPasta.length === 0 && basesDaPastaRef.current.length > 0) {
      console.log('⚠️ [ESTADO] Estado vazio mas ref tem dados! Restaurando...');
      setBasesDaPasta([...basesDaPastaRef.current]);
      return;
    }
    
    basesDaPasta.forEach((base, idx) => {
      console.log(`🔵 [ESTADO] Base ${idx}:`, base);
    });
  }, [basesDaPasta]);

  const getBaseSelecionada = () => {
    const lista = basesDaPasta.length > 0 ? basesDaPasta : basesDaPastaRef.current;
    return lista.find((base) => base.id === baseSelecionadaId) || null;
  };

  const handleSelecionarBase = (id) => {
    console.log('🔵 Selecionando base:', id);
    setBaseSelecionadaId(id);
    baseSelecionadaIdRef.current = id;
    
    // Usar fallback para encontrar a base
    const lista = basesDaPasta.length > 0 ? basesDaPasta : basesDaPastaRef.current;
    const base = lista.find((item) => item.id === id) || null;
    
    console.log('🔵 Base encontrada:', base);
    apiService.salvarBaseAtiva(base);
  };

  // ===== STEP 1: Ler XML =====
  const handleCarregarXml = async () => {
    const folderPath = folderPathRef.current;
    
    if (!folderPath.trim()) {
      setErroXml('Informe o caminho do arquivo ou pasta');
      return;
    }

    setCarregandoXml(true);
    setErroXml(null);
    setMensagemXml(null);

    try {
      const resultado = await apiService.listarBasesDaPasta(folderPath.trim());

      console.log('🔵 [XML] Resposta backend completa:', resultado);

      if (resultado.status !== 'ok') {
        setErroXml(resultado.mensagem || 'Erro ao ler arquivo');
        setCarregandoXml(false);
        return;
      }

      const lista = Array.isArray(resultado.bases) ? resultado.bases : [];
      console.log('🔵 [XML] Lista de bases recebidas:', lista);
      console.log('🔵 [XML] Total recebido:', lista.length);

      const normalizadas = lista.map((item, idx) => {
        console.log(`🔵 [XML] Processando item ${idx + 1}:`, item);
        
        if (typeof item === 'string') {
          const normalizado = {
            id: `base-${idx}`,
            sistema: 'N/A',
            banco: item,
            label: item
          };
          console.log(`  ✅ String normalizada:`, normalizado);
          return normalizado;
        }
        
        const normalizado = {
          id: item.id || `base-${idx}`,
          sistema: item.sistema || 'N/A',
          banco: item.banco || '',
          label: item.label || `${item.sistema} | ${item.banco}`
        };
        console.log(`  ✅ Objeto normalizado:`, normalizado);
        console.log(`  Campo 'banco': '${normalizado.banco}' (truthy: ${!!normalizado.banco})`);
        return normalizado;
      });

      console.log('🔵 [XML] Bases antes do filter:', normalizadas);
      
      const basesComBanco = normalizadas.filter(item => {
        const temBanco = !!item.banco;
        if (!temBanco) {
          console.log(`  ⚠️ Base FILTRADA (sem banco):`, item);
        }
        return temBanco;
      });

      console.log('🔵 [XML] Bases após filter:', basesComBanco);
      console.log('🔵 [XML] Total após filter:', basesComBanco.length);

      if (basesComBanco.length === 0) {
        setErroXml('Nenhuma base encontrada no arquivo');
        setCarregandoXml(false);
        return;
      }

      console.log('🔵 [XML] Atualizando estado com bases:', basesComBanco);
      
      // Salvar no ref ANTES do estado para garantir persistência
      basesDaPastaRef.current = basesComBanco;
      baseSelecionadaIdRef.current = basesComBanco[0].id;
      
      // Usar callback form para garantir atualização
      setBasesDaPasta(() => {
        console.log('🔵 [XML] setState callback executado com:', basesComBanco);
        return basesComBanco;
      });
      
      setBaseSelecionadaId(basesComBanco[0].id);
      apiService.salvarBaseAtiva(basesComBanco[0]);
      setMensagemXml(`✅ ${basesComBanco.length} base(s) encontrada(s)! Selecione uma base e clique em "Próximo".`);
      setCarregandoXml(false);
      
      // NÃO mudar de step automaticamente - deixar usuário ver e selecionar as bases
      console.log('🔵 [XML] Carregamento concluído. Aguardando seleção do usuário.');
    } catch (err) {
      setErroXml('Erro ao conectar com servidor');
      setCarregandoXml(false);
    }
  };

  // ===== STEP 2: Preencher SQL =====
  const handleProximoStep = () => {
    if (!servidorRef.current.trim() || !usuarioRef.current.trim() || !senhaRef.current.trim()) {
      setStatusTeste({ tipo: 'erro', msg: 'Preencha todos os campos' });
      return;
    }
    setStep(3);
  };

  // ===== STEP 3: Testar Conexão =====
  const handleTestarConexao = async () => {
    setTestando(true);
    setStatusTeste(null);

    try {
      const baseSelecionada = getBaseSelecionada();
      const bancoSelecionado = baseSelecionada?.banco || '';
      
      const response = await fetch(`${API_BASE_URL}/config/teste`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config: {
            servidor: servidorRef.current,
            banco: bancoSelecionado,
            usuario: usuarioRef.current,
            senha: senhaRef.current
          }
        })
      });

      const resultado = await response.json();

      if (resultado.status === 'ok' || resultado.status === 'sucesso') {
        setStatusTeste({ tipo: 'sucesso', msg: 'Conexão bem-sucedida!' });
      } else {
        // Erro do backend (status 500 mas resposta JSON)
        setStatusTeste({ 
          tipo: 'erro', 
          msg: resultado.mensagem || resultado.erro || 'Falha ao conectar ao servidor' 
        });
      }
      setTestando(false);
    } catch (err) {
      console.error('Erro ao testar conexão:', err);
      setStatusTeste({ tipo: 'erro', msg: `Erro na requisição: ${err.message}` });
      setTestando(false);
    }
  };

  const handleValidarEAtivar = async () => {
    setTestando(true);
    setStatusTeste(null);

    try {
      const baseSelecionada = getBaseSelecionada();
      if (!baseSelecionada) {
        setStatusTeste({ tipo: 'erro', msg: 'Selecione uma base antes de validar.' });
        return;
      }

      const configAtiva = {
        servidor: servidorRef.current,
        banco: baseSelecionada.banco,
        usuario: usuarioRef.current,
        senha: senhaRef.current
      };

      const ativacao = await validarConfig(configAtiva, {
        ambiente: baseSelecionada.label || baseSelecionada.banco
      });

      if (!ativacao?.sucesso) {
        setStatusTeste({ tipo: 'erro', msg: ativacao?.erro || 'Falha ao ativar configuração.' });
        return;
      }

      // ✅ Capturar config_key da validação e associar à base
      const configKey = ativacao.config_key;
      console.log('🔑 Config key obtida:', configKey);
      
      const baseComConfigKey = {
        ...baseSelecionada,
        config_key: configKey
      };

      apiService.salvarBaseAtiva(baseComConfigKey);
      apiService.salvarSqlConfig({
        ...configAtiva,
        sistema: baseSelecionada.sistema,
        label: baseSelecionada.label,
        versao: null,
        config_key: configKey
      });

      const basesSelecionadas = [baseComConfigKey];
      
      console.log('🔵 Salvando configuração:', {
        xml_path: folderPathRef.current,
        sql_server: servidorRef.current,
        sql_username: usuarioRef.current,
        bases: basesSelecionadas
      });
      
      const resultado = await apiService.salvarConfiguracao({
        xml_path: folderPathRef.current,
        sql_server: servidorRef.current,
        sql_username: usuarioRef.current,
        sql_password: senhaRef.current,
        bases: basesSelecionadas
      });

      console.log('🟢 Resposta do backend:', resultado);

      if (resultado.status === 'ok') {
        setBasesSalvas(resultado.data);
        setStep(4); // Sucesso
      } else {
        setStatusTeste({ tipo: 'erro', msg: resultado.mensagem });
      }
    } catch (err) {
      console.error('🔴 Erro ao salvar:', err);
      setStatusTeste({ tipo: 'erro', msg: 'Erro ao salvar configuração' });
    } finally {
      setTestando(false);
    }
  };

  // ===== COMPONENTES DE UI =====

  const StepIndicator = () => (
    <div style={stepsContainerStyle}>
      {[1, 2, 3, 4].map((s) => (
        <div key={s} style={stepStyle(s, step)}>
          <div style={stepNumberStyle(s, step)}>{s}</div>
          <div style={stepLabelStyle(s, step)}>
            {['XML', 'SQL', 'Testar', 'Sucesso'][s - 1]}
          </div>
        </div>
      ))}
    </div>
  );

  const Step1 = () => (
    <div style={stepCardStyle}>
      <h2 style={stepTitleStyle}>📁 Localizar Arquivo Advice.xml</h2>
      <p style={stepDescStyle}>
        Informe o caminho completo do arquivo ou da pasta contendo o Advice.xml
      </p>

      <div style={inputGroupStyle}>
        <label style={labelStyle}>Caminho do Advice.xml</label>
        <input
          type="text"
          placeholder="Ex: C:\Advice ou C:\Advice\config\Advice.xml"
          defaultValue=""
          onChange={(e) => {
            folderPathRef.current = e.target.value;
          }}
          disabled={carregandoXml}
          style={inputStyle}
          autoComplete="off"
        />
      </div>

      {erroXml && (
        <div style={{ ...alertStyle, backgroundColor: '#fee', borderColor: '#fcc' }}>
          ❌ {erroXml}
        </div>
      )}

      {mensagemXml && (
        <div style={{ ...alertStyle, backgroundColor: '#efe', borderColor: '#cfc' }}>
          {mensagemXml}
        </div>
      )}

      {(() => {
        // Usar ref como fallback se estado estiver vazio
        const basesParaExibir = basesDaPasta.length > 0 ? basesDaPasta : basesDaPastaRef.current;
        console.log('🔵 [RENDER] Bases para exibir:', basesParaExibir);
        
        if (basesParaExibir.length === 0) return null;
        
        return (
          <div style={previewStyle}>
            <h3 style={{ color: '#1f2937', margin: '0 0 12px 0', fontSize: '14px' }}>
              📊 Bases Encontradas ({basesParaExibir.length})
            </h3>
            <div style={basesListStyle}>
              {basesParaExibir.map((base, idx) => {
                console.log(`🔵 [RENDER] Renderizando base ${idx}:`, base);
                return (
                  <div
                    key={base.id}
                    style={{
                      ...baseItemStyle,
                      backgroundColor: baseSelecionadaId === base.id ? '#dbeafe' : '#f9fafb',
                      borderColor: baseSelecionadaId === base.id ? '#0084ff' : '#e5e7eb'
                    }}
                    onClick={() => handleSelecionarBase(base.id)}
                    role="button"
                  >
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>
                      <strong>{base.sistema}</strong> | {base.banco}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
        <button
          onClick={handleCarregarXml}
          disabled={carregandoXml}
          style={buttonPrimaryStyle}
        >
          {carregandoXml ? '⏳ Lendo...' : '📂 Ler Arquivo'}
        </button>
        
        {(basesDaPasta.length > 0 || basesDaPastaRef.current.length > 0) && (
          <button
            onClick={() => {
              console.log('🔵 Avançando para Step 2');
              setStep(2);
            }}
            style={{...buttonPrimaryStyle, backgroundColor: '#10b981'}}
          >
            ➡️ Próximo
          </button>
        )}
      </div>
    </div>
  );

  const Step2 = () => (
    <div style={stepCardStyle}>
      <h2 style={stepTitleStyle}>🔐 Credenciais SQL Server</h2>
      <p style={stepDescStyle}>
        Informe os dados para se conectar ao SQL Server
      </p>

      <div style={inputGroupStyle}>
        <label style={labelStyle}>Servidor SQL</label>
        <input
          type="text"
          placeholder="Ex: localhost\SQLEXPRESS ou 192.168.1.1"
          defaultValue={servidorRef.current}
          onChange={(e) => servidorRef.current = e.target.value}
          style={inputStyle}
          autoComplete="off"
        />
        <div style={helperStyle}>IP ou nome do servidor SQL</div>
      </div>

      <div style={inputGroupStyle}>
        <label style={labelStyle}>Usuário </label>
        <input
          type="text"
          placeholder="Ex: sa ou seu_usuario"
          defaultValue={usuarioRef.current}
          onChange={(e) => usuarioRef.current = e.target.value}
          style={inputStyle}
          autoComplete="off"
        />
        <div style={helperStyle}>Usuário para autenticação</div>
      </div>

      <div style={inputGroupStyle}>
        <label style={labelStyle}>Senha</label>
        <input
          type="password"
          placeholder="••••••••"
          defaultValue={senhaRef.current}
          onChange={(e) => senhaRef.current = e.target.value}
          style={inputStyle}
          autoComplete="off"
        />
        <div style={helperStyle}>Senha do usuário SQL</div>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
        <button
          onClick={() => setStep(1)}
          style={{ ...buttonSecondaryStyle, flex: 1 }}
        >
          ← Voltar
        </button>
        <button
          onClick={handleProximoStep}
          style={{ ...buttonPrimaryStyle, flex: 1 }}
        >
          Próximo →
        </button>
      </div>
    </div>
  );

  const Step3 = () => (
    <div style={stepCardStyle}>
      <h2 style={stepTitleStyle}>✔️ Testar Conexão</h2>
      <p style={stepDescStyle}>
        Valide se os dados estão corretos e o servidor está acessível
      </p>

      <div style={connectionInfoStyle}>
        <div style={infoRowStyle}>
          <span style={{ color: '#6b7280' }}>🖥️ Servidor:</span>
          <span style={{ fontWeight: '600' }}>{servidorRef.current}</span>
        </div>
        <div style={infoRowStyle}>
          <span style={{ color: '#6b7280' }}>👤 Usuário:</span>
          <span style={{ fontWeight: '600' }}>{usuarioRef.current}</span>
        </div>
        <div style={infoRowStyle}>
          <span style={{ color: '#6b7280' }}>📊 Base:</span>
          <span style={{ fontWeight: '600' }}>
            {basesDaPasta.find(b => b.id === baseSelecionadaId)?.banco || 'N/A'}
          </span>
        </div>
      </div>

      {statusTeste && (
        <div style={{
          ...alertStyle,
          backgroundColor: statusTeste.tipo === 'sucesso' ? '#efe' : '#fee',
          borderColor: statusTeste.tipo === 'sucesso' ? '#cfc' : '#fcc'
        }}>
          <div style={{ marginBottom: '8px' }}>
            {statusTeste.tipo === 'sucesso' ? '✅' : '❌'} {statusTeste.msg}
          </div>
          {statusTeste.tipo === 'erro' && (
            <div style={{ fontSize: '12px', color: '#7f1d1d', marginTop: '8px' }}>
              💡 Dica: Verifique se o servidor está correto e as credenciais são válidas
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
        <button
          onClick={() => setStep(2)}
          style={{ ...buttonSecondaryStyle, flex: 1 }}
        >
          ← Voltar
        </button>
        <button
          onClick={handleTestarConexao}
          disabled={testando}
          style={{ ...buttonSecondaryStyle, flex: 1 }}
        >
          {testando ? '⏳ Testando...' : '🔗 Testar Conexão'}
        </button>
        <button
          onClick={handleValidarEAtivar}
          disabled={testando || statusTeste?.tipo !== 'sucesso'}
          style={{ ...buttonPrimaryStyle, flex: 1 }}
        >
          {testando ? '⏳ Salvando...' : '✅ Validar & Ativar'}
        </button>
      </div>
    </div>
  );

  const Step4 = () => (
    <div style={stepCardStyle}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '64px', marginBottom: '20px' }}>🎉</div>
        <h2 style={{ ...stepTitleStyle, textAlign: 'center' }}>Configuração Concluída!</h2>
        <p style={{ ...stepDescStyle, textAlign: 'center' }}>
          Suas bases foram salvas com sucesso
        </p>
      </div>

      {basesSalvas && (
        <div style={previewStyle}>
          <h3 style={{ color: '#1f2937', marginTop: '20px', marginBottom: '12px' }}>
            📊 Resumo da Configuração
          </h3>
          <div style={summaryStyle}>
            <div style={summaryRowStyle}>
              <span>Total de Bases:</span>
              <strong>{basesSalvas.total_bases || basesDaPasta.length}</strong>
            </div>
            <div style={summaryRowStyle}>
              <span>Arquivo XML:</span>
              <strong style={{ fontSize: '12px' }}>Salvo</strong>
            </div>
            <div style={summaryRowStyle}>
              <span>Credenciais:</span>
              <strong style={{ fontSize: '12px' }}>Encriptadas</strong>
            </div>
          </div>
        </div>
      )}

      <button
        onClick={() => navigate('/')}
        style={{ ...buttonPrimaryStyle, marginTop: '30px', width: '100%' }}
      >
        ✨ Ir para Dashboard
      </button>
    </div>
  );

  // ===== RENDER =====
  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ margin: 0, color: '#1f2937', fontSize: '24px' }}>
          ⚙️ Configuração de Banco de Dados
        </h1>
      </div>

      <StepIndicator />

      <div style={contentStyle}>
        {step === 1 && <Step1 />}
        {step === 2 && <Step2 />}
        {step === 3 && <Step3 />}
        {step === 4 && <Step4 />}
      </div>
    </div>
  );
}

// ===== ESTILOS =====

const containerStyle = {
  minHeight: '100vh',
  backgroundColor: '#f3f4f6',
  padding: '20px'
};

const headerStyle = {
  marginBottom: '30px',
  paddingBottom: '20px',
  borderBottom: '2px solid #e5e7eb'
};

const stepsContainerStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  marginBottom: '40px',
  position: 'relative'
};

const stepStyle = (num, current) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  flex: 1,
  position: 'relative'
});

const stepNumberStyle = (num, current) => {
  let bgColor = '#e5e7eb';
  let color = '#6b7280';
  
  if (num < current) {
    bgColor = '#10b981';
    color = '#fff';
  } else if (num === current) {
    bgColor = '#3b82f6';
    color = '#fff';
  }

  return {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: bgColor,
    color: color,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '16px',
    marginBottom: '8px'
  };
};

const stepLabelStyle = (num, current) => ({
  fontSize: '12px',
  fontWeight: '600',
  color: num <= current ? '#1f2937' : '#9ca3af'
});

const contentStyle = {
  maxWidth: '600px',
  margin: '0 auto'
};

const stepCardStyle = {
  backgroundColor: '#fff',
  borderRadius: '12px',
  padding: '30px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  marginBottom: '20px'
};

const stepTitleStyle = {
  margin: '0 0 8px 0',
  color: '#1f2937',
  fontSize: '20px'
};

const stepDescStyle = {
  margin: '0 0 24px 0',
  color: '#6b7280',
  fontSize: '14px'
};

const inputGroupStyle = {
  marginBottom: '20px'
};

const labelStyle = {
  display: 'block',
  marginBottom: '8px',
  fontWeight: '600',
  color: '#374151',
  fontSize: '14px'
};

const inputStyle = {
  width: '100%',
  padding: '10px 12px',
  border: '1px solid #d1d5db',
  borderRadius: '8px',
  fontSize: '14px',
  boxSizing: 'border-box',
  fontFamily: 'inherit'
};

const helperStyle = {
  fontSize: '12px',
  color: '#9ca3af',
  marginTop: '4px'
};

const alertStyle = {
  padding: '12px 16px',
  borderRadius: '8px',
  border: '1px solid #dbeafe',
  marginBottom: '16px',
  fontSize: '14px'
};

const previewStyle = {
  backgroundColor: '#f9fafb',
  border: '1px solid #e5e7eb',
  borderRadius: '8px',
  padding: '16px',
  marginBottom: '24px'
};

const basesListStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px'
};

const baseItemStyle = {
  padding: '12px',
  border: '1px solid #e5e7eb',
  borderRadius: '6px',
  cursor: 'pointer',
  transition: 'all 0.2s',
  backgroundColor: '#f9fafb'
};

const buttonPrimaryStyle = {
  width: '100%',
  padding: '12px 16px',
  backgroundColor: '#3b82f6',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  fontSize: '14px',
  fontWeight: '600',
  cursor: 'pointer',
  transition: 'all 0.2s',
  marginTop: '20px'
};

const buttonSecondaryStyle = {
  padding: '10px 16px',
  backgroundColor: '#e5e7eb',
  color: '#1f2937',
  border: 'none',
  borderRadius: '8px',
  fontSize: '14px',
  fontWeight: '600',
  cursor: 'pointer',
  transition: 'all 0.2s'
};

const connectionInfoStyle = {
  backgroundColor: '#f0f9ff',
  border: '1px solid #bfdbfe',
  borderRadius: '8px',
  padding: '16px',
  marginBottom: '20px'
};

const infoRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  paddingBottom: '8px',
  fontSize: '14px'
};

const summaryStyle = {
  backgroundColor: '#f9fafb',
  borderRadius: '8px',
  padding: '12px'
};

const summaryRowStyle = {
  display: 'flex',
  justifyContent: 'space-between',
  padding: '8px 0',
  fontSize: '14px',
  color: '#6b7280'
};
