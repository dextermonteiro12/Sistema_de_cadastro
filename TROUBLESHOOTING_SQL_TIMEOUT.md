# 🚨 Guia de Troubleshooting - Timeout SQL Server

## ❌ Erro Encontrado

```
TCP Provider: The wait operation timed out.
Login timeout expired
Server is not found or not accessible
```

## 🎯 O Que Esse Erro Significa?

O **backend** (192.168.0.119) está tentando se conectar ao **SQL Server** (que está em outra máquina), mas não consegue alcançá-lo em tempo hábil. É como tentar ligar para alguém e ninguém atender.

## 🗺️ Arquitetura Atual

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   VOCÊ       │         │   BACKEND    │         │  SQL SERVER  │
│ (Cliente)    │────────▶│ 192.168.0.   │───✗────▶│  ???.???.    │
│              │   OK    │    119       │ TIMEOUT │  ???.???     │
└──────────────┘         └──────────────┘         └──────────────┘
    HTTP :5000              Python/FastAPI          SQL Server :1433
```

**O problema está na conexão Backend → SQL Server!**

## 🔍 Passo 1: Identificar o IP do SQL Server

### Opção A: Ver no XML (Advice.xml)

Abra o arquivo Advice.xml e procure pelo tag `<Servidor>`:

```xml
<Servidor>192.168.0.200</Servidor>  <!-- Este é o IP! -->
<Usuario>sa</Usuario>
<Senha>MinHaSenHa</Senha>
<NomeBanco>CORP</NomeBanco>
```

### Opção B: Ver nos logs do backend

Olhe a mensagem de erro completa, ela mostra qual servidor tentou conectar:

```
🔵 Tentando conectar ao SQL Server: 192.168.0.200,1433
🔵 Banco: CORP, Usuário: sa
❌ Erro ao conectar ao SQL Server 192.168.0.200,1433: timeout
```

## 🧪 Passo 2: Testar Conectividade

### **IMPORTANTE: Execute os testes NO SERVIDOR BACKEND (192.168.0.119)!**

### Teste Rápido (PowerShell):

```powershell
# Substitua 192.168.0.200 pelo IP do SEU SQL Server
Test-NetConnection -ComputerName 192.168.0.200 -Port 1433
```

**Resultado esperado:**
```
TcpTestSucceeded : True   ← ✅ SQL está acessível
```

**Se retornar False:**
```
TcpTestSucceeded : False  ← ❌ SQL não está acessível
```

### Teste Completo:

```powershell
cd C:\Users\fmonteiro\Documents\sistema_cadastro

# Teste com IP, usuário e senha do XML
.\teste-conexao-sql.ps1 -SqlServer "192.168.0.200" -Database "CORP" -Username "sa" -Password "SuaSenha"
```

## ⚙️ Passo 3: Corrigir o Problema

### Se `TcpTestSucceeded : False`

O SQL Server não está acessível do backend. **Ação necessária NO SERVIDOR SQL:**

#### 3.1 Verificar se SQL Server está rodando

**Execute NO SERVIDOR SQL:**
```powershell
Get-Service MSSQLSERVER
# Status deve ser: Running
```

Se estiver parado:
```powershell
net start MSSQLSERVER
```

#### 3.2 Habilitar TCP/IP

**NO SERVIDOR SQL:**

1. Abra **SQL Server Configuration Manager**
   - Pressione `Win + R`
   - Digite: `SQLServerManager15.msc` (SQL 2019) ou `SQLServerManager14.msc` (SQL 2017)

2. Navegue:
   ```
   SQL Server Network Configuration
   └── Protocols for MSSQLSERVER
       └── TCP/IP → Botão direito → Enable
   ```

3. Configure a porta:
   - Duplo clique em **TCP/IP**
   - Aba **IP Addresses**
   - Role até **IPAll**:
     - TCP Dynamic Ports: (deixe vazio)
     - TCP Port: **1433**

4. Reiniciar SQL Server:
   ```powershell
   net stop MSSQLSERVER
   net start MSSQLSERVER
   ```

#### 3.3 Liberar Firewall

**NO SERVIDOR SQL:**
```powershell
# Abra PowerShell como Administrador
New-NetFirewallRule -DisplayName "SQL Server 1433" `
  -Direction Inbound `
  -LocalPort 1433 `
  -Protocol TCP `
  -Action Allow

