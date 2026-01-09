import React from 'react';

// --- FUNÇÕES AUXILIARES (Fora do componente para melhor performance) ---

const downloadFile = (data, filename, type) => {
  const blob = new Blob([data], { type: type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const formatarSql = (data, tableName = "clientes_ficticios") => {
  const columns = Object.keys(data).join(", ");
  const values = Object.values(data).map(value => {
    if (typeof value === 'string') return `'${value.replace(/'/g, "''")}'`;
    if (value === null || value === undefined) return 'NULL';
    return value;
  }).join(", ");
  return `INSERT INTO ${tableName} (${columns}) VALUES (${values});`;
};

// --- COMPONENTE PRINCIPAL ---

function ClientTable({ clientes }) {
  if (!clientes || clientes.length === 0) {
    return <p style={{ padding: '20px' }}>Nenhum dado gerado. Clique em "Gerar Dados" para começar!</p>;
  }

  const keys = Object.keys(clientes[0]);

  const formatHeader = (key) => {
    return key.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
  };
  
  const handleDownloadAllJson = () => {
    const jsonContent = JSON.stringify(clientes, null, 2);
    downloadFile(jsonContent, 'clientes_pld.json', 'application/json');
  };

  const handleDownloadAllSql = () => {
    const allSql = clientes.map(cliente => formatarSql(cliente)).join('\n');
    downloadFile(allSql, 'clientes_pld.sql', 'text/plain');
  };

  return (
    <div style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3>Dados Gerados ({clientes.length} Registros)</h3>
            <div>
                <button onClick={handleDownloadAllJson} style={{ marginRight: '10px', cursor: 'pointer' }}>
                    📦 Baixar JSON
                </button>
                <button onClick={handleDownloadAllSql} style={{ cursor: 'pointer' }}>
                    💾 Baixar SQL
                </button>
            </div>
        </div>

        {/* CONTAINER COM SCROLL HORIZONTAL */}
        <div style={{ 
            width: '100%', 
            overflowX: 'auto', 
            border: '1px solid #ddd', 
            borderRadius: '8px',
            boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
        }}> 
            <table style={{ 
                width: '100%', 
                borderCollapse: 'collapse', 
                minWidth: '4000px', // Força a largura para acomodar os 48 campos
                backgroundColor: '#fff'
            }}>
                <thead>
                    <tr style={{ backgroundColor: '#20232a' }}>
                        {keys.map(key => (
                            <th key={key} style={{ 
                                border: '1px solid #444', 
                                padding: '12px 8px', 
                                textAlign: 'left',
                                color: '#61dafb',
                                whiteSpace: 'nowrap'
                            }}>
                                {formatHeader(key)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {clientes.map((cliente, index) => (
                        <tr key={index} style={{ backgroundColor: index % 2 === 0 ? '#f9f9f9' : '#fff' }}>
                            {keys.map(key => (
                                <td key={key} style={{ 
                                    border: '1px solid #ddd', 
                                    padding: '10px 8px',
                                    fontSize: '13px',
                                    whiteSpace: 'nowrap' 
                                }}>
                                    {/* Lógica para exibição de valores (trata null e booleano) */}
                                    {cliente[key] === null ? 'NULL' : cliente[key].toString()}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
        <p style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
            * Role para a direita para visualizar todos os campos PLD.
        </p>
    </div>
  );
}

export default ClientTable;