# 🌐 Configuração para Acesso Externo (Rede Local)

Este guia explica como configurar o sistema para ser acessado de outras máquinas na rede local.

---

## ✅ Configuração Atual

### Backend (já configurado)
- ✅ FastAPI escutando em `0.0.0.0:5000` (todas as interfaces)
- ✅ CORS habilitado para requisições de qualquer origem
- ✅ Pronto para acesso externo

### Frontend (requer configuração)
- 📝 Arquivo `.env` já configurado
- 📝 Variável `HOST=0.0.0.0` adicionada
- 📝 Variável `REACT_APP_API_URL` apontando para IP do servidor

---

## 🔧 Passos para Habilitar Acesso Externo

### 1️⃣ Descobrir o IP do Servidor

**Windows (PowerShell ou CMD):**
```powershell
ipconfig
```
Procure por "Endereço IPv4" da interface ativa (ex: `192.168.0.119`)

**Linux/Mac:**
```bash
hostname -I
```

### 2️⃣ Verificar/Atualizar Configuração do Frontend

Arquivo: `frontend-app/.env`

```env
# React escutará em todas as interfaces (permite acesso externo)
HOST=0.0.0.0

# URL do backend - ALTERAR para o IP do seu servidor
REACT_APP_API_URL=http://192.168.0.119:5000
```

⚠️ **Importante**: Substitua `192.168.0.119` pelo IP real do seu servidor!

### 3️⃣ Liberar Portas no Firewall do Windows

Execute como **Administrador** no PowerShell:

```powershell
# Porta 3000 - Frontend React
New-NetFirewallRule -DisplayName "PLD Frontend (React)" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow

# Porta 5000 - Backend FastAPI
New-NetFirewallRule -DisplayName "PLD Backend (FastAPI)" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow

# Porta 50051 - Worker gRPC (opcional, só se precisar acesso direto)
New-NetFirewallRule -DisplayName "PLD Worker (gRPC)" -Direction Inbound -LocalPort 50051 -Protocol TCP -Action Allow
```

**Verificar regras criadas:**
```powershell
Get-NetFirewallRule -DisplayName "PLD*" | Select-Object DisplayName, Enabled, Direction, Action
```

**Remover regras (se necessário):**
```powershell
Remove-NetFirewallRule -DisplayName "PLD Frontend (React)"
Remove-NetFirewallRule -DisplayName "PLD Backend (FastAPI)"
Remove-NetFirewallRule -DisplayName "PLD Worker (gRPC)"
```

### 4️⃣ Reiniciar os Serviços

```bash
npm run stop:all
npm run start:all
```

---

## 🌐 Acessar de Outra Máquina

Substitua `192.168.0.119` pelo IP real do servidor:

### Frontend (Interface Web)
```
http://192.168.0.119:3000
```

### Backend (API direta - para testes)
```
http://192.168.0.119:5000/docs
```

---

## 🔍 Diagnóstico de Problemas

### Problema: "Não consigo acessar de outra máquina"

**1. Verificar se serviços estão rodando:**
```powershell
# Frontend
netstat -ano | findstr :3000

# Backend
netstat -ano | findstr :5000
```

**2. Testar conexão do próprio servidor:**
```powershell
# Frontend
curl http://localhost:3000

# Backend
curl http://localhost:5000
```

**3. Testar conexão de outra máquina:**
```bash
# De outra máquina na rede
curl http://IP_DO_SERVIDOR:5000
```

**4. Verificar firewall:**
```powershell
Get-NetFirewallRule -DisplayName "PLD*"
```

**5. Verificar se HOST está configurado:**
```powershell
# Ver conteúdo do .env
Get-Content frontend-app\.env
```

Deve aparecer:
```
HOST=0.0.0.0
REACT_APP_API_URL=http://SEU_IP:5000
```

### Problema: "Frontend carrega mas API não funciona"

**Causa**: `REACT_APP_API_URL` no `.env` está incorreto

**Solução**:
1. Abrir `frontend-app/.env`
2. Corrigir `REACT_APP_API_URL=http://IP_CORRETO:5000`
3. Reiniciar frontend: `npm run stop:all` → `npm run start:all`

⚠️ **Importante**: Após alterar `.env`, é OBRIGATÓRIO reiniciar o frontend!

### Problema: "Erro de CORS"

**Causa**: Backend não está aceitando requisições do IP remoto

**Verificação**: Checar console do backend procurando por:
```
INFO:     192.168.X.X:PORT - "OPTIONS /config/..." 200 OK
```

Se aparecer erro 403/405, verificar CORS no `api-gateway/main.py` (já deve estar configurado).

---

## 📋 Checklist Rápido

- [ ] IP do servidor identificado (ex: `ipconfig`)
- [ ] Arquivo `frontend-app/.env` atualizado com IP correto
- [ ] Variável `HOST=0.0.0.0` presente no `.env`
- [ ] Portas 3000 e 5000 liberadas no firewall
- [ ] Serviços reiniciados (`npm run restart:all`)
- [ ] Teste de acesso externo: `http://IP_SERVIDOR:3000`

---

## 🔒 Segurança

### Recomendações para Produção:

1. **Não expor para Internet pública** - apenas rede local
2. **Adicionar autenticação/autorização** - já implementado com JWT
3. **Configurar HTTPS** - usar certificado SSL/TLS
4. **Restringir IPs permitidos** - usar regras de firewall específicas
5. **Usar VPN** - para acesso remoto seguro

### Configuração Atual:
- ✅ Autenticação JWT implementada
- ✅ SQLite para armazenamento de usuários
- ✅ Credenciais criptografadas com Fernet
- ⚠️ Sem HTTPS (apenas HTTP)
- ⚠️ Sem restrição de IPs

---

## 🎯 Exemplo de Uso Típico

### Cenário: 3 máquinas na rede local

**Servidor (192.168.0.119)**:
- Roda backend, worker e frontend
- Configuração: `.env` com `HOST=0.0.0.0` e `REACT_APP_API_URL=http://192.168.0.119:5000`

**Cliente 1 (192.168.0.120)**:
- Acessa via navegador: `http://192.168.0.119:3000`

**Cliente 2 (192.168.0.121)**:
- Acessa via navegador: `http://192.168.0.119:3000`

Todos usam o mesmo backend/worker centralizados no servidor!

---

## 📞 Suporte

Se após seguir este guia ainda houver problemas:

1. Verificar logs do backend (terminal onde rodou `npm run backend:start`)
2. Verificar logs do frontend (terminal onde rodou frontend)
3. Testar conectividade: `ping 192.168.0.119` de outra máquina
4. Verificar se serviços estão escutando: `netstat -ano | findstr :3000`