New-NetFirewallRule -DisplayName "SQL Browser 1434" `
  -Direction Inbound `
  -LocalPort 1434 `
  -Protocol UDP `
  -Action Allow
```

#### 3.4 Habilitar Conexões Remotas

**NO SERVIDOR SQL, via SSMS:**

1. Conecte ao servidor localmente
2. Botão direito no servidor → **Properties**
3. Página **Connections**
4. Marque: ✅ **"Allow remote connections to this server"**
5. Remote query timeout: `600`
6. OK

#### 3.5 Verificar se está escutando na porta correta

**NO SERVIDOR SQL:**
```powershell
netstat -an | findstr ":1433"

# Deve mostrar:
# TCP    0.0.0.0:1433    0.0.0.0:0    LISTENING
```

## 🔄 Passo 4: Testar Novamente

Após configurar no servidor SQL, **teste DO SERVIDOR BACKEND:**

```powershell
# DO SERVIDOR BACKEND (192.168.0.119)
Test-NetConnection -ComputerName 192.168.0.200 -Port 1433
```

Se retornar `TcpTestSucceeded : True`, tente conectar no sistema novamente!

## 📋 Checklist de Verificação

Execute NO SERVIDOR SQL:

- [ ] Serviço SQL Server está rodando
  ```powershell
  Get-Service MSSQLSERVER
  ```

- [ ] TCP/IP está habilitado
  - Configuration Manager → TCP/IP → Enabled

- [ ] Porta 1433 configurada
  - TCP/IP Properties → IPAll → TCP Port: 1433

- [ ] Firewall liberado para porta 1433
  ```powershell
  Get-NetFirewallRule | Where-Object {$_.LocalPort -eq 1433}
  ```

- [ ] SQL Server escutando na porta
  ```powershell
  netstat -an | findstr ":1433"
  ```

- [ ] Conexões remotas habilitadas
  - SSMS → Properties → Connections → Allow remote connections

- [ ] Backend consegue acessar a porta
  **Execute DO SERVIDOR BACKEND:**
  ```powershell
  Test-NetConnection -ComputerName IP_DO_SQL -Port 1433
  ```

## 🎯 Teste Final

Após completar o checklist:

1. **NO SERVIDOR BACKEND (192.168.0.119):**
   ```powershell
   .\teste-conexao-sql.ps1 -SqlServer "IP_DO_SQL" -Database "CORP" -Username "usuario" -Password "senha"
   ```

2. Se o teste passar, acesse o sistema:
   - `http://192.168.0.119:3000`
   - Tela de Configuração
   - Selecione o XML
   - Conecte às bases

## 📚 Documentação Relacionada

- **[ARQUITETURA_REDE.md](./ARQUITETURA_REDE.md)** - Entenda a arquitetura completa
- **[SQL_SERVER_ACESSO_REMOTO.md](./SQL_SERVER_ACESSO_REMOTO.md)** - Guia detalhado SQL Server
- **[teste-conexao-sql.ps1](./teste-conexao-sql.ps1)** - Script de teste automatizado

## 🆘 Se Ainda Não Funcionar

### Verificar Rede Entre Backend e SQL

**NO SERVIDOR BACKEND:**
```powershell
# Traceroute para ver o caminho
tracert IP_DO_SQL

# Ping
ping IP_DO_SQL

# Verificar rotas
route print
```

### Verificar Credenciais

**NO SERVIDOR SQL, via SSMS:**
```sql
-- Verificar se usuário existe
SELECT name, is_disabled, type_desc 
FROM sys.server_principals 
WHERE name = 'seu_usuario'

-- Verificar permissões
EXEC sp_helplogins 'seu_usuario'
```

### Logs Detalhados

Os logs agora mostram exatamente o que está acontecendo:

```powershell
# Ver logs do backend
Get-Content api-gateway\logs\*.log -Tail 50

# Procurar por:
# 🔵 Tentando conectar ao SQL Server: ...
# ❌ Erro ao conectar ao SQL Server ...
```

---

**Versão:** 1.0  
**Última atualização:** 2024-02-21  
**Status:** Melhorias aplicadas - diagnostico aumentado + timeout estendido para 15s
