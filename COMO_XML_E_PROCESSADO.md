# Como o Sistema Identifica Bases no Advice.xml

## 📋 Resumo
O sistema procura **especificamente** por sistemas chamados `CORP` e `EGUARDIAN` no XML e extrai informações de banco de dados de cada empresa configurada dentro desses sistemas.

---

## 🔍 Estrutura Esperada do XML

O sistema espera esta estrutura hierárquica:

```xml
<root>
    <CORP>
        <EMPRESA>
            <nome_empresa_1>
                <BANCO_DADOS>
                    <NOME_SERVIDOR>servidor1</NOME_SERVIDOR>
                    <NOME_BD>BASE_CORP_1</NOME_BD>
                    <USUARIO>usuario1</USUARIO>
                    <PROVIDER>SQLOLEDB</PROVIDER>
                    <TIME_OUT>30</TIME_OUT>
                </BANCO_DADOS>
            </nome_empresa_1>
            <nome_empresa_2>
                <BANCO_DADOS>
                    <NOME_SERVIDOR>servidor2</NOME_SERVIDOR>
                    <NOME_BD>BASE_CORP_2</NOME_BD>
                    <USUARIO>usuario2</USUARIO>
                    <PROVIDER>SQLOLEDB</PROVIDER>
                    <TIME_OUT>30</TIME_OUT>
                </BANCO_DADOS>
            </nome_empresa_2>
        </EMPRESA>
    </CORP>
    
    <EGUARDIAN>
        <EMPRESA>
            <empresa_A>
                <BANCO_DADOS>
                    <NOME_SERVIDOR>servidor_eguardian</NOME_SERVIDOR>
                    <NOME_BD>BASE_EGUARDIAN_A</NOME_BD>
                    <USUARIO>user_eguardian</USUARIO>
                    <PROVIDER>SQLOLEDB</PROVIDER>
                    <TIME_OUT>30</TIME_OUT>
                </BANCO_DADOS>
            </empresa_A>
        </EMPRESA>
    </EGUARDIAN>
</root>
```

---

## 🎯 Lógica de Identificação (Código Backend)

### 1. **Sistema Procurado**
O código busca **hardcoded** por apenas 2 sistemas:

```python
for sistema in ["CORP", "EGUARDIAN"]:
    sistema_node = find_sistema_node(sistema)
```

**❗ Importante:** Se o XML tiver outros sistemas (ex: `ADVISOR`, `LEGADO`, `V9`), eles **NÃO serão lidos**.

---

### 2. **Navegação Hierárquica**
Após encontrar `<CORP>` ou `<EGUARDIAN>`, o código:

1. Procura nó filho `<EMPRESA>`
2. Itera por todos os nós dentro de `<EMPRESA>`
3. Para cada nó filho (empresa), procura `<BANCO_DADOS>`

```python
sistema_node = find_sistema_node("CORP")  # ou "EGUARDIAN"
empresa_root = find_child(sistema_node, "EMPRESA")

for empresa_node in list(empresa_root):
    banco_node = find_child(empresa_node, "BANCO_DADOS")
```

---

### 3. **Extração de Dados**
Dentro do nó `<BANCO_DADOS>`, busca estes campos obrigatórios:

| Campo XML | Uso | Obrigatório |
|-----------|-----|-------------|
| `NOME_SERVIDOR` | Servidor SQL | ❌ (opcional) |
| `NOME_BD` | Nome da base | ✅ **SIM** |
| `USUARIO` | Usuário SQL | ❌ (opcional) |
| `PROVIDER` | Provider OLEDB | ❌ (opcional) |
| `TIME_OUT` | Timeout conexão | ❌ (opcional) |

**🚨 Regra Crítica:** Se `NOME_BD` (nome do banco) estiver vazio, a base **NÃO** é adicionada à lista.

```python
banco = find_text(banco_node, "NOME_BD")

if not banco:
    logger.warning(f"Banco não encontrado para {sistema}/{empresa}")
    continue  # ⚠️ Base ignorada!
```

---

### 4. **Case Insensitive**
O código ignora maiúsculas/minúsculas nas tags:

```python
def local_name(tag: str) -> str:
    return tag.split("}")[-1].strip()

def find_child(parent, child_name: str):
    alvo = child_name.lower()
    for child in list(parent):
        if local_name(child.tag).lower() == alvo:
            return child
    return None
```

**✅ Funciona:**
- `<CORP>`, `<corp>`, `<Corp>`
- `<EMPRESA>`, `<empresa>`, `<Empresa>`
- `<BANCO_DADOS>`, `<banco_dados>`

---

### 5. **Namespace XML**
Se o XML tiver namespace (ex: `<ns0:CORP xmlns:ns0="...">`), o código remove automaticamente:

