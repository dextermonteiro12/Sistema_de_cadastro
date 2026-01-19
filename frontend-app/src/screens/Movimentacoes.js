import React, { useState } from 'react';
import GeneratorForm from '../components/GeneratorForm'; 

const labelStyle = { display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px' };
const inputStyle = { padding: '12px', borderRadius: '6px', border: '1px solid #ddd', width: '100%', fontSize: '15px', boxSizing: 'border-box' };
const btnSide = { width: '100%', marginBottom: '12px', padding: '14px', cursor: 'pointer', backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px', textAlign: 'left', fontWeight: '500', transition: '0.3s', fontSize: '13px' };
const btnActive = { ...btnSide, backgroundColor: '#007bff', color: 'white', borderColor: '#0056b3', boxShadow: '0 4px 12px rgba(0,123,255,0.2)' };

export default function Movimentacoes() {
  const [tipoAtivo, setTipoAtivo] = useState('MOVFIN');
  const [dataReferencia, setDataReferencia] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);
  const [modoData, setModoData] = useState('fixa'); 
  const [busca, setBusca] = useState(''); 

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  // AJUSTE: Agora recebe 'qtd' que vem do GeneratorForm
  const handleGerarCarga = async (qtd) => {
    const configRaw = localStorage.getItem('pld_sql_config');
    if (!configRaw) return alert("⚠️ Configure o Ambiente SQL primeiro!");
    
    const configSql = JSON.parse(configRaw);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/gerar_movimentacoes`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          config: configSql, 
          tipo: tipoAtivo,
          quantidade: qtd,          // <--- ENVIANDO A QUANTIDADE PARA O BACKEND
          data_referencia: dataReferencia,
          modo_data: modoData, 
          busca: busca         
        })
      });

      const data = await res.json();
      if (res.ok) alert(`✅ Sucesso: ${data.message}`);
      else alert(`❌ Erro: ${data.erro || 'Falha ao processar carga'}`);
    } catch (err) { 
      alert("❌ Erro de conexão com o servidor."); 
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '80vh', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: 'white' }}>
      
      {/* Menu Lateral */}
      <div style={{ width: '250px', backgroundColor: '#f8f9fa', padding: '20px', borderRight: '1px solid #ddd' }}>
        <h4 style={{fontSize: '12px', color: '#999', marginBottom: '20px', letterSpacing: '1px'}}>CENÁRIOS ISOLADOS</h4>
        <button onClick={() => setTipoAtivo('MOVFIN')} style={tipoAtivo === 'MOVFIN' ? btnActive : btnSide}>💰 NACIONAL (BRL)</button>
        <button onClick={() => setTipoAtivo('MOVFIN_ME')} style={tipoAtivo === 'MOVFIN_ME' ? btnActive : btnSide}>🌎 ESTRANGEIRA (ME)</button>
        <button onClick={() => setTipoAtivo('MOVFIN_INTERMEDIADOR')} style={tipoAtivo === 'MOVFIN_INTERMEDIADOR' ? btnActive : btnSide}>🤝 INTERMEDIADOR</button>
      </div>

      <div style={{ flex: 1, padding: '30px' }}>
        <h3>Módulo de Movimentação Financeira</h3>
        <p style={{color: '#666', marginBottom: '25px'}}>Cenário ativo: <b>{tipoAtivo.replace('MOVFIN_', '').replace('MOVFIN', 'NACIONAL')}</b></p>
        
        <div style={{ backgroundColor: '#fcfcfc', padding: '25px', borderRadius: '12px', border: '1px solid #eee', marginBottom: '20px' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            <div>
              <label style={labelStyle}>📅 Estratégia de Data:</label>
              <select value={modoData} onChange={(e) => setModoData(e.target.value)} style={inputStyle}>
                <option value="fixa">Data Fixa Selecionada</option>
                <option value="mes_atual">Aleatória (Mês Atual)</option>
                <option value="mes_anterior">Aleatória (Mês Anterior)</option>
              </select>
            </div>

            <div>
              <label style={labelStyle}>🗓️ Data Base:</label>
              <input 
                type="date" 
                value={dataReferencia} 
                disabled={modoData !== 'fixa'}
                onChange={(e) => setDataReferencia(e.target.value)}
                style={{ ...inputStyle, opacity: modoData !== 'fixa' ? 0.5 : 1 }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '25px' }}>
            <label style={labelStyle}>🔎 Filtrar Cliente Específico (Opcional):</label>
            <input 
              type="text" 
              placeholder="Digite o CPF, ID ou Nome (DE_CLIENTE)..." 
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              style={inputStyle}
            />
          </div>
          
          <div style={{ padding: '15px', backgroundColor: '#fff4e5', borderLeft: '4px solid #ffa94d', borderRadius: '4px', marginBottom: '20px' }}>
            <p style={{ fontSize: '13px', color: '#856404', margin: 0 }}>
              <strong>Lógica:</strong> {modoData === 'fixa' ? `Data fixa: ${dataReferencia}` : `Sorteio no ${modoData.replace('_', ' ')}`}
            </p>
          </div>
          
          <hr style={{ border: '0.5px solid #f0f0f0', margin: '20px 0' }} />
          
          <div style={{ opacity: loading ? 0.5 : 1, pointerEvents: loading ? 'none' : 'auto' }}>
              <GeneratorForm onGenerate={handleGerarCarga} labelBtn={loading ? "Processando..." : `Gerar Movimentações ${tipoAtivo}`} />
          </div>
        </div>
      </div>
    </div>
  );
}