# 🔐 Isolamento Multi-Usuário - Guia Rápido

## O que foi implementado?

Agora cada usuário logado no sistema tem seu **ambiente isolado**:
- ✅ Apenas bases que o usuário configurou são acessíveis
- ✅ Tentativas de acessar bases de outros usuários retornam erro 403 (Forbidden)
- ✅ Todos os endpoints de dados validam autenticação (JWT) e autorização (config_key)

## Como funciona?

### 1. Login
```javascript
// Frontend: Login.js
const response = await fetch(`${API_URL}/login`, {
  method: 'POST',
  body: JSON.stringify({ username: 'admin', password: '1234' })
});
const { token } = await response.json();
localStorage.setItem('token', token);  // Salva JWT
```

### 2. Configuração
```javascript
// Frontend: Configuracao_v2.js
// Usuário seleciona bases (CORP, EGUARDIAN, etc)
// Sistema salva no AuthDB:
// user_id: "admin" → bases: [
//   { config_key: "corp_abc", nome: "CORP", ... },
//   { config_key: "eguard_xyz", nome: "EGUARDIAN", ... }
// ]
```

### 3. Acesso a Dados
```javascript
// Frontend: Dashboard.js
const response = await fetch(`${API_URL}/api/saude-servidor`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ config_key: 'corp_abc' })
});

// Backend valida:
// 1. JWT válido? → Extrai user_id
// 2. config_key pertence a user_id? → Consulta AuthDB
// 3. ✅ Sim → Retorna dados
//    ❌ Não → Retorna 403 Forbidden
```

## Endpoints Protegidos

**Todos estes endpoints agora requerem JWT e validam ownership:**

| Rota | O que faz |
|------|-----------|
| `/api/saude-servidor` | Saúde do servidor |
| `/api/clientes-pendentes` | Clientes não integrados |
| `/status_dashboard` | Dashboard completo |
| `/api/dashboard/log-pesquisas` | Logs |
| `/api/dashboard/fila-adsvc` | Fila de processamento |
| `/api/dashboard/performance-workers` | Performance |
| `/gerar_clientes` | Geração de clientes |
| `/movimentacoes` | Movimentações |
| `/check_ambiente` | Verifica estrutura |
| `/setup_ambiente` | Cria estrutura |
| `/grpc/gerar_clientes` | Geração via gRPC |

**GraphQL também protegido:**
- `health_check`
- `monitoramento_status`
- `clientes_count`

## Testando

### Cenário: Dois usuários

**User A:**
```bash
# 1. Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "userA", "password": "123"}'
# Resposta: {"token": "eyJhbGc..."}

# 2. User A configurou base CORP (config_key: "corp_a")
# 3. User A acessa seus dados - ✅ OK
curl -X POST http://localhost:5000/api/saude-servidor \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{"config_key": "corp_a"}'
```

**User B:**
```bash
# 1. Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "userB", "password": "456"}'

# 2. User B tenta acessar base de User A - ❌ BLOQUEADO
curl -X POST http://localhost:5000/api/saude-servidor \
  -H "Authorization: Bearer <token_userB>" \
  -d '{"config_key": "corp_a"}'

# Resposta:
# Status: 403 Forbidden
# {"erro": "Você não tem permissão para acessar esta configuração"}
```

## Códigos de Erro

| Código | Quando ocorre |
|--------|---------------|
| **401** | Token JWT ausente ou inválido |
| **403** | Token válido, mas config_key não pertence ao usuário |
| **400** | config_key não informado no request |

## Frontend - Como usar

### Adicione token em todas as requisições:

```javascript
// utils/api.js ou similar
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const apiRequest = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      ...options.headers
    }
  });
  
  // Se 401, redirecionar para login
  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
  
  return response;
};
```

### Exemplo de uso em componente:

```javascript
// Dashboard.js
import { apiRequest } from '../utils/api';

const fetchDashboard = async () => {
  try {
    const response = await apiRequest('/api/saude-servidor', {
      method: 'POST',
      body: JSON.stringify({ config_key: selectedBase.config_key })
    });
    
    if (!response.ok) {
      if (response.status === 403) {
        alert('Você não tem permissão para acessar esta base');
      }
      return;
    }
    
    const data = await response.json();
    setDashboardData(data);
  } catch (error) {
    console.error('Erro:', error);
  }
};
```

