# Template: Planilha Padrão de Leads — V4 WK Marketing

> **Objetivo:** padrão único de planilha de tracking de leads, aplicável tanto para LP quanto para Lead Ads do Meta (Forms Nativo).
>
> **Cliente piloto:** WK Carpetes
> **Versão:** 1.0
> **Última atualização:** 2026-05-17

---

## 1. Estrutura de colunas

### Aba `Leads` (única aba ativa — substitui LP 1 - MQL V1 e FORMS - MQL V1)

| Col | Nome | Tipo | Origem do dado | Obrigatório |
|-----|------|------|----------------|-------------|
| A | `lead_id` | Texto | GTM (event_id) ou Meta (leadgen_id) | ✅ |
| B | `data_lead` | Data + Hora | Auto (n8n / formulário) | ✅ |
| C | `origem` | Lista (dropdown) | n8n preenche | ✅ |
| D | `nome` | Texto | Form/Meta | ✅ |
| E | `email` | Email | Form/Meta | ✅ |
| F | `whatsapp` | Texto (telefone) | Form/Meta | ✅ |
| G | `ambiente` | Lista (dropdown) | Form/Meta | ✅ |
| H | `metragem` | Lista (dropdown) | Form/Meta | ✅ |
| I | `utm_source` | Texto | URL | — |
| J | `utm_medium` | Texto | URL | — |
| K | `utm_campaign` | Texto | URL ou Meta campaign_id | — |
| L | `utm_term` | Texto | URL ou Meta adset_id | — |
| M | `utm_content` | Texto | URL ou Meta ad_id | — |
| N | `gclid` | Texto | URL (Google Ads click) | — |
| O | `fbclid` | Texto | URL (Meta click) | — |
| **P** | **`status`** | **Lista (dropdown)** | **Vendedor altera manualmente** | ✅ |
| Q | `data_mql` | Data | Fórmula automática | — |
| R | `data_sql` | Data | Fórmula automática | — |
| S | `data_venda` | Data | Fórmula automática | — |
| T | `motivo_perdido` | Lista (dropdown) | Vendedor (só se status=Perdido) | Condicional |
| U | `vendedor` | Lista (dropdown) | Quem atendeu o lead | ✅ |
| V | `faturamento` | Moeda (R$) | Valor da venda (só se status=Cliente) | Condicional |
| W | `observacao` | Texto livre | Vendedor (qualquer momento) | — |
| X | `sincronizado_capi` | Checkbox | Apps Script marca quando enviar pro SSGTM | — |

---

## 2. Configuração de Dropdowns (Validação de Dados)

### Coluna C: `origem`
- `LP - carpete-em-placas`
- `LP - <outra-lp>` (adicione conforme crie mais LPs)
- `FB Form - Pegasus` (ou nome do form atual)
- `FB Form - <outro-form>`
- `WhatsApp Direto`
- `Indicação`
- `Outros`

### Coluna G: `ambiente` (idêntico ao form)
- `corporativo/escritório`
- `hotelaria/flats`
- `institucional (cinemas, teatros)`
- `residencial (quarto, sala, home office)`

### Coluna H: `metragem` (idêntico ao form)
- `até 25m²`
- `entre 25 e 50m²`
- `entre 50 e 75m²`
- `entre 75 e 100m²`
- `acima de 100m²`

### Coluna P: `status` ⭐ (CORAÇÃO DA PLANILHA)
- `Lead` (chegou no sistema, ainda não qualificado)
- `MQL` (qualificou no formulário pela LP — automático)
- `SQL` (qualificou no contato pelo time comercial)
- `Cliente` (fechou venda)
- `Perdido` (não fechou — preencher motivo_perdido)

### Coluna T: `motivo_perdido`
- `Fora do perfil`
- `Sem orçamento`
- `Foi pra concorrente`
- `Sem retorno do cliente`
- `Projeto cancelado`
- `Timing errado (volta depois)`
- `Outro`

### Coluna U: `vendedor`
- Lista com os nomes dos vendedores da WK
- Ex.: `João Silva`, `Maria Costa`, etc.

---

## 3. Fórmulas Automáticas (Datas)

⚠️ **As datas de transição NÃO devem ser preenchidas à mão.** Use Apps Script (recomendado) OU fórmulas matriciais.

### Solução A — Apps Script (recomendado, robusto)

Cole no Editor de Script (Extensões → Apps Script):

