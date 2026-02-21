import React, { useState, useContext, useRef, useEffect } from 'react';
import { ConfigContext } from '../context/ConfigContext';
import { apiService } from '../services/apiService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Clientes() {
  const { configKey } = useContext(ConfigContext);
  const [quantidade, setQuantidade] = useState(10);
  const [qtdPf, setQtdPf] = useState("");
  const [qtdPj, setQtdPj] = useState("");
  const [modoManual, setModoManual] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [resultado, setResultado] = useState(null);

  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState(null);

  const eventSourceRef = useRef(null);
  const pollRef = useRef(null);

  const [custom, setCustom] = useState({
    CD_TP_CLIENTE: "",
    DE_CLIENTE: "",
    CIC_CPF: "",
    DT_DESATIVACAO: "1900-01-01",
    CD_RISCO_INERENTE: 3,
    FL_GRANDES_FORTUNAS: 1,
    CD_NAT_JURIDICA: ""
  });

  const isCargaDividida = qtdPf !== "" || qtdPj !== "";

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = (id) => {
    if (pollRef.current) clearInterval(pollRef.current);

    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/grpc/job_status/${id}`);
        const data = await res.json();
        setJobStatus(data);
        if (["done", "error", "not_found", "erro"].includes(data.status)) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch (e) {
        setJobStatus({ status: "erro", percent: 0, inserted: 0, message: e.message });
      }
    };

    fetchStatus();
    pollRef.current = setInterval(fetchStatus, 2000);
  };

  const startSSE = (id) => {
    if (eventSourceRef.current) eventSourceRef.current.close();

    try {
      const es = new EventSource(`${API_BASE_URL}/grpc/job_status/stream/${id}`);
      eventSourceRef.current = es;

      es.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          setJobStatus(data);
          if (["done", "error", "not_found", "erro"].includes(data.status)) {
            es.close();
          }
        } catch {
          // fallback to polling
          es.close();
          startPolling(id);
        }
      };

      es.onerror = () => {
        es.close();
        startPolling(id);
      };
    } catch {
      startPolling(id);
    }
  };

  const handleGerar = async () => {
    const baseAtiva = apiService.carregarBaseAtiva();
    if (!configKey) {
      alert("Configuracao nao ativa. Acesse Configuracao primeiro.");
      return;
    }
    if (!baseAtiva?.banco) {
      alert("Base ativa não selecionada. Volte em Configuração/Home e selecione uma base.");
      return;
    }

    setCarregando(true);
    setJobStatus(null);
    setJobId("");

    try {
      const res = await fetch(`${API_BASE_URL}/grpc/gerar_clientes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config_key: configKey,
          quantidade: isCargaDividida ? (Number(qtdPf) + Number(qtdPj)) : Number(quantidade),
          qtd_pf: qtdPf !== "" ? Number(qtdPf) : 0,
          qtd_pj: qtdPj !== "" ? Number(qtdPj) : 0
        })
      });

      const data = await res.json();

      if (data.status === "accepted" || data.status === "ok") {
        setResultado({ tipo: "sucesso", mensagem: data.message || "Job iniciado" });
        setJobId(data.job_id || "");
        if (data.job_id) startSSE(data.job_id);
      } else {
        setResultado({ tipo: "erro", mensagem: data.erro || data.message || "Erro ao gerar clientes" });
      }
    } catch (err) {
      setResultado({ tipo: "erro", mensagem: err.message });
    } finally {
      setCarregando(false);
    }
  };

  const percent = jobStatus?.percent ?? 0;

  return (
    <div style={{ padding: "30px", backgroundColor: "#f8f9fa", minHeight: "100vh" }}>
      <div style={containerStyle}>
        <h2>Gerador de Cargas: Clientes PLD</h2>

        {!configKey && (
          <div style={{ backgroundColor: "#f8d7da", color: "#721c24", padding: "15px", borderRadius: "5px", marginBottom: "20px" }}>
            Configuracao inativa. Acesse a tela de Configuracao para conectar ao banco.
          </div>
        )}

        <div style={panelStyle}>
          <h4>Volume da Carga</h4>
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
            <div style={{ display: "flex", gap: "10px" }}>
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
            <p style={{ color: "#28a745", fontSize: "12px", marginTop: "5px" }}>
              Modo proporcional ativo: Total de {Number(qtdPf) + Number(qtdPj)} registros.
            </p>
          )}
        </div>

        <div style={{ marginBottom: "20px" }}>
          <label style={{ cursor: "pointer", fontWeight: "bold" }}>
            <input
              type="checkbox"
              checked={modoManual}
              onChange={() => setModoManual(!modoManual)}
            /> Customizar regras de negocio
          </label>
        </div>

        {modoManual && (
          <div style={{ ...panelStyle, backgroundColor: "#e9ecef" }}>
            <h4>Parametros Personalizados</h4>
            <div style={gridStyle}>
              <div>
                <label>Tipo Cliente:</label>
                <select
                  style={inputStyle}
                  value={custom.CD_TP_CLIENTE}
                  onChange={(e) => setCustom({ ...custom, CD_TP_CLIENTE: e.target.value })}
                >
                  <option value="">Aleatorio</option>
                  <option value="01">01 - Pessoa Fisica</option>
                  <option value="02">02 - Pessoa Juridica</option>
                </select>
              </div>

              <div>
                <label>Documento (CPF/CNPJ):</label>
                <input
                  placeholder="Somente numeros"
                  style={inputStyle}
                  value={custom.CIC_CPF}
                  onChange={(e) => setCustom({ ...custom, CIC_CPF: e.target.value })}
                />
              </div>

              <div>
                <label>Nome Especifico:</label>
                <input
                  placeholder="Aleatorio se vazio"
                  style={inputStyle}
                  value={custom.DE_CLIENTE}
                  onChange={(e) => setCustom({ ...custom, DE_CLIENTE: e.target.value })}
                />
              </div>

              <div>
                <label>Risco Inerente:</label>
                <input
                  type="number"
                  style={inputStyle}
                  value={custom.CD_RISCO_INERENTE}
                  onChange={(e) => setCustom({ ...custom, CD_RISCO_INERENTE: e.target.value })}
                />
              </div>
            </div>
          </div>
        )}

        <button
          onClick={handleGerar}
          disabled={carregando || !configKey}
          style={buttonStyle(carregando || !configKey)}
        >
          {carregando ? "Processando..." : "Iniciar Carga de Dados (gRPC)"}
        </button>

        {jobId && (
          <div style={{ marginTop: 20 }}>
            <div style={{ fontSize: 12, color: "#64748b" }}>Job ID: {jobId}</div>
            <div style={{ marginTop: 8, height: 12, background: "#e2e8f0", borderRadius: 6 }}>
              <div style={{ height: 12, width: `${percent}%`, background: "#10b981", borderRadius: 6 }} />
            </div>
            <div style={{ marginTop: 8, fontSize: 12 }}>
              Status: {jobStatus?.status || "pending"} | {percent}% | Inseridos: {jobStatus?.inserted ?? 0}
            </div>
            <div style={{ fontSize: 12, color: "#64748b" }}>{jobStatus?.message || ""}</div>
          </div>
        )}

        {resultado && (
          <div style={{ marginTop: 12, fontSize: 12, color: resultado.tipo === "sucesso" ? "#16a34a" : "#dc2626" }}>
            {resultado.mensagem}
          </div>
        )}
      </div>
    </div>
  );
}

const containerStyle = { background: "white", padding: "30px", borderRadius: "12px", boxShadow: "0 4px 20px rgba(0,0,0,0.1)", maxWidth: "900px", margin: "0 auto" };
const panelStyle = { background: "#f1f3f5", padding: "20px", borderRadius: "8px", marginBottom: "20px", border: "1px solid #dee2e6" };
const gridStyle = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px", marginTop: "10px" };
const inputStyle = { width: "100%", padding: "10px", borderRadius: "5px", border: "1px solid #ccc", marginTop: "5px" };
const buttonStyle = (disabled) => ({
  width: "100%", padding: "15px", backgroundColor: disabled ? "#ccc" : "#007bff", color: "white",
  border: "none", borderRadius: "5px", fontWeight: "bold", cursor: disabled ? "default" : "pointer", fontSize: "18px", transition: "0.3s"
});