```python
tag.split("}")[-1]  # Remove tudo antes de '}' (namespace)
```

✅ **Suporta**: `{http://example.com/schema}CORP` → `CORP`

---

## 🛠️ Resultado Final

Cada base encontrada gera este objeto:

```json
{
  "id": "CORP:MATRIZ:BASE_PLD_MATRIZ",
  "sistema": "CORP",
  "empresa": "MATRIZ",
  "servidor": "SQL-SERVER-01",
  "banco": "BASE_PLD_MATRIZ",
  "usuario": "pld_user",
  "provider": "SQLOLEDB",
  "timeout": "30",
  "label": "CORP | MATRIZ | BASE_PLD_MATRIZ"
}
```

---

## 🐛 Possíveis Motivos para Bases Não Aparecerem

### ❌ 1. Sistema não é CORP ou EGUARDIAN
```xml
<ADVISOR>  ⚠️ Será IGNORADO
    <EMPRESA>...</EMPRESA>
</ADVISOR>
```
**Solução:** Renomear para `<CORP>` ou `<EGUARDIAN>`, ou atualizar código backend.

---

### ❌ 2. Estrutura hierárquica diferente
```xml
<CORP>
    <MATRIZ>  ⚠️ ERRO: deveria estar dentro de <EMPRESA>
        <BANCO_DADOS>...</BANCO_DADOS>
    </MATRIZ>
</CORP>
```

**Estrutura correta:**
```xml
<CORP>
    <EMPRESA>
        <MATRIZ>
            <BANCO_DADOS>...</BANCO_DADOS>
        </MATRIZ>
    </EMPRESA>
</CORP>
```

---

### ❌ 3. Campo NOME_BD vazio ou ausente
```xml
<BANCO_DADOS>
    <NOME_SERVIDOR>servidor1</NOME_SERVIDOR>
    <NOME_BD></NOME_BD>  ⚠️ Vazio = Base IGNORADA
    <USUARIO>user1</USUARIO>
</BANCO_DADOS>
```

---

### ❌ 4. Nó BANCO_DADOS não existe
```xml
<MATRIZ>
    <SERVIDOR>sql-server</SERVIDOR>  ⚠️ ERRO: deveria ser <BANCO_DADOS>
    <BD_NOME>PLD_MATRIZ</BD_NOME>
</MATRIZ>
```

**Estrutura correta:**
```xml
<MATRIZ>
    <BANCO_DADOS>
        <NOME_SERVIDOR>sql-server</NOME_SERVIDOR>
        <NOME_BD>PLD_MATRIZ</NOME_BD>
    </BANCO_DADOS>
</MATRIZ>
```

---

## 📊 Logs de Debug

O backend gera estes logs durante a leitura:

```
INFO: Procurando sistema: CORP
INFO: Sistema CORP encontrado
INFO: Nó EMPRESA encontrado para CORP
INFO: Base encontrada: CORP | MATRIZ | BASE_PLD_MATRIZ
INFO: Base encontrada: CORP | FILIAL1 | BASE_PLD_FILIAL1
INFO: Procurando sistema: EGUARDIAN
WARNING: Sistema EGUARDIAN não encontrado no XML
INFO: Total de bases encontradas: 2
```

---

## 🔧 Como Diagnosticar

### Opção 1: Verificar logs do backend
Ao carregar o XML, procure no console backend por:
- `Sistema {nome} não encontrado no XML`
- `Nó EMPRESA não encontrado para {sistema}`
- `Banco não encontrado para {sistema}/{empresa}`

### Opção 2: Verificar estrutura do XML
1. Abra o `Advice.xml`
2. Confirme que existe `<CORP>` e/ou `<EGUARDIAN>` na raiz
3. Dentro de cada sistema, confirme `<EMPRESA>`
4. Dentro de `<EMPRESA>`, confirme nós de empresa (ex: `<MATRIZ>`)
5. Dentro de cada empresa, confirme `<BANCO_DADOS>`
6. Dentro de `<BANCO_DADOS>`, confirme `<NOME_BD>` preenchido

---

## 🎯 Próximos Passos

Para incluir bases de outros sistemas (não CORP/EGUARDIAN):

**Opção A:** Modificar o código backend para aceitar mais sistemas:
```python
for sistema in ["CORP", "EGUARDIAN", "ADVISOR", "LEGADO"]:
```

**Opção B:** Adicionar busca genérica por qualquer nó que tenha `<EMPRESA>/<BANCO_DADOS>`.

**Opção C:** Permitir configuração manual no frontend (sem depender do XML).

---

## 📝 Arquivo Backend
Local: `api-gateway/routes/config.py`
Função principal: `_extract_bases_from_xml(xml_path: Path)`
Endpoint: `POST /config/listar-bases-pasta`
