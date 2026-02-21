# 🔧 Configuração SQL Server para Acesso Remoto

## 🚨 Problema

Erro ao conectar de cliente remoto:
```
[08001] [Microsoft][ODBC Driver 17 for SQL Server]Named Pipes Provider: Could not open a connection to SQL Server [64]
Login timeout expired
Server is not found or not accessible
```

## ✅ Solução Completa

### 1️⃣ Habilitar TCP/IP no SQL Server

**SQL Server Configuration Manager:**

1. **Abrir SQL Server Configuration Manager**
   - Pressione `Win + R`
   - Digite: `SQLServerManager15.msc` (SQL 2019) ou `SQLServerManager14.msc` (SQL 2017)
   - OU busque: "SQL Server Configuration Manager" no menu Iniciar

2. **Habilitar TCP/IP**
   ```
   SQL Server Network Configuration
   └── Protocols for MSSQLSERVER
       └── TCP/IP → Botão direito → Enable
   ```

3. **Configurar Porta TCP/IP**
   - Clique duplo em **TCP/IP**
   - Aba **IP Addresses**
   - Role até a última seção: **IPAll**
   - Configure:
     ```
     TCP Dynamic Ports: (deixe vazio)
     TCP Port: 1433
     ```
   - Clique **OK**

4. **Reiniciar SQL Server**
   ```powershell
   # PowerShell como Administrador
   net stop MSSQLSERVER
   net start MSSQLSERVER
   ```

### 2️⃣ Habilitar SQL Server Browser

O SQL Server Browser permite que clientes encontrem instâncias SQL Server na rede.

```powershell
# PowerShell como Administrador

# Configurar para iniciar automaticamente
sc config SQLBrowser start= auto

# Iniciar serviço
net start SQLBrowser
```

### 3️⃣ Configurar Firewall do Windows

```powershell
# PowerShell como Administrador

# Regra para SQL Server (porta TCP 1433)
New-NetFirewallRule -DisplayName "SQL Server TCP 1433" `
  -Direction Inbound `
  -LocalPort 1433 `
  -Protocol TCP `
  -Action Allow

# Regra para SQL Browser (porta UDP 1434)
New-NetFirewallRule -DisplayName "SQL Server Browser UDP 1434" `
  -Direction Inbound `
  -LocalPort 1434 `
  -Protocol UDP `
  -Action Allow
```

**OU manualmente:**

1. Painel de Controle → Firewall do Windows → Configurações Avançadas
2. Regras de Entrada → Nova Regra
3. Tipo: Porta
4. Protocolo: TCP, Porta: 1433
5. Ação: Permitir conexão
6. Perfil: Domínio, Privado, Público (marque todos)
7. Nome: "SQL Server TCP 1433"

### 4️⃣ Habilitar Conexões Remotas no SQL Server

**SQL Server Management Studio (SSMS):**

1. Conecte ao servidor
2. Botão direito no nome do servidor (topo) → **Properties**
3. Página **Connections**
4. Marque: ✅ **"Allow remote connections to this server"**
5. Remote query timeout: `600` (10 minutos)
6. Clique **OK**

### 5️⃣ Verificar Autenticação SQL Server

**SSMS:**

1. Botão direito no servidor → **Properties**
2. Página **Security**
3. Server authentication: **SQL Server and Windows Authentication mode** (Mixed Mode)
4. Clique **OK**
5. **Reiniciar SQL Server** (necessário para aplicar)

### 6️⃣ Verificar Usuário e Permissões

**SSMS:**

```sql
-- Verificar se usuário existe
SELECT name, type_desc, is_disabled 
FROM sys.server_principals 
WHERE name = 'seu_usuario'

-- Verificar permissões no banco
USE [CORP]
GO
SELECT 
    dp.name AS UserName,
    dp.type_desc AS UserType,
    o.permission_name AS Permission,
    o.state_desc AS PermissionState
FROM sys.database_permissions o
LEFT JOIN sys.database_principals dp ON o.grantee_principal_id = dp.principal_id
WHERE dp.name = 'seu_usuario'

-- Criar usuário se não existir
CREATE LOGIN [pld_user] WITH PASSWORD = 'Senha@Forte123'
GO
USE [CORP]
GO
CREATE USER [pld_user] FOR LOGIN [pld_user]
GO
ALTER ROLE db_datareader ADD MEMBER [pld_user]
ALTER ROLE db_datawriter ADD MEMBER [pld_user]
GO
```

## 🧪 Testando a Configuração

### Teste 1: Porta Aberta

```powershell
# PowerShell no computador REMOTO
Test-NetConnection -ComputerName 192.168.0.119 -Port 1433

# Resultado esperado:
# TcpTestSucceeded : True
```

### Teste 2: Telnet

```cmd
# CMD no computador REMOTO
telnet 192.168.0.119 1433

# Se conectar: tela preta = sucesso
# Se erro: "Não foi possível abrir conexão"
```

### Teste 3: SQL Server Management Studio

```
Server name: 192.168.0.119,1433
Authentication: SQL Server Authentication
Login: pld_user
Password: ***
```

### Teste 4: PowerShell Connection Test

