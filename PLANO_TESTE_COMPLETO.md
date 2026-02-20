# PLANO DE TESTE COMPLETO - FASE 1, 2 E 3

## 🎯 Objetivo
Validar o fluxo completo de autenticação, configuração e indicadores dinâmicos por sistema.

---

## 📋 PASSO 1: LOGIN

**URL**: http://localhost:3000

### Ação
1. Você verá a tela de Login
2. Clique em **"Não tem conta? Registre-se"** para criar uma nova conta OU use credenciais existentes
3. Se for criar conta:
   - **Username**: testuser
   - **Password**: teste123
   - Clique em **"Criar Conta"**

### ✅ O que verificar
- [ não] Tela de login carrega sem erros
- [não ] Botão de toggle entre Login/Register funciona
- [ não] Após registro/login bem-sucedido, redirecionamento automático para /configuracao
- [não ] Token JWT armazenado em localStorage (verificar no DevTools → Application → localStorage → auth_token)

---

## 📊 PASSO 2: CONFIGURAR BASES (Configuração)

**URL**: http://localhost:3000/configuracao (automático após login)

### Ação
1. **Preencher Arquivo Advice.xml**:
   - Path: `C:\Advice` (ou o caminho onde você tem o arquivo)
   - Clique em **"Ler arquivo Advice.xml"**

2. **Preencher Credenciais SQL Server**:
   - **Servidor**: localhost\\SQLEXPRESS (ou seu servidor)
   - **Usuario**: sa
   - **Senha**: sua_senha_sql
   - Clique em **"Validar Conexão"**

3. **Após validação bem-sucedida**:
   - Sistema descobrirá as bases do XML
   - Mostrará: "Base(s) encontrada(s): X"
   - Clique em **"Testar & Ativar"**

### ✅ O que verificar (Fase 2)
- [ ] XML é lido corretamente
- [ ] Bases são descobertas e mostradas (com sistema = CORP ou EGUARDIAN)
- [ ] SQL connection é testada
- [ ] Mensagem de sucesso: "Configuração salva com sucesso: N base(s)"
- [ ] Dados salvos no SQLite (user_configs com credentials encriptados)

---

## 🏠 PASSO 3: HOME - SELETOR DE BASES

**URL**: http://localhost:3000/home (automático após sucesso em Configuração)

### Ação
1. A tela Home carregará com:
   - **Box**: "Bases para monitorar"
   - **Dropdown**: Lista de bases descobertas
   - **Botão**: "Limpar seleção"

2. Clique no dropdown para abrir a lista
3. Deve aparecer as bases com labels tipo: "CORP | CORP | CORP"

### ✅ O que verificar (Fim da Fase 2)
- [ ] Dropdown carrega as bases salvas do usuário
- [ ] Busca/filtro funciona (digite parte do nome)
- [ ] Base selecionada é mantida no estado
- [ ] Bases mostram: id, label, sistema, banco

---

## 📊 PASSO 4: INDICADORES - O GRANDE TESTE (FASE 3)

### 4.1 - Selecionar Base CORP

**Ação**:
1. No dropdown, procure por uma base com label contendo "CORP"
2. Clique na base CORP

### ✅ O que verificar (Fase 3 - IndicatorsCORP)
Após selecionar, você deve ver um painel com:

**Header**: 
- [ ] "📊 Indicadores CORP - {NomeDoBanco}"

**4 KPI Cards** em grid (linha única):

1. **Fila de Processamento**
   - [ ] Valor numérico (ex: 42)
   - [ ] Status com cor (verde se <100, amarelo se <500, vermelho se >=500)
   - [ ] Label: "Fila de Processamento"

2. **Status do Servidor**
   - [ ] Valor: "✓ Online" ou "✗ Offline"
   - [ ] Cor apropriada ao status
   - [ ] Label: "Status do Servidor"

3. **Erros Registrados**
   - [ ] Número de erros (ex: 0, 5, 12)
   - [ ] Color status (verde=0, amarelo=<10, vermelho=>=10)
   - [ ] Label: "Erros Registrados"

4. **Clientes Pendentes**
   - [ ] Quantidade (ex: 0, 3, 15)
   - [ ] Status (amarelo se >0, verde se 0)
   - [ ] Label: "Clientes Pendentes"

**Rodapé**:
- [ ] Timestamp de atualização: "Atualizado: HH:MM:SS"
- [ ] Label "CORP"

---

### 4.2 - Selecionar Base Não-CORP (EGUARDIAN ou outra)

