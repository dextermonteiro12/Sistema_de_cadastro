import React, { useState } from 'react';
import ClientTable from './components/ClientTable'; // Importa o novo componente
import GeneratorForm from './components/GeneratorForm'; // Importa o formulário
import './App.css';

function App() {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);

// NOVA FUNÇÃO: Recebe a quantidade do formulário e faz a chamada à API
  const handleGenerateData = (quantidade) => {
    const URL_API = `http://127.0.0.1:5000/gerar_dados/${quantidade}`; // URL dinâmica
  

  setLoading(true);
    setErro(null); 
    setClientes([]); // Limpa a tabela enquanto carrega

    fetch(URL_API)
      .then(response => {
        if (!response.ok) {
          throw new Error('Falha na resposta da rede ou limite excedido.');
        }
        return response.json();
      })
      .then(data => {
        setClientes(data);
      })
      .catch(error => {
        console.error("Erro ao buscar dados da API:", error);
        setErro("Erro ao carregar dados. Verifique o console e a API Python.");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div className="App">
      <h1>Gerador de Dados Fictícios (React)</h1>
      
      {/* O componente GeneratorForm chama a função handleGenerateData */}
      <GeneratorForm onGenerate={handleGenerateData} />

      <hr style={{ margin: '20px 0' }}/>
      
      {loading && <p>Carregando dados da API Python...</p>}
      {erro && <p style={{ color: 'red' }}>Erro: {erro}</p>}
      
      {/* O componente ClientTable exibe os dados */}
      {!loading && !erro && <ClientTable clientes={clientes} />}
    </div>
  );
}

export default App;