```powershell
$server = "192.168.0.119,1433"
$database = "CORP"
$username = "pld_user"
$password = "Senha@Forte123"

$connectionString = "Server=$server;Database=$database;User Id=$username;Password=$password;TrustServerCertificate=True"
$connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)

try {
    $connection.Open()
    Write-Host "✅ CONEXÃO ESTABELECIDA COM SUCESSO!" -ForegroundColor Green
    $connection.Close()
} catch {
    Write-Host "❌ ERRO AO CONECTAR: $_" -ForegroundColor Red
}
```

### Teste 5: Python/SQLAlchemy

```python
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

server = "192.168.0.119,1433"
database = "CORP"
username = "pld_user"
password = "Senha@Forte123"
driver = "ODBC Driver 17 for SQL Server"

encoded_driver = quote_plus(driver)

connection_url = (
    f"mssql+pyodbc://{username}:{password}@"
    f"{server}/{database}"
    f"?driver={encoded_driver}&TrustServerCertificate=yes"
)

engine = create_engine(connection_url, connect_args={'timeout': 10})

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT @@VERSION"))
        print("✅ CONEXÃO OK!")
        print(result.fetchone()[0])
except Exception as e:
    print(f"❌ ERRO: {e}")
```

## 📋 Checklist Completo

Execute o script de diagnóstico:
```cmd
cd C:\Users\fmonteiro\Documents\sistema_cadastro
diagnostico-sqlserver.bat
```

### Verificações Manuais:

- [ ] **Serviço SQL Server rodando**
  ```powershell
  Get-Service MSSQLSERVER
  # Status deve ser: Running
  ```

- [ ] **SQL Browser rodando**
  ```powershell
  Get-Service SQLBrowser
  # Status deve ser: Running
  ```

- [ ] **TCP/IP habilitado**
  - Configuration Manager → TCP/IP → Enabled

- [ ] **Porta 1433 configurada**
  - TCP/IP Properties → IP Addresses → IPAll → TCP Port: 1433

- [ ] **Firewall liberado**
  ```powershell
  Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*SQL*"}
  # Deve mostrar regras para porta 1433
  ```

- [ ] **Conexões remotas habilitadas**
  - SSMS → Properties → Connections → Allow remote connections ✅

- [ ] **Mixed Mode habilitado**
  - SSMS → Properties → Security → SQL Server and Windows Authentication

- [ ] **Usuário tem permissões**
  ```sql
  EXEC sp_helpuser 'pld_user'
  ```

## 🔍 Diagnóstico de Erros Comuns

### Erro: "Named Pipes Provider: Could not open a connection"

**Causa:** SQL Server está usando Named Pipes (somente local) ao invés de TCP/IP

**Solução:**
1. Habilitar TCP/IP no Configuration Manager
2. Adicionar porta explicitamente: `servidor,1433`
3. Reiniciar SQL Server

### Erro: "Login timeout expired"

**Causa:** Firewall bloqueando porta 1433 OU SQL Server não está escutando TCP/IP

**Solução:**
```powershell
# Verificar se porta está aberta
netstat -an | findstr ":1433"

# Deve mostrar: TCP    0.0.0.0:1433    0.0.0.0:0    LISTENING
```

### Erro: "Login failed for user 'pld_user'"

**Causa:** Usuário não existe ou não tem permissões

**Solução:**
```sql
-- Verificar login
SELECT name, is_disabled FROM sys.server_principals WHERE name = 'pld_user'

-- Dar permissões
USE [CORP]
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO [pld_user]
```

### Erro: "Server is not found or not accessible"

**Causa:** Nome/IP do servidor incorreto OU SQL Server não está rodando

**Solução:**
1. Verificar serviço: `Get-Service MSSQLSERVER`
2. Testar ping: `ping 192.168.0.119`
3. Testar porta: `Test-NetConnection -ComputerName 192.168.0.119 -Port 1433`

## 🎯 Connection String Correta

### Para Python/SQLAlchemy (nosso caso):

```python
# ✅ CORRETO - Com porta explícita
servidor = "192.168.0.119,1433"  # Vírgula + porta força TCP/IP
connection_url = f"mssql+pyodbc://{user}:{password}@{servidor}/{banco}?driver=..."

# ❌ ERRADO - Sem porta (pode usar Named Pipes)
servidor = "192.168.0.119"
```

### Para .NET/ADO.NET:

```csharp
Server=192.168.0.119,1433;Database=CORP;User Id=pld_user;Password=***;TrustServerCertificate=True
```

### Para ODBC:

```
Driver={ODBC Driver 17 for SQL Server};Server=192.168.0.119,1433;Database=CORP;Uid=pld_user;Pwd=***;TrustServerCertificate=yes
```

## 📚 Referências

- [Configure Windows Firewall for SQL Server](https://docs.microsoft.com/en-us/sql/sql-server/install/configure-the-windows-firewall-to-allow-sql-server-access)
- [Enable TCP/IP Network Protocol](https://docs.microsoft.com/en-us/sql/database-engine/configure-windows/enable-or-disable-a-server-network-protocol)
- [SQL Server Configuration Manager](https://docs.microsoft.com/en-us/sql/relational-databases/sql-server-configuration-manager)

---

**Última atualização:** 2024-02-21  
**Versão:** 1.0  
**Testado em:** SQL Server 2017, 2019, 2022
