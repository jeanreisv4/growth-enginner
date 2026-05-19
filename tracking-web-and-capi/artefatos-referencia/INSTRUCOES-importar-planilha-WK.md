# Instruções pra importar e configurar a planilha

## 📦 Arquivos que você tem

1. **`template-leads-WK.csv`** — cabeçalhos da aba `Leads` + 1 linha de exemplo
2. **`template-dropdowns-WK.csv`** — valores das listas (origem, ambiente, metragem, status, motivo_perdido)
3. **`template-planilha-leads-WK.md`** — documentação completa de referência

---

## 🚀 Passo a passo (15-20 min)

### 1) Criar nova planilha
1. Abra https://sheets.google.com
2. Clique em **+ Em branco** (nova planilha)
3. Renomeie pra `[OFICIAL] Leads - WK Carpetes`
4. Configure permissão: **Compartilhar → Restrito** (não público)

### 2) Importar a aba `Leads`
1. Na nova planilha, clique na aba `Página1` (canto inferior) → renomeie pra `Leads`
2. **Arquivo → Importar** → faça upload de `template-leads-WK.csv`
3. Local da importação: **Substituir planilha atual**
4. Tipo de separador: **Detectar automaticamente**
5. Confirme

A aba `Leads` agora tem 24 colunas + 1 linha de exemplo. **Apague a linha de exemplo** (clique direito → Excluir linha) antes de começar o uso real.

### 3) Criar aba `Configuracao` (valores dos dropdowns)
1. Canto inferior → **+** (nova aba) → renomeie pra `Configuracao`
2. **Arquivo → Importar** → upload de `template-dropdowns-WK.csv`
3. Local: **Anexar à planilha** (NÃO substituir)
4. Confirme
5. Mova a aba para o final (clique direito → Mover para o final)

A aba `Configuracao` vai ter 5 colunas (origem, ambiente, metragem, status, motivo_perdido) com os valores possíveis. **Não apague essa aba.**

### 4) Configurar dropdowns (Validação de Dados) na aba `Leads`

⚠️ Faça com a aba `Leads` selecionada.

**Para cada coluna abaixo, repita:**

#### Coluna C (origem):
1. Selecione **C2:C** (toda a coluna a partir da linha 2)
2. **Dados → Validação de dados → Adicionar regra**
3. Critério: **Suspenso (do intervalo)**
4. Intervalo de origem: `=Configuracao!A2:A`
5. Mostrar texto de ajuda: marcar
6. Em dados inválidos: **Rejeitar entrada**
7. Salvar

#### Coluna G (ambiente):
- Intervalo: `=Configuracao!B2:B`

#### Coluna H (metragem):
- Intervalo: `=Configuracao!C2:C`

#### Coluna P (status) — ⭐ a mais importante:
- Intervalo: `=Configuracao!D2:D`

#### Coluna T (motivo_perdido):
- Intervalo: `=Configuracao!E2:E`

#### Coluna U (vendedor):
- Use lista direta: `João Silva,Maria Costa,...` (substitua pelos nomes reais do time de vendas)

### 5) Configurar formatação condicional (cores por status)
1. Selecione **A2:X1000** (toda a área de dados)
2. **Formatar → Formatação condicional**
3. Clique em **+ Adicionar outra regra** pra cada status:

| Regra | Fórmula | Cor de fundo |
|-------|---------|--------------|
| 1 | `=$P2="Lead"` | Cinza claro |
| 2 | `=$P2="MQL"` | Amarelo claro |
| 3 | `=$P2="SQL"` | Laranja claro |
| 4 | `=$P2="Cliente"` | Verde claro |
| 5 | `=$P2="Perdido"` | Vermelho claro |

### 6) Instalar Apps Script (datas automáticas)
1. **Extensões → Apps Script**
2. Apague o código padrão
3. Cole este código:

```javascript
function onEdit(e) {
  const sheet = e.range.getSheet();
  if (sheet.getName() !== 'Leads') return;

  const col = e.range.getColumn();
  const row = e.range.getRow();
  if (row < 2) return;

  // Coluna P = status (16)
  if (col !== 16) return;

  const status = e.value;
  const now = new Date();

  const dateCols = {
    'MQL': 17,
    'SQL': 18,
    'Cliente': 19
  };

  if (dateCols[status]) {
    const dateCol = dateCols[status];
    const existingDate = sheet.getRange(row, dateCol).getValue();
    if (!existingDate) {
      sheet.getRange(row, dateCol).setValue(now);
    }
  }
}
```

4. **Salvar** (ícone de disquete)
5. Renomeie o projeto pra `WK - Auto Dates`
6. **Fechar** (volta pra planilha)

**Como testar:** numa linha de teste, mude o status pra `MQL`. A célula `data_mql` (coluna Q) deve preencher automaticamente.

### 7) Migrar os 8 leads atuais

Pra cada lead na aba antiga (LP 1 - MQL V1 ou FORMS - MQL V1), criar uma linha nova em `Leads`:

| Campo antigo | Campo novo | Observação |
|--------------|-----------|------------|
| (não existe) | `lead_id` | gerar manual: `HIST-001`, `HIST-002`... pros leads históricos |
| Data + Hora | `data_lead` | combinar em 1 célula |
| (não existe) | `origem` | aba antiga LP → `LP - carpete-em-placas`; aba antiga FORMS → `FB Form - Pegasus` |
| Nome, E-mail, WhatsApp, Ambiente, Metragem, utm_* | mesmos campos | direto |
| MQL/SQL/VENDA checked? | `status` | última etapa marcada vira o status |
| PERDIDO/FORA DO PERFIL checked? | `status` = `Perdido` | preencher `motivo_perdido` |
| FATURAMENTO | `faturamento` | direto |
| OBSERVAÇÃO | `observacao` | direto |

Após migrar, **renomeie as 2 abas antigas pra**:
- `LP 1 - MQL V1 [HISTÓRICO - NÃO USAR]`
- `FORMS - MQL V1 [HISTÓRICO - NÃO USAR]`

### 8) Compartilhar e proteger
1. **Compartilhar** → adicionar emails específicos (você, coordenador, vendedores)
2. Vendedores: **Editor**
3. Coordenador (você): **Proprietário ou Editor**
4. **Proteger colunas automáticas**:
   - Selecionar colunas A (lead_id), Q (data_mql), R (data_sql), S (data_venda), X (sincronizado_capi)
   - **Dados → Proteger intervalos** → permitir edição só pra você

---

## ✅ Checklist final

- [ ] Planilha criada com nome oficial
- [ ] Aba `Leads` com 24 colunas + cabeçalhos
- [ ] Aba `Configuracao` com listas
- [ ] Dropdowns configurados em C, G, H, P, T, U
- [ ] Formatação condicional aplicada (5 cores)
- [ ] Apps Script `onEdit` instalado e testado
- [ ] 8 leads históricos migrados (com `lead_id` `HIST-001` a `HIST-008`)
- [ ] Abas antigas renomeadas como [HISTÓRICO]
- [ ] Permissões restritas + colunas automáticas protegidas

---

## 🎯 Depois disso, me manda:

1. **Link da nova planilha** (continua privada, só me adiciona se quiser que eu valide)
2. **Workflow n8n exportado** (JSON)

Que eu adapto o n8n pra escrever na nova aba e monto o Apps Script de envio Purchase pro SSGTM.