**Ação**:
1. No dropdown, procure por uma base NÃO-CORP (ex: EGUARDIAN)
2. Clique nessa base

### ✅ O que verificar (Fase 3 - IndicatorsDefault)
Após selecionar, você deve ver um painel DIFERENTE com:

**Header**: 
- [ ] "📈 Indicadores - {NomeDoBanco}" (note: sem "CORP")

**4 KPI Cards** em grid (linha única):

1. **Status da Conexão**
   - [ ] Valor: "✓ Ativa" ou "✗ Inativa"
   - [ ] Cor apropriada
   - [ ] Label: "Status da Conexão"

2. **Disponibilidade**
   - [ ] Percentual (ex: 100%, 95%, 87%)
   - [ ] Status: Verde (>=95%), Amarelo (>=80%), Vermelho (<80%)
   - [ ] Label: "Disponibilidade"

3. **Latência Média**
   - [ ] Tempo em ms (ex: 45ms, 150ms, 800ms)
   - [ ] Status: Verde (<100), Amarelo (<500), Vermelho (>=500)
   - [ ] Label: "Latência Média"

4. **Taxa de Erro**
   - [ ] Número de erros (ex: 0, 2, 15)
   - [ ] Status: Verde (0), Amarelo (<5), Vermelho (>=5)
   - [ ] Label: "Taxa de Erro"

**Rodapé**:
- [ ] Timestamp: "Atualizado: HH:MM:SS"
- [ ] Label "PADRÃO"

---

## 🔄 PASSO 5: TESTAR ALTERNÂNCIA

**Ação**:
1. Volta ao dropdown e seleciona a base **CORP** novamente
2. Verifica que IndicatorsCORP reaparece
3. Volta ao dropdown e seleciona base **Não-CORP**
4. Verifica que IndicatorsDefault reaparece

### ✅ O que verificar
- [ ] Componentes alternam corretamente baseado em `sistema`
- [ ] Headers mudam ("CORP" vs padrão)
- [ ] KPIs são diferentes (Fila/Status/Erros/Clientes vs Conexão/Disponibilidade/Latência/Taxa)
- [ ] Cores mantêm lógica apropriada

---

## 📈 PASSO 6: GRÁFICO DE PERFORMANCE (Bônus)

**Verificar**:
- [ ] Após os 4 KPI cards, aparece um gráfico "LATÊNCIA / CARGA"
- [ ] Gráfico mostra barras com dados de performance
- [ ] Gráfico atualiza a cada 10 segundos (auto-refresh)

---

## 🎯 CHECKLIST FINAL

| Fase | Componente | Status |
|------|-----------|--------|
| 1 | Login/Register | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 1 | JWT Token Storage | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 2 | XML Read + Base Discovery | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 2 | User Config Persistence | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 2 | Base Selector Dropdown | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 3 | IndicatorsCORP Render | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 3 | IndicatorsDefault Render | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 3 | IndicatorsManager Logic | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |
| 3 | Sistema-based Routing | [![Testing](https://img.shields.io/badge/status-testing-yellow)] |

---

## 🐛 TROUBLESHOOTING

### "Página branca na tela de Login"
- Verificar console (F12 → Console)
- Confirmar que backend está respondendo em http://localhost:5000/health
- Confirmar que frontend está servindo em http://localhost:3000

### "Erro ao fazer login"
- Verificar credenciais
- Verificar campo `auth_token` em localStorage (DevTools)
- Verificar resposta em Network do backend registro/login endpoints

### "Bases não aparecem no dropdown"
- Verificar que arquivo Advice.xml foi lido corretamente
- Verificar console para mensagens de erro do XML parser
- Confirmar que XML tem tags `<Sistema>` preenchidas

### "IndicatorsCORP não aparece para base CORP"
- Verificar que a base tem `sistema: 'CORP'` nos dados
- Verificar DevTools → React DevTools → props do IndicatorsManager
- Verificar console para erros do componente

### "Componentes aparecem em branco"
- Verificar console para erros JavaScript
- Confirmar que props estão sendo passadas corretamente
- Verificar que CSS inline está correto

---

## 📝 PRÓXIMOS PASSOS (Após Validação)

1. Substituir **dados mock** pelos **dados reais** de cada endpoint
2. Conectar KPIs a endpoints específicos (saude-servidor, clientes-pendentes, etc)
3. Adicionar **novos indicadores** conforme necessário
4. Implementar **alertas** para KPIs críticos
5. Adicionar **histórico** de indicadores

---

**Criado em**: 20/02/2026
**Status**: 🔴 Aguardando teste do usuário
