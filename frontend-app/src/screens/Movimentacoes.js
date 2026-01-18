import React, { useState } from 'react';
import GeneratorForm from '../components/GeneratorForm'; 
import ClientTable from '../components/ClientTable'; 

export default function Movimentacoes() {
  const [tipoAtivo, setTipoAtivo] = useState('MOVFIN');
  const [dataReferencia, setDataReferencia] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false); // Estado para feedback de processamento
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  const handleGerarCarga = async () => {
    // 1. Busca a configuração do SQL
    const configRaw = localStorage.getItem('pld_sql_config');
    if (!configRaw) return alert("⚠️ Configure o Ambiente SQL primeiro!");
    
    const configSql = JSON.parse(configRaw);
    setLoading(true);

    try {
      // Chamada para a rota que agora processa os cenários isolados
      const res = await fetch(`${API_BASE_URL}/gerar_movimentacoes`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          config: configSql, 
          tipo: tipoAtivo, // 'MOVFIN', 'MOVFIN_ME' ou 'MOVFIN_INTERMEDIADOR'
          data_referencia: dataReferencia 
        })
      });

      const data = await res.json();
      
      if (res.ok) {
        alert(`✅ Processamento iniciado: ${data.message}`);
      } else {
        alert(`❌ Erro: ${data.erro || 'Falha ao processar carga'}`);
      }
    } catch (err) { 
      alert("❌ Erro de conexão com o servidor."); 
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '80vh', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: 'white' }}>
      
      {/* Menu Lateral de Tipos Financeiros - Segregação de Cenários */}
      <div style={{ width: '250px', backgroundColor: '#f8f9fa', padding: '20px', borderRight: '1px solid #ddd' }}>
        <h4 style={{fontSize: '12px', color: '#999', marginBottom: '20px', letterSpacing: '1px'}}>CENÁRIOS ISOLADOS</h4>
        <button onClick={() => setTipoAtivo('MOVFIN')} style={tipoAtivo === 'MOVFIN' ? btnActive : btnSide}>💰 NACIONAL (BRL)</button>
        <button onClick={() => setTipoAtivo('MOVFIN_ME')} style={tipoAtivo === 'MOVFIN_ME' ? btnActive : btnSide}>🌎 ESTRANGEIRA (ME)</button>
        <button onClick={() => setTipoAtivo('MOVFIN_INTERMEDIADOR')} style={tipoAtivo === 'MOVFIN_INTERMEDIADOR' ? btnActive : btnSide}>🤝 INTERMEDIADOR</button>
      </div>

      {/* Área de Configuração e Disparo */}
      <div style={{ flex: 1, padding: '30px' }}>
        <h3 style={{marginBottom: '5px'}}>Módulo de Movimentação Financeira</h3>
        <p style={{color: '#666', marginBottom: '25px'}}>Cenário ativo: <b style={{color: '#007bff'}}>{tipoAtivo.replace('MOVFIN_', '').replace('MOVFIN', 'NACIONAL')}</b></p>
        
        <div style={{ backgroundColor: '#fcfcfc', padding: '25px', borderRadius: '12px', border: '1px solid #eee', marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold', fontSize: '14px' }}>
            📅 Data de Referência do Lançamento:
          </label>
          <input 
            type="date" 
            value={dataReferencia} 
            onChange={(e) => setDataReferencia(e.target.value)}
            style={{ padding: '12px', borderRadius: '6px', border: '1px solid #ddd', width: '220px', marginBottom: '20px', fontSize: '16px' }}
          />
          
          <div style={{ padding: '15px', backgroundColor: '#fff4e5', borderLeft: '4px solid #ffa94d', borderRadius: '4px', marginBottom: '20px' }}>
            <p style={{ fontSize: '13px', color: '#856404', margin: 0 }}>
              <strong>Atenção:</strong> Esta ação percorrerá a base de clientes e gerará <b>débitos e créditos</b> automáticos para o cenário selecionado.
            </p>
          </div>
          
          <hr style={{ border: '0.5px solid #f0f0f0', margin: '20px 0' }} />
          
          {/* O GeneratorForm aqui servirá para disparar o processo, 
              mas o backend agora ignora a "quantidade" em favor dos clientes existentes */}
          <div style={{ opacity: loading ? 0.5 : 1, pointerEvents: loading ? 'none' : 'auto' }}>
             <GeneratorForm onGenerate={handleGerarCarga} labelBtn={`Gerar Movimentações ${tipoAtivo}`} />
          </div>
        </div>
        
        {/* Placeholder para feedback de execução */}
        <div style={{marginTop: '20px', padding: '20px', border: '1px dashed #ccc', borderRadius: '8px', textAlign: 'center', color: '#999'}}>
            {loading ? "⚙️ O servidor está processando os lotes no banco de dados..." : "Aguardando comando para nova carga financeira."}
        </div>
      </div>
    </div>
  );
}

// Estilos locais mantidos e otimizados
const btnSide = { width: '100%', marginBottom: '12px', padding: '14px', cursor: 'pointer', backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '6px', textAlign: 'left', fontWeight: '500', transition: '0.3s', fontSize: '13px' };
const btnActive = { ...btnSide, backgroundColor: '#007bff', color: 'white', borderColor: '#0056b3', boxShadow: '0 4px 12px rgba(0,123,255,0.2)' };