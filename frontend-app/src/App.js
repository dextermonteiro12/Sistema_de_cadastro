import React, { useState, useEffect } from 'react';
import './App.css'; 

function App() {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const URL_API = 'http://127.0.0.1:5000/gerar_dados/10'; // Busca 10 registros

  useEffect(() => {
    // Função para buscar os dados da API Python
    fetch(URL_API)
      .then(response => response.json())
      .then(data => {
        setClientes(data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Erro ao buscar dados da API:", error);
        setLoading(false);
      });
  }, []); // O array vazio garante que o 'fetch' rode apenas uma vez (ao carregar o componente)

  return (
    <div className="App">
      <h1>Gerador de Dados Fictícios (React Frontend)</h1>
      {loading ? (
        <p>Carregando dados da API Python...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>CPF Fictício</th>
              <th>Movimentação Sim.</th>
            </tr>
          </thead>
          <tbody>
            {clientes.map((cliente) => (
              <tr key={cliente.id_cliente}>
                <td>{cliente.id_cliente.substring(0, 8)}...</td>
                <td>{cliente.nome}</td>
                <td>{cliente.cpf}</td>
                <td>R$ {cliente.movimentacao_simulada.toFixed(2).replace('.', ',')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}


export default App;