## Segurança

### Logs automáticos
Tentativas de acesso não autorizado são logadas:
```
2024-01-15 10:32:45 WARNING Usuário userB tentou acessar config_key corp_a sem autorização
```

### Backend - Como adicionar segurança a nova rota:

```python
# api-gateway/main.py

@app.post("/minha_nova_rota")
async def minha_nova_rota(request: Request, body: dict):
    # Validação em 1 linha!
    user_id, config_key, error = _require_user_config(request, body or {})
    if error:
        return error
    
    # Usuário validado! Prosseguir com lógica
    with get_db_session(config_key) as session:
        # ... sua lógica aqui
        pass
```

## Troubleshooting

### Erro 401 - Não autenticado
**Causa:** Token JWT ausente, expirado ou inválido

**Solução:**
1. Verificar se `localStorage.getItem('token')` retorna valor
2. Fazer login novamente
3. Verificar se header `Authorization: Bearer <token>` está sendo enviado

### Erro 403 - Não autorizado
**Causa:** Token válido, mas config_key não pertence ao usuário

**Solução:**
1. Verificar se config_key está correto
2. Reconfigurar ambiente no wizard de configuração
3. Checar logs do backend para ver tentativa de acesso

### Erro 400 - config_key não informado
**Causa:** Request sem config_key no body/headers

**Solução:**
```javascript
// ❌ Errado
fetch('/api/saude-servidor', {
  method: 'POST',
  body: JSON.stringify({})
});

// ✅ Correto
fetch('/api/saude-servidor', {
  method: 'POST',
  body: JSON.stringify({ config_key: 'corp_abc' })
});
```

### Erro de Conexão SQL Server (Acesso Remoto)
**Erro:** `Named Pipes Provider: Could not open a connection to SQL Server`

**Causa:** SQL Server (que pode estar em outra máquina) não configurado para acesso remoto via TCP/IP

**IMPORTANTE:** O SQL Server pode estar em um servidor diferente do backend!

**Arquitetura:**
```
Cliente → Backend (192.168.0.119) → SQL Server (outra máquina)
```

**Diagnóstico:**

1. **Execute NO SERVIDOR BACKEND** (onde está o Python/FastAPI):
   ```powershell
   cd C:\Users\fmonteiro\Documents\sistema_cadastro
   
   # Teste interativo
   .\teste-conexao-sql.ps1
   
   # OU direto com parâmetros
   .\teste-conexao-sql.ps1 -SqlServer "IP_DO_SQL" -Database "CORP" -Username "usuario" -Password "senha"
   ```

2. **Se o teste falhar, configure NO SERVIDOR SQL:**
   - ✅ Habilitar TCP/IP no SQL Server Configuration Manager
   - ✅ Configurar porta 1433 em TCP/IP Properties
   - ✅ Iniciar SQL Server Browser Service
   - ✅ Liberar porta 1433 no Firewall **DO SERVIDOR SQL**
   - ✅ Habilitar "Allow remote connections" no SSMS
   - ✅ Reiniciar serviço SQL Server

3. **Ver guias completos:**
   - [ARQUITETURA_REDE.md](./ARQUITETURA_REDE.md) - Entenda onde configurar cada coisa
   - [SQL_SERVER_ACESSO_REMOTO.md](./SQL_SERVER_ACESSO_REMOTO.md) - Configuração SQL detalhada

**Correção Aplicada no Código:**
O sistema agora força conexão via TCP/IP adicionando porta `,1433`:
```python
# Antes: servidor = "192.168.0.200"
# Depois: servidor = "192.168.0.200,1433"  ← Força TCP/IP
```

## Próximos Passos

- [ ] Implementar testes automatizados de isolamento
- [ ] Adicionar cache de validação (performance)
- [ ] Adicionar rate limiting por usuário
- [ ] Logs de auditoria (acessos bem-sucedidos)
- [ ] Painel admin para gerenciar permissões

---

**Versão:** 1.0  
**Data:** 2024-01-15  
**Status:** ✅ Implementado

Para mais detalhes técnicos, veja: [ISOLAMENTO_MULTI_USUARIO.md](./ISOLAMENTO_MULTI_USUARIO.md)
