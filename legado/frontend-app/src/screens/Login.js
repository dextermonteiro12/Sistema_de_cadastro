// No seu componente de Login, o envio deve estar assim:
body: JSON.stringify({
  username: username, // Antes estava 'usuario'
  password: password  // Antes estava 'senha'
})

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.119:5000';