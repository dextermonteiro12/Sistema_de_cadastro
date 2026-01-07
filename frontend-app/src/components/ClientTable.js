import React from 'react';

// Função auxiliar para formatar em JSON
const formatarJson = (data) => {
  return JSON.stringify(data, null, 2); // Usa indentação 2 para leitura fácil
};
// Função auxiliar para formatar em SQL INSERT (com base na estrutura atual da API)
const formatarSql = (data, tableName = "clientes_ficticios") => {
  let sqlScripts = [];

  // Pega apenas as chaves do objeto principal (que contêm os dados do cliente)
  const columns = Object.keys(data);
  
  // Mapeia os valores, garantindo aspas em strings e formato correto para data/UUID
  const values = Object.values(data).map(value => {
    if (typeof value === 'string') {
      // Adiciona aspas em strings, tratando aspas simples dentro da string
      return `'${value.replace(/'/g, "''")}'`;
    }
    if (value === null || value === undefined) {
      return 'NULL';
    }
    return value; // Números e outros tipos
  });

  const colsStr = columns.join(", ");
  const valsStr = values.join(", ");
  
  sqlScripts.push(`INSERT INTO ${tableName} (${colsStr}) VALUES (${valsStr});`);
  
  return sqlScripts.join('\n'); // Retorna uma string com o script SQL
};

// Função principal para criar e iniciar o download
const downloadFile = (data, filename, type) => {
  const blob = new Blob([data], { type: type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url); // Libera o recurso
};


function ClientTable({ clientes }) {
  if (clientes.length === 0) {
    return <p>Nenhum dado gerado. Clique em "Gerar Dados" para começar!</p>;
  }

  // Captura as chaves do primeiro objeto para usar como cabeçalhos da tabela
  // Isso torna a tabela dinâmica para qualquer campo que o backend esteja enviando.
  const keys = Object.keys(clientes[0]);

  // Função para formatar o nome da coluna (ex: id_cliente -> ID Cliente)
  const formatHeader = (key) => {
      // Substitui '_' por espaço e capitaliza a primeira letra de cada palavra
      return key.split('_').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
  };
  
  // Lógica para download de TODOS os clientes em JSON (usando o formato da API)
  const handleDownloadAllJson = () => {
    const jsonContent = JSON.stringify(clientes, null, 2);
    downloadFile(jsonContent, 'clientes_ficticios.json', 'application/json');
  };

  // Para fins de teste, criamos uma função SQL simples aqui
  const formatarSql = (data, tableName = "clientes_ficticios") => {
      const columns = Object.keys(data).join(", ");
      // Mapeamento simples de valores para SQL (necessário tratar strings e datas com aspas)
      const values = Object.values(data).map(value => {
          if (typeof value === 'string' || value instanceof Date) return `'${value}'`;
          return value;
      }).join(", ");
      return `INSERT INTO ${tableName} (${columns}) VALUES (${values});`;
  };
  
  // Lógica para download de TODOS os clientes em SQL
  const handleDownloadAllSql = () => {
      const allSql = clientes.map(cliente => formatarSql(cliente)).join('\n');
      downloadFile(allSql, 'clientes_ficticios.sql', 'text/plain');
  };

  return (
    <div>
        <h3>Dados Gerados ({clientes.length} Registros)</h3>
        
        <div style={{ margin: '10px 0', paddingBottom: '10px' }}>
            <h4>Opções de Download</h4>
            <button onClick={handleDownloadAllJson} style={{ marginRight: '10px' }}>
                Baixar Todos como JSON
            </button>
            <button onClick={handleDownloadAllSql}>
                Baixar Todos como SQL
            </button>
        </div>

        <div style={{ overflowX: 'auto' }}> {/* Adiciona barra de rolagem horizontal se necessário */}
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr>
                        {/* Cria os cabeçalhos da tabela dinamicamente */}
                        {keys.map(key => (
                            <th key={key} style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>
                                {formatHeader(key)}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {clientes.map((cliente, index) => (
                        <tr key={index}>
                            {/* Preenche as células com os valores correspondentes */}
                            {keys.map(key => (
                                <td key={key} style={{ border: '1px solid #ddd', padding: '8px' }}>
                                    {/* Formatação simples para números grandes (UUIDs) */}
                                    {key === 'id_cliente' && typeof cliente[key] === 'string' ? `${cliente[key].substring(0, 8)}...` : cliente[key]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
  );
}

// ... (resto do código da função ClientTable)

export default ClientTable; // <-- DEVE TER 'export default'