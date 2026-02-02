import React, { useState, useEffect } from 'react';

export default function Clientes() {
  const [quantidade, setQuantidade] = useState(10);
  const [qtdPf, setQtdPf] = useState('');
  const [qtdPj, setQtdPj] = useState('');
  const [modoManual, setModoManual] = useState(false);
  const [carregando, setCarregando] = useState(false);
  
  const [custom, setCustom] = useState({
    CD_TP_CLIENTE: '', 
    DE_CLIENTE: '',
    CIC_CPF: '',
    DT_DESATIVACAO: '1900-01-01',
    CD_RISCO_INERENTE: 3,
    FL_GRANDES_FORTUNAS: 1,
    CD_NAT_JURIDICA: ''
  });

  // Bloqueia o campo total se houver preenchimento específico de PF ou PJ
  const isCargaDividida = qtdPf !== '' || qtdPj !== '';

  useEffect(() => {
    if (modoManual && custom.CIC_CPF.trim() !== "") {
      setQuantidade(1);
      setQtdPf('');
      setQtdPj('');
    }
  }, [custom.CIC_CPF, modoManual]);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  const handleGerar = async () => {
    setCarregando(true);
    const configSql = JSON.parse(sessionStorage.getItem('pld_sql_config'));

    try {
      const res = await fetch(`${API_BASE_URL}/gerar_clientes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config: configSql,
          quantidade: isCargaDividida ? (Number(qtdPf) + Number(qtdPj)) : quantidade,
          qtd_pf: qtdPf !== '' ? Number(qtdPf) : null,
          qtd_pj: qtdPj !== '' ? Number(qtdPj) : null,
          customizacao: modoManual ? custom : {}
        })
      });
      
      const data = await res.json();
      alert(data.message);
    } catch (err) {
      alert("Erro ao iniciar carga");
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div style={{ padding: '30px', backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <div style={containerStyle}>
        <h2>🚀 Gerador de Cargas: Clientes PLD</h2>
        
        <div style={panelStyle}>
          <h4>📊 Volume da Carga</h4>
          <div style={gridStyle}>
            <div>
              <label>Quantidade Total (50/50):</label>
              <input 
                type="number" 
                value={quantidade} 
                onChange={(e) => setQuantidade(e.target.value)}
                style={inputStyle}
                disabled={isCargaDividida || (modoManual && custom.CIC_CPF.trim() !== "")}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <div>
                <label>Qtd PF (01):</label>
                <input 
                  type="number" 
                  placeholder="Opcional"
                  value={qtdPf} 
                  onChange={(e) => setQtdPf(e.target.value)}
                  style={inputStyle}
                  disabled={modoManual && custom.CIC_CPF.trim() !== ""}
                />
              </div>
              <div>
                <label>Qtd PJ (02):</label>
                <input 
                  type="number" 
                  placeholder="Opcional"
                  value={qtdPj} 
                  onChange={(e) => setQtdPj(e.target.value)}
                  style={inputStyle}
                  disabled={modoManual && custom.CIC_CPF.trim() !== ""}
                />
              </div>
            </div>
          </div>
          {isCargaDividida && (
            <p style={{ color: '#28a745', fontSize: '12px', marginTop: '5px' }}>
              ✅ <strong>Modo Proporcional Ativo:</strong> Total de {Number(qtdPf) + Number(qtdPj)} registros.
            </p>
          )}
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ cursor: 'pointer', fontWeight: 'bold' }}>
            <input 
              type="checkbox" 
              checked={modoManual} 
              onChange={() => {
                setModoManual(!modoManual);
                if (!modoManual === false) setCustom({...custom, CIC_CPF: ''});
              }} 
            /> Customizar Regras de Negócio
          </label>
        </div>

        {modoManual && (
          <div style={{ ...panelStyle, backgroundColor: '#e9ecef' }}>
            <h4>🛠️ Parâmetros Personalizados</h4>
            <div style={gridStyle}>
              <div>
                <label>Tipo Cliente:</label>
                <select 
                  style={inputStyle} 
                  value={custom.CD_TP_CLIENTE} 
                  onChange={(e) => setCustom({...custom, CD_TP_CLIENTE: e.target.value})}
                >
                  <option value="">Aleatório</option>
                  <option value="01">01 - Pessoa Física</option>
                  <option value="02">02 - Pessoa Jurídica</option>
                </select>
              </div>
              
              <div>
                <label>Documento (CPF/CNPJ):</label>
                <input 
                  placeholder="Somente números" 
                  style={inputStyle}
                  value={custom.CIC_CPF}
                  onChange={(e) => setCustom({...custom, CIC_CPF: e.target.value})}
                />
              </div>

              <div>
                <label>Nome Específico:</label>
                <input 
                  placeholder="Aleatório se vazio" 
                  style={inputStyle}
                  value={custom.DE_CLIENTE}
                  onChange={(e) => setCustom({...custom, DE_CLIENTE: e.target.value})}
                />
              </div>

              <div>
                <label>Risco Inerente:</label>
                <input 
                  type="number" 
                  style={inputStyle}
                  value={custom.CD_RISCO_INERENTE}
                  onChange={(e) => setCustom({...custom, CD_RISCO_INERENTE: e.target.value})}
                />
              </div>
            </div>
          </div>
        )}

        <button 
          onClick={handleGerar} 
          disabled={carregando}
          style={buttonStyle(carregando)}
        >
          {carregando ? "Processando 10 Milhões..." : "🚀 Iniciar Carga de Dados"}
        </button>
      </div>
    </div>
  );
}

// Estilos mantidos e otimizados
const containerStyle = { background: 'white', padding: '30px', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', maxWidth: '900px', margin: '0 auto' };
const panelStyle = { background: '#f1f3f5', padding: '20px', borderRadius: '8px', marginBottom: '20px', border: '1px solid #dee2e6' };
const gridStyle = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '10px' };
const inputStyle = { width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #ccc', marginTop: '5px' };
const buttonStyle = (loading) => ({
  width: '100%', padding: '15px', backgroundColor: loading ? '#ccc' : '#007bff', color: 'white', 
  border: 'none', borderRadius: '5px', fontWeight: 'bold', cursor: loading ? 'default' : 'pointer', fontSize: '18px', transition: '0.3s'
});