```javascript
function onEdit(e) {
  const sheet = e.range.getSheet();
  if (sheet.getName() !== 'Leads') return;

  const col = e.range.getColumn();
  const row = e.range.getRow();
  if (row < 2) return; // ignora cabeçalho

  // Coluna P = status (16)
  if (col !== 16) return;

  const status = e.value;
  const now = new Date();

  // Mapa status → coluna de data
  const dateCols = {
    'MQL': 17,      // Q
    'SQL': 18,      // R
    'Cliente': 19   // S
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

**Resultado:** quando vendedor mudar status pra MQL → data_mql preenche sozinho. Idem pra SQL e Cliente.

### Solução B — Fórmula (mais simples, mas exige clicar manualmente em cada linha)

Não recomendo. Use Apps Script.

---

## 4. Formatação Condicional (visual do funil)

Aplique em **toda a linha** (A:X) baseado no valor da coluna P (status):

| Status | Cor de fundo |
|--------|--------------|
| `Lead` | Cinza claro (#f3f3f3) |
| `MQL` | Amarelo claro (#fff2cc) |
| `SQL` | Laranja claro (#fce5cd) |
| `Cliente` | Verde claro (#d9ead3) |
| `Perdido` | Vermelho claro (#f4cccc) |

**Como configurar:**
1. Selecione A2:X (até onde for usar)
2. Formatar → Formatação condicional → Adicionar regra
3. Tipo: "A fórmula personalizada é"
4. Fórmula: `=$P2="MQL"` (substitua pelo status)
5. Estilo: cor de fundo correspondente
6. Repita pra cada status

---

## 5. Proteções de coluna

### Bloquear edição manual de colunas automáticas
- **A `lead_id`** → bloquear (apenas n8n / Apps Script escreve)
- **B `data_lead`** → bloquear
- **C `origem`** → bloquear
- **Q, R, S `data_mql/sql/venda`** → bloquear (fórmula preenche)
- **X `sincronizado_capi`** → bloquear

**Como:** Dados → Proteger intervalos → adicionar exceção pra essas colunas, permitir edição só pra você (admin).

---

## 6. Mapeamento de dados antigos → novos

Pra migrar os 8 leads atuais sem perder informação:

| Coluna antiga | Coluna nova | Transformação |
|---------------|-------------|---------------|
| Data + Hora | `data_lead` | Combinar em um único timestamp |
| Nome | `nome` | direto |
| E-mail | `email` | direto |
| WhatsApp | `whatsapp` | direto |
| Seu Ambiente | `ambiente` | direto |
| Sua metragem | `metragem` | direto |
| utm_* | utm_* | direto |
| OBSERVAÇÃO | `observacao` | direto (parte vira `motivo_perdido` se for caso de perda) |
| CONEXÃO (checkbox) | (descartar) | a coluna `status` substitui — se CONEXÃO=true e nenhum status posterior, status="Lead" |
| MQL (checkbox) | `status` | se checked, status = "MQL" |
| SQL (checkbox) | `status` | se checked, status = "SQL" (sobrescreve MQL) |
| VENDA (checkbox) | `status` | se checked, status = "Cliente" (sobrescreve) |
| PERDIDO/FORA DO PERFIL | `status` | se checked, status = "Perdido", preencher motivo_perdido |
| FATURAMENTO | `faturamento` | direto |
| (não existia) | `lead_id` | gerar manualmente para histórico (ex.: `HIST-001`, `HIST-002`...) |
| (não existia) | `origem` | inferir: aba LP → "LP - carpete-em-placas", aba FORMS → "FB Form - Pegasus" |

---

## 7. Validações adicionais (Data → Validação de dados)

| Coluna | Tipo de validação | Regra |
|--------|------------------|-------|
| E `email` | Texto contém | `@` |
| F `whatsapp` | Texto comprimento | mínimo 10 caracteres |
| V `faturamento` | Número | maior que 0 |
| T `motivo_perdido` | Customizado | Se P="Perdido" → obrigatório preencher |

---

## 8. Permissões de compartilhamento

❌ **NUNCA**: "Qualquer pessoa com o link"
✅ **Sempre**: "Restrito" + emails específicos
✅ Editores: vendedor responsável, coordenador
✅ Visualizadores: gestor de tráfego, líder

---

## 9. Próximos passos após criar a planilha

1. [ ] Estrutura criada conforme template
2. [ ] Dropdowns configurados (validação de dados)
3. [ ] Apps Script de datas automáticas instalado
4. [ ] Formatação condicional aplicada
5. [ ] Permissões revisadas (restrito)
6. [ ] 8 leads migrados da estrutura antiga
7. [ ] Workflow n8n adaptado para escrever na nova aba
8. [ ] Apps Script de Purchase event (será fornecido depois)
9. [ ] Teste end-to-end com 1 lead

---

## 10. Como o ciclo completo funciona

```
[Lead vem da LP ou FB Form]
        ↓
[n8n escreve linha na aba `Leads`]
   - lead_id preenchido
   - status = "Lead" (default)
   - ambiente e metragem chegam do form
        ↓
[Se ambiente ≠ residencial AND metragem ≥ 50m² → vendedor muda status para "MQL"]
   - data_mql preenche automaticamente
        ↓
[Vendedor entra em contato, qualifica → status = "SQL"]
   - data_sql preenche automaticamente
        ↓
[Negócio fecha → status = "Cliente"]
   - data_venda preenche automaticamente
   - vendedor preenche `faturamento`
   - Apps Script dispara Purchase event para SSGTM
   - SSGTM envia para Meta + Google + GA4
   - Coluna sincronizado_capi vira ✅
```

OU

```
[Negócio não fecha → status = "Perdido"]
   - vendedor preenche motivo_perdido (obrigatório)
   - vendedor preenche observacao (opcional)
   - Não envia evento aos pixels (correto)
```

---

## 11. Reports que essa estrutura habilita

- **Funil de conversão por origem:** Lead → MQL → SQL → Cliente por LP vs FB Form
- **Tempo médio de cada etapa:** (data_mql - data_lead), (data_venda - data_lead)
- **Motivos de perda:** % de leads perdidos por motivo
- **Performance por vendedor:** taxa de conversão SQL → Cliente
- **Atribuição:** ROAS por utm_campaign / utm_source
- **Ticket médio:** AVG(faturamento) onde status=Cliente
- **EMQ no Meta:** vai subir porque o `lead_id` cruza com pixel/CAPI

---

**Dúvidas? Próximo passo é gerar a planilha física com essa estrutura ou aplicar tudo na atual.**
