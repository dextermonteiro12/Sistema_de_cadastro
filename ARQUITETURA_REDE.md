# 🌐 Arquitetura de Rede - Sistema PLD

## 📋 Cenário de Implantação

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  CLIENTE        │         │  SERVIDOR       │         │  SERVIDOR SQL   │
│  (Você)         │────────▶│  BACKEND        │────────▶│                 │
│                 │         │                 │         │                 │
│  172.20.200.67  │         │  192.168.0.119  │         │  192.168.0.XXX  │
│                 │         │                 │         │                 │
│  Browser        │         │  FastAPI :5000  │         │  SQL Server     │
│  React :3000    │         │  React :3000    │         │  Porta :1433    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
      HTTP                       SQL                        TCP/IP
```

## 🔍 Entendendo o Fluxo

### 1. Cliente → Backend (HTTP)
**O que acontece:**
- Usuário acessa `http://192.168.0.119:3000` (frontend React)
- Frontend faz requisições para `http://192.168.0.119:5000/api/*` (backend FastAPI)
- Envia JWT token + config_key nas requisições

**Firewalls necessários:**
```powershell
# NO SERVIDOR BACKEND (192.168.0.119)
New-NetFirewallRule -DisplayName "PLD Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "PLD Backend" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### 2. Backend → SQL Server (SQL)
**O que acontece:**
- Backend (rodando em 192.168.0.119) precisa conectar ao SQL Server
- SQL Server pode estar em **OUTRA máquina** (ex: 192.168.0.200, 192.168.1.50, etc)
- Conexão usa protocolo **TCP/IP na porta 1433**

**Firewalls necessários:**
```powershell
# NO SERVIDOR SQL (192.168.0.XXX - onde está o SQL Server)
New-NetFirewallRule -DisplayName "SQL Server" -Direction Inbound -LocalPort 1433 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "SQL Browser" -Direction Inbound -LocalPort 1434 -Protocol UDP -Action Allow
```

**⚠️ IMPORTANTE:** As configurações SQL devem ser feitas **NO SERVIDOR SQL**, não no servidor backend!

## 🧪 Testando Conectividade

### Passo 1: Identificar o Servidor SQL

**No seu XML (Advice.xml), procure:**
```xml
<Servidor>192.168.0.200</Servidor>  <!-- Este é o IP do SQL Server -->
<Usuario>sa</Usuario>
<Senha>MinHaSenHa</Senha>
```

### Passo 2: Testar do Servidor Backend

**IMPORTANTE:** O teste deve ser feito **DO SERVIDOR BACKEND** (192.168.0.119), pois é ele quem precisa acessar o SQL!

**Execute NO SERVIDOR BACKEND (192.168.0.119):**

```powershell
cd C:\Users\fmonteiro\Documents\sistema_cadastro

# Teste interativo - vai pedir servidor, usuário e senha
.\teste-conexao-sql.ps1

# OU com parâmetros diretos
.\teste-conexao-sql.ps1 -SqlServer "192.168.0.200" -Database "CORP" -Username "sa" -Password "SuaSenha"
```

**O que o script testa:**
1. ✅ Ping no servidor SQL
2. ✅ Porta 1433 aberta
3. ✅ Conexão SQL sem porta explícita
4. ✅ Conexão SQL com porta `,1433` (forçando TCP/IP)
5. ✅ Permissões do usuário

### Passo 3: Configurar SQL Server Remoto

**Execute estes comandos NO SERVIDOR SQL (não no backend!):**

#### 3.1 Habilitar TCP/IP

1. Abra **SQL Server Configuration Manager** no servidor SQL
2. Navegue: `SQL Server Network Configuration` → `Protocols for MSSQLSERVER`
3. Clique direito em **TCP/IP** → **Enable**
4. Duplo clique em **TCP/IP** → Aba **IP Addresses**
5. Role até **IPAll**:
   - TCP Dynamic Ports: (deixe vazio)
   - TCP Port: **1433**

#### 3.2 Reiniciar SQL Server

```powershell
# NO SERVIDOR SQL
net stop MSSQLSERVER
net start MSSQLSERVER
```

#### 3.3 Liberar Firewall

```powershell
# NO SERVIDOR SQL
New-NetFirewallRule -DisplayName "SQL Server 1433" -Direction Inbound -LocalPort 1433 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "SQL Browser 1434" -Direction Inbound -LocalPort 1434 -Protocol UDP -Action Allow
```

#### 3.4 Habilitar Conexões Remotas

**SQL Server Management Studio (NO SERVIDOR SQL):**
1. Conecte ao servidor localmente
2. Botão direito no servidor → **Properties**
3. Página **Connections**
4. Marque: ✅ **"Allow remote connections to this server"**
5. Remote query timeout: `600`

#### 3.5 Habilitar Mixed Mode (SQL + Windows Auth)

**SSMS (NO SERVIDOR SQL):**
1. Botão direito no servidor → **Properties**
2. Página **Security**
3. Server authentication: **SQL Server and Windows Authentication mode**
4. OK → **Reiniciar SQL Server**

## 📝 Checklist Completo

### No SERVIDOR BACKEND (192.168.0.119):

- [ ] Firewall liberado para porta 5000 (backend)
- [ ] Firewall liberado para porta 3000 (frontend)
- [ ] Código atualizado com força TCP/IP (`,1433`)
- [ ] Teste de conexão executado: `.\teste-conexao-sql.ps1`

### No SERVIDOR SQL (192.168.0.XXX):

- [ ] Serviço SQL Server rodando
- [ ] Serviço SQL Browser rodando
- [ ] TCP/IP habilitado no Configuration Manager
- [ ] Porta 1433 configurada no TCP/IP Properties
- [ ] Firewall liberado para porta 1433 (TCP)
- [ ] Firewall liberado para porta 1434 (UDP)
- [ ] "Allow remote connections" habilitado
- [ ] Mixed Mode habilitado (SQL + Windows Auth)
- [ ] Usuário criado e com permissões

### No CLIENTE (seu computador):

- [ ] Consegue acessar `http://192.168.0.119:3000`
- [ ] Consegue fazer login no sistema
- [ ] Consegue ler o XML e ver as bases
- [ ] Consegue conectar às bases

