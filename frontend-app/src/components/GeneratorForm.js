import React, { useState } from 'react';

function GeneratorForm({ onGenerate }) {
  const [quantidade, setQuantidade] = useState(10); // Valor inicial: 10

  const handleSubmit = (event) => {
    event.preventDefault(); // Impede o recarregamento padrão da página
    onGenerate(quantidade); // Chama a função passada pelo App.js com a quantidade
  };

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="quantidade">
        Quantos registros gerar (máx. 100):
      </label>
      <input
        id="quantidade"
        type="number"
        min="1"
        max="100"
        value={quantidade}
        onChange={(e) => setQuantidade(e.target.value)} // Atualiza o estado
        style={{ margin: '0 10px', padding: '5px', width: '80px' }}
      />
      <button type="submit">Gerar Dados</button>
    </form>
  );
}

export default GeneratorForm;