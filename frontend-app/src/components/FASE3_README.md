# FASE 3: Indicadores Dinâmicos por Sistema

## Objetivo
Implementar componentes de indicadores que variam de acordo com o sistema da base selecionada (CORP vs Outras).

## Estrutura Implementada

### 1. **IndicatorsCORP.js**
**Local**: `src/components/IndicatorsCORP.js`

Componente específico para bases CORP com os seguintes KPIs:

- **Fila de Processamento**: Mostra quantidade de requisições na fila
  - Status: Verde (<100), Amarelo (<500), Vermelho (>=500)
- **Status do Servidor**: Indica se o servidor está online ou offline
- **Erros Registrados**: Contagem de erros no período
- **Clientes Pendentes**: Clientes aguardando integração

**Props**:
```javascript
{
  saude: { fila, status, erros },  // Dados de saúde do servidor
  clientesPendentes: { quantidade }, // Clientes aguardando integração
  banco: String,                      // Nome do banco
  atualizadoEm: String,              // ISO timestamp da última atualização
  erro: String                        // Mensagem de erro se houver
}
```

### 2. **IndicatorsDefault.js**
**Local**: `src/components/IndicatorsDefault.js`

Componente genérico para bases não-CORP (EGUARDIAN, manuais, etc) com os seguintes KPIs:

- **Status da Conexão**: Ativa ou Inativa
- **Disponibilidade**: Percentual de uptime
- **Latência Média**: Tempo médio de resposta em ms
- **Taxa de Erro**: Contagem de erros

**Props**:
```javascript
{
  saude: { conexao, disponibilidade, latencia, erros },
  banco: String,
  atualizadoEm: String,
  erro: String
}
```

### 3. **IndicatorsManager.js**
**Local**: `src/components/IndicatorsManager.js`

Componente gerenciador que escolhe qual variante renderizar:

```javascript
if (sistema === 'CORP') {
  return <IndicatorsCORP {...props} />
} else {
  return <IndicatorsDefault {...props} />
}
```

**Props**:
```javascript
{
  sistema: String,           // "CORP" ou outro
  banco: String,             // Nome do banco
  saude: Object,             // Dados de saúde
  clientesPendentes: Object, // (Apenas para CORP)
  atualizadoEm: String,      // Timestamp
  erro: String,              // Mensagem de erro
  loading: Boolean           // Estado de carregamento
}
```

### 4. **Home.js Atualizado**
**Local**: `src/screens/home.js`

**Mudanças**:
- Importou `IndicatorsManager`
- Substituiu renderização manual de KPIs pela chamada do gerenciador
- Passa `sistema` da base selecionada para o gerenciador
- Mantém gráfico original de performance se disponível

**Fluxo**:
```
Home.js
  ↓
carregarBases() → Obtém sistema de cada base
  ↓
Usuário seleciona base
  ↓
IndicatorsManager recebe sistema + dados
  ↓
IF sistema == 'CORP' → IndicatorsCORP
ELSE → IndicatorsDefault
```

## Estrutura de Dados das Bases

Cada base agora contém:

```javascript
{
  id: String,      // ID único
  label: String,   // "CORP | CORP | CORP" format
  sistema: String, // "CORP" ou outro (EGUARDIAN, etc)
  banco: String    // Nome do banco
}
```

O `sistema` vem do arquivo `Advice.xml` durante o discovery:
```xml
<Base>
  <Nome>...</Nome>
  <Sistema>CORP</Sistema>  <!-- Este valor é usado para rotear indicadores -->
  <Banco>NomedoBanco</Banco>
</Base>
```

## UI/UX

### IndicatorsCORP
- Header: "📊 Indicadores CORP - {banco}"
- Grid: 4 KPI cards em linha
- Cores: Variam por status (Verde=OK, Amarelo=Aviso, Vermelho=Erro)
- Rodapé: Timestamp da última atualização

### IndicatorsDefault  
- Header: "📈 Indicadores - {banco}"
- Grid: 4 KPI cards em linha (mesma estrutura)
- Cores: Mesma estratégia de status
- Rodapé: Timestamp + "PADRÃO"

## Próximos Passos (User Specifys)

1. **Substituir dados MOCK pelos reais**:
   - IndicatorsCORP: Conectar aos endpoints que retornam fila, status, erros, clientes_pendentes
   - IndicatorsDefault: Conectar aos endpoints para conexão, disponibilidade, latência, erros

2. **Adicionar endpoints no Backend**:
   - `/api/indicadores/corp/{session_id}` - KPIs CORP específicos
   - `/api/indicadores/default/{session_id}` - KPIs genéricos

3. **Expandir para mais sistemas**:
   - Se houver outras variantes além de CORP vs Default, crie novos componentes
   - Ex: `IndicatorsEGUARDIAN.js` se necessário

4. **Adicionar funcionalidades avançadas**:
   - Auto-refresh (já está em Home.js com 10s)
   - Histórico de indicadores
   - Alertas quando status crítico
   - Exportar dados

## Testes

Para testar a estrutura:

1. Fazer login com base CORP → Deve ser renderizado IndicatorsCORP
2. Fazer login com base EGUARDIAN → Deve ser renderizado IndicatorsDefault
3. Verificar que o gráfico de performance ainda aparece ao fim

## Comentários no Código

Cada arquivo tem comentários descritivos indicando:
- **Propósito**: O que o componente faz
- **KPIs**: Quais indicadores mostra
- **Props**: Dados esperados
- **Status**: Lógica de coloração
- **TODO**: Onde inserir dados reais

---

**Status**: ✅ Estrutura criada | ⏳ Aguardando dados reais para popular