## 🚨 Troubleshooting por Máquina

### Erro: "Cannot connect to 192.168.0.119:5000"

**Problema:** Cliente não alcança o backend

**Onde resolver:** NO SERVIDOR BACKEND
```powershell
# Verificar se backend está rodando
netstat -an | findstr ":5000"

# Verificar firewall
Get-NetFirewallRule | Where-Object {$_.LocalPort -eq 5000}

# Liberar se necessário
New-NetFirewallRule -DisplayName "PLD Backend" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Erro: "Could not open connection to SQL Server [64]"

**Problema:** Backend não alcança o SQL Server

**Onde resolver:** NO SERVIDOR SQL
```powershell
# Verificar se SQL está rodando
Get-Service MSSQLSERVER

# Verificar se porta 1433 está escutando
netstat -an | findstr ":1433"

# Verificar firewall
Get-NetFirewallRule | Where-Object {$_.LocalPort -eq 1433}
```

**Teste DO SERVIDOR BACKEND:**
```powershell
# NO SERVIDOR BACKEND, testar conexão com SQL Server
Test-NetConnection -ComputerName 192.168.0.200 -Port 1433
```

### Erro: "Login failed for user 'usuario'"

**Problema:** Credenciais incorretas ou sem permissão

**Onde resolver:** NO SERVIDOR SQL (via SSMS)
```sql
-- Verificar se usuário existe
SELECT name, is_disabled FROM sys.server_principals WHERE name = 'seu_usuario'

-- Criar usuário
CREATE LOGIN [pld_user] WITH PASSWORD = 'Senha@123'

-- Dar permissões
USE [CORP]
CREATE USER [pld_user] FOR LOGIN [pld_user]
ALTER ROLE db_datareader ADD MEMBER [pld_user]
ALTER ROLE db_datawriter ADD MEMBER [pld_user]
```

## 🔧 Scripts Úteis

### Testar Conectividade Completa

```powershell
# Execute NO SERVIDOR BACKEND
cd C:\Users\fmonteiro\Documents\sistema_cadastro

# Teste SQL
.\teste-conexao-sql.ps1 -SqlServer "IP_DO_SQL" -Database "CORP" -Username "usuario" -Password "senha"

# Diagnóstico acesso externo
.\diagnostico-acesso-externo.bat
```

### Verificar Logs Backend

```powershell
# Logs do backend
Get-Content C:\Users\fmonteiro\Documents\sistema_cadastro\logs\backend.log -Tail 50 -Wait
```

## 📚 Documentos Relacionados

- **[SQL_SERVER_ACESSO_REMOTO.md](./SQL_SERVER_ACESSO_REMOTO.md)** - Configuração detalhada SQL Server
- **[CONFIGURACAO_ACESSO_EXTERNO.md](./CONFIGURACAO_ACESSO_EXTERNO.md)** - Configuração frontend/backend
- **[README_ISOLAMENTO.md](./README_ISOLAMENTO.md)** - Sistema multi-usuário

---

**Versão:** 1.0  
**Última atualização:** 2024-02-21  
**Testado em:** Windows Server 2019, SQL Server 2017/2019
