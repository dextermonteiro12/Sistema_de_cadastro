import React, { useCallback, useState } from 'react';
import { useConfig } from '../context/ConfigContext';
import { apiService } from '../services/apiService';


export default function Configuracao() {
  const { configKey, config, ambiente, status, carregando, erro, validarConfig, testarConexao, desconectar } = useConfig();

  const [formData, setFormData] = useState({
    servidor: config?.servidor || '',
    banco: config?.banco || '',
    usuario: config?.usuario || '',
    senha: config?.senha || ''
  });

  const [testando, setTestando] = useState(false);
  const [statusTeste, setStatusTeste] = useState(null);
  const [folderPath, setFolderPath] = useState('');
  const [basesDaPasta, setBasesDaPasta] = useState([]);
  const [baseSelecionadaId, setBaseSelecionadaId] = useState('');
  const [carregandoBasesPasta, setCarregandoBasesPasta] = useState(false);
  const [erroBasesPasta, setErroBasesPasta] = useState(null);
  const [mensagemXml, setMensagemXml] = useState(null);

  const carregarBasesAtivas = useCallback(async () => {
    // Placeholder - can be removed in future refactor
  }, []);

  // Handle form change
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCarregarBasesDaPasta = async () => {
    if (!folderPath.trim()) {
      alert('⚠️ Informe o caminho da pasta raiz ou do Advice.xml');
      return;
    }

    setCarregandoBasesPasta(true);
    setErroBasesPasta(null);
    setMensagemXml(null);

    console.log('🔍 Iniciando leitura de Advice.xml para:', folderPath.trim());

    try {
      const resultado = await apiService.listarBasesDaPasta(folderPath.trim());
      
      console.log('📥 Resposta do servidor:', resultado);

      if (resultado.status !== 'ok') {
        setBasesDaPasta([]);
        const msgErro = resultado.mensagem || 'Não foi possível ler o Advice.xml';
        setErroBasesPasta(`❌ ${msgErro}`);
        console.error('Erro ao ler XML:', msgErro);
        return;
      }

      const lista = Array.isArray(resultado.bases) ? resultado.bases : [];
      console.log(`✅ ${lista.length} base(s) encontrada(s) no XML`);

      const normalizadas = lista.map((item, idx) => {
        if (typeof item === 'string') {
          return {
            id: `base-${idx}`,
            sistema: 'N/A',
            empresa: item,
            servidor: formData.servidor || '',
            banco: item,
            usuario: formData.usuario || '',
            label: item
          };
        }

        return {
          id: item.id || `base-${idx}`,
          sistema: item.sistema || 'N/A',
          empresa: item.empresa || item.banco || `Empresa ${idx + 1}`,
          servidor: item.servidor || '',
          banco: item.banco || '',
          usuario: item.usuario || '',
          label: item.label || `${item.sistema || 'N/A'} | ${item.empresa || '-'} | ${item.banco || '-'}`
        };
      }).filter((item) => item.banco);

      setBasesDaPasta(normalizadas);

      if (normalizadas.length > 0) {
        const primeira = normalizadas[0];
        setBaseSelecionadaId(primeira.id);
        setFormData((prev) => ({
          ...prev,
          servidor: primeira.servidor || prev.servidor,
          banco: primeira.banco,
          usuario: primeira.usuario || prev.usuario
        }));
        const msg = `✅ XML lido com sucesso: ${normalizadas.length} base(s) encontrada(s)`;
        setMensagemXml(msg);
        console.log(msg);
        normalizadas.forEach(base => {
          console.log(`  📊 ${base.label} | ${base.servidor}`);
        });
      } else {
        setBaseSelecionadaId('');
        setMensagemXml('⚠️ XML lido, mas nenhuma base válida foi encontrada');
        console.warn('Nenhuma base válida encontrada no XML');
      }
    } catch (error) {
      console.error('💥 Erro ao tentar ler Advice.xml:', error);
      setBasesDaPasta([]);
      setErroBasesPasta(`❌ Erro: ${error.message}`);
    } finally {
      setCarregandoBasesPasta(false);
    }
  };

  const handleSelecionarBaseXml = (e) => {
    const id = e.target.value;
    setBaseSelecionadaId(id);

    const base = basesDaPasta.find((item) => item.id === id);
    if (!base) {
      return;
    }

    setFormData((prev) => ({
      ...prev,
      servidor: base.servidor || prev.servidor,
      banco: base.banco,
      usuario: base.usuario || prev.usuario
    }));
  };

  const baseSelecionadaXml = basesDaPasta.find((item) => item.id === baseSelecionadaId) || null;

  // Validar configuração
  const handleValidar = async (e) => {
    e.preventDefault();
    
    if (!formData.servidor || !formData.banco || !formData.usuario || !formData.senha) {
      alert('⚠️ Preencha todos os campos');
      return;
    }

    const resultado = await validarConfig(formData, {
      ambiente: baseSelecionadaXml?.label || formData.banco
    });
    
    if (resultado.sucesso) {
      // Salvar configuração do usuário no banco SQLite
      const configData = {
        xml_path: folderPath || 'N/A',
        sql_server: formData.servidor,
        sql_username: formData.usuario,
        sql_password: formData.senha,
        bases: basesDaPasta.length > 0 ? basesDaPasta : [
          {
            id: formData.banco,
            sistema: 'Manual',
            empresa: 'Manual',
            servidor: formData.servidor,
            banco: formData.banco,
            usuario: formData.usuario,
            label: formData.banco
          }
        ]
      };

      const saveResult = await apiService.salvarConfiguracao(configData);
      
      if (saveResult.status === 'ok') {
        alert(`✅ Configuração salva com sucesso!\nVersão: ${resultado.detalhes.versao_sistema}\nBases: ${saveResult.total_bases}`);
      } else {
        alert(`✅ Banco validado!\nMas erro ao salvar localizado: ${saveResult.mensagem}`);
      }
    } else {
      alert(`❌ Erro: ${resultado.erro}`);
    }
  };

  // Apenas testar conexão
  const handleTestar = async () => {
    if (!formData.servidor || !formData.banco || !formData.usuario || !formData.senha) {
      alert('⚠️ Preencha todos os campos');
      return;
    }

    setTestando(true);
    setStatusTeste(null);

    try {
      const resultado = await testarConexao(formData);
      setStatusTeste(resultado);
    } finally {
      setTestando(false);
    }
  };

  // Desconectar
  const handleDesconectar = async () => {
    if (window.confirm('Tem certeza que deseja desconectar?')) {
      await desconectar();
      setFormData({ servidor: '', banco: '', usuario: '', senha: '' });
      alert('✓ Desconectado');
    }
  };

  return (
    <div style={containerStyle}>
      <h2>⚙️ Configuração de Banco de Dados</h2>



      {/* Form */}
      <form onSubmit={handleValidar} style={formStyle}>
        <div style={fieldGroupStyle}>
          <label>Caminho do Advice.xml</label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              placeholder="ex: C:\\Advice (ou C:\\Advice\\config\\Advice.xml)"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              disabled={carregando || testando || carregandoBasesPasta}
              style={inputStyle}
            />
            <button
              type="button"
              onClick={handleCarregarBasesDaPasta}
              disabled={carregando || testando || carregandoBasesPasta}
              style={btnSecondaryLargeStyle}
            >
              {carregandoBasesPasta ? '⌛ Lendo XML...' : '📄 Ler Advice.xml'}
            </button>
          </div>
          <small style={helpTextStyle}>
            Informe a pasta raiz (ex.: C:\\Advice) para ler automaticamente C:\\Advice\\config\\Advice.xml
          </small>
          <small style={helpTextStyle}>
            A senha NÃO é lida do XML; informe a senha manualmente para autenticar.
          </small>
          {erroBasesPasta && (
            <small style={{ ...helpTextStyle, color: '#b91c1c' }}>{erroBasesPasta}</small>
          )}
          {mensagemXml && !erroBasesPasta && (
            <small style={{ ...helpTextStyle, color: '#166534' }}>{mensagemXml}</small>
          )}
        </div>

        <div style={fieldGroupStyle}>
          <label>Servidor SQL Server</label>
          <input
            type="text"
            name="servidor"
            placeholder="ex: localhost ou 192.168.1.10"
            value={formData.servidor}
            onChange={handleChange}
            disabled={carregando || testando}
            style={inputStyle}
          />
          <small style={helpTextStyle}>IP ou nome do servidor SQL Server</small>
        </div>

        <div style={fieldGroupStyle}>
          <label>Banco de Dados</label>
          {basesDaPasta.length > 0 ? (
            <>
              <select
                name="banco_xml"
                value={baseSelecionadaId}
                onChange={handleSelecionarBaseXml}
                disabled={carregando || testando}
                style={inputStyle}
              >
                {basesDaPasta.map((base) => (
                  <option key={base.id} value={base.id}>{base.label}</option>
                ))}
              </select>
              <small style={helpTextStyle}>Base selecionada do Advice.xml ({basesDaPasta.length} encontrada(s), ex.: CORP e EGUARDIAN)</small>
            </>
          ) : (
            <>
              <input
                type="text"
                name="banco"
                placeholder="ex: PLD"
                value={formData.banco}
                onChange={handleChange}
                disabled={carregando || testando}
                style={inputStyle}
              />
              <small style={helpTextStyle}>Nome do banco de dados PLD</small>
            </>
          )}
        </div>

        <div style={fieldGroupStyle}>
          <label>Usuário SQL</label>
          <input
            type="text"
            name="usuario"
            placeholder="ex: sa"
            value={formData.usuario}
            onChange={handleChange}
            disabled={carregando || testando}
            style={inputStyle}
          />
          <small style={helpTextStyle}>Usuário de autenticação SQL</small>
        </div>

        <div style={fieldGroupStyle}>
          <label>Senha</label>
          <input
            type="password"
            name="senha"
            placeholder="Sua senha"
            value={formData.senha}
            onChange={handleChange}
            disabled={carregando || testando}
            style={inputStyle}
          />
          <small style={helpTextStyle}>Senha do usuário SQL</small>
        </div>

        <div style={buttonGroupStyle}>
          <button
            type="button"
            onClick={handleTestar}
            disabled={carregando || testando}
            style={btnSecondaryLargeStyle}
          >
            {testando ? '⌛ Testando...' : '🔍 Testar Conexão'}
          </button>
          <button
            type="submit"
            disabled={carregando || testando}
            style={btnPrimaryStyle}
          >
            {carregando ? '⌛ Validando...' : '✅ Validar e Ativar'}
          </button>
        </div>
      </form>

      {/* Resultado do teste */}
      {statusTeste && (
        <div style={resultadoStyle(statusTeste.status)}>
          <strong>{statusTeste.status === 'ok' ? '✅ Sucesso' : '❌ Erro'}</strong>
          <p>{statusTeste.mensagem}</p>
          {statusTeste.detalhes && (
            <pre style={{ fontSize: '11px', color: '#666', margin: '10px 0 0 0' }}>
              {JSON.stringify(statusTeste.detalhes, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Info Box */}
      <div style={infoBoxStyle}>
        <strong>ℹ️ Como funciona:</strong>
        <ul style={{ margin: '10px 0 0 0', fontSize: '12px', paddingLeft: '20px' }}>
          <li>Configure suas credenciais SQL Server</li>
          <li>Clique "Testar Conexão" para validar (opcional)</li>
          <li>Clique "Validar e Ativar" para conectar ao banco</li>
          <li>Uma vez conectado, todas as operações usarão essa conexão</li>
          <li>Você pode desconectar e conectar a outro servidor quando quiser</li>
        </ul>
      </div>
    </div>
  );
}

// ===== ESTILOS =====
const containerStyle = {
  padding: '30px',
  backgroundColor: '#f8f9fa',
  minHeight: '100vh'
};

const statusCardStyle = (status) => ({
  padding: '20px',
  marginBottom: '30px',
  borderRadius: '8px',
  border: '2px solid',
  borderColor: status === 'conectado' ? '#10b981' : status === 'erro' ? '#ef4444' : '#d1d5db',
  backgroundColor: status === 'conectado' ? '#ecfdf5' : status === 'erro' ? '#fef2f2' : '#f9fafb'
});

const formStyle = {
  backgroundColor: 'white',
  padding: '20px',
  borderRadius: '8px',
  marginBottom: '20px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
};

const baseTagStyle = {
  display: 'inline-block',
  padding: '6px 10px',
  borderRadius: '999px',
  border: '1px solid',
  fontSize: '11px',
  color: '#1f2937'
};

const fieldGroupStyle = {
  marginBottom: '15px'
};

const inputStyle = {
  width: '100%',
  padding: '10px',
  border: '1px solid #d1d5db',
  borderRadius: '4px',
  fontSize: '14px',
  marginTop: '5px',
  boxSizing: 'border-box'
};

const helpTextStyle = {
  display: 'block',
  marginTop: '4px',
  color: '#6b7280',
  fontSize: '11px'
};

const buttonGroupStyle = {
  display: 'flex',
  gap: '10px',
  marginTop: '20px'
};

const btnPrimaryStyle = {
  flex: 1,
  padding: '10px',
  backgroundColor: '#007bff',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontSize: '14px',
  fontWeight: 'bold',
  cursor: 'pointer',
  transition: 'background-color 0.2s'
};

const btnSecondaryLargeStyle = {
  flex: 1,
  padding: '10px',
  backgroundColor: '#6c757d',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontSize: '14px',
  fontWeight: 'bold',
  cursor: 'pointer'
};

const resultadoStyle = (status) => ({
  padding: '15px',
  marginBottom: '20px',
  borderRadius: '8px',
  backgroundColor: status === 'ok' ? '#ecfdf5' : '#fef2f2',
  border: `1px solid ${status === 'ok' ? '#10b981' : '#ef4444'}`,
  color: status === 'ok' ? '#065f46' : '#7f1d1d'
});

const infoBoxStyle = {
  padding: '15px',
  backgroundColor: '#eff6ff',
  border: '1px solid #93c5fd',
  borderRadius: '8px',
  fontSize: '13px',
  color: '#1e40af'
};
