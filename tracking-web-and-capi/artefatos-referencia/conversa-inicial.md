# Conversa Inicial — Origem do Projeto Padrão de Tracking

> Resumo executivo da conversa que originou todo o projeto.
> Use como briefing pros próximos chats no Cursor / Claude Code.

**Data:** 2026-05-17
**Participantes:** Jean Reis (Growth/Mídia Paga V4) + Claude (Opus 4.7)

---

## Como tudo começou

A conversa começou como um pedido simples de validação de tracking GTM do cliente WK Carpetes. Ao longo de várias horas, evoluiu para implementação completa (GTM Web + Server + dedup Browser/CAPI + EMQ + planilha + auditoria).

No final, o Jean identificou que a dor real **não é o cliente WK** — é a **falta de padrão na operação de 200 pessoas da V4 Company**. Cada operador faz tracking do seu jeito, cada cliente fica num nível diferente.

A decisão: usar o setup do WK como **caso piloto canônico**, construir um padrão a partir dele, criar aula obrigatória e Skill no Claude Code pra auditar.

---

## O que foi feito tecnicamente (WK Carpetes)

### Stack implementada e em produção
- GTM Web `GTM-KG7X38D6` (v6 publicada)
- GTM Server `GTM-PNKWBGFC` via stape.io (Free)
- SSGTM URL: `https://whhhlqap.sac.stape.io`
- Meta Pixel + CAPI deduplicados via `event_id`
- Google Ads (Lead + MQL como conversions)
- GA4 (Web + relay via SSGTM)

### Funcionalidades
- ✅ Lead, MQL, PageView, Contact (WhatsApp) — todos disparando
- ✅ MQL automatizado por critério da LP (ambiente ≠ residencial AND metragem ≥ 50m²)
- ✅ Trigger Lead na `/obrigado` (não no `gtm.formSubmit`, que falha em forms AJAX)
- ✅ Values diferenciados por canal (Modelo A — lucro proxy)
- ✅ Advanced Matching: em + ph + fn + external_id + country + state (EMQ 8.0/10 → 9.5 esperado)
- ✅ Tag HTML que persiste form data em sessionStorage no submit
- ✅ Planilha nova com Apps Script automático (dropdown, cores, datas auto)

### Bug crítico descoberto
Template **Facebook Conversion API (stape-io)** tem parâmetro `inheritEventName` que é **SELECT** (`"inherit" | "override"`), **NÃO BOOLEAN**. Setar como BOOLEAN `true` faz a tag não enviar `event_name`. Meta retorna 400 "event_name is required". Fix: usar string `"override"` + setar `eventNameStandard` ou `eventNameCustom`.

---

## Valores proxy calculados (Modelo A — lucro)

Base WK:
- Ticket médio: R$ 12.000
- Margem bruta: 35% (lucro/venda = R$ 4.200)
- Taxa MQL→SQL Google Ads: 50% (real)
- Taxa MQL→SQL Meta Ads: 31,81% (real)
- Taxa Lead→MQL: 30% (benchmark)
- Taxa SQL→Venda: 30% (benchmark)

Resultado (por canal):

| Evento | Google Ads | Meta Ads | GA4 |
|--------|-----------|----------|-----|
| Lead | R$ 190 | R$ 120 | R$ 150 |
| MQL | R$ 630 | R$ 400 | R$ 500 |
| SQL | (futuro via back-pass) |  |  |
| Purchase | (futuro via back-pass) |  |  |

---

## Decisões arquiteturais importantes

1. **Trigger Lead = página /obrigado** (PAGEVIEW), não `gtm.formSubmit` (falha em AJAX)
2. **sessionStorage** para persistir form data entre LP e /obrigado (variáveis JS no DOM falham)
3. **inheritEventName: "override"** no template Meta CAPI (não `true`)
4. **Status como dropdown único** (Lead/MQL/SQL/Cliente/Perdido), não checkboxes
5. **motivo_perdido** como coluna separada de **observacao** (lista vs texto livre)
6. **1 aba `Leads` unificada** (origem distingue LP vs FB Form vs WhatsApp)
7. **Stape Free** suficiente pra maioria dos clientes da V4 Company
8. **Custom domain** opcional (recomendado quando tiver DNS)
9. **1 skill com 3 modos** (planejar, auditar, troubleshoot) > 2 skills separadas

---

## Pendências do caso WK (não bloqueiam o projeto padrão)

- [ ] Migrar 8 leads históricos pra nova planilha
- [ ] Adaptar workflow n8n pra escrever na aba `Leads` unificada
- [ ] Construir Apps Script `onEdit` que envia Purchase pro SSGTM quando status=Cliente
- [ ] Configurar custom domain `gtm.wkcarpetes.com.br` (aguardando DNS)
- [ ] Regenerar token Meta (foi exposto várias vezes em prints)
- [ ] Validar EMQ subiu pra ~9.5/10 após quick wins

---

## Mapa do projeto padrão (próximos chats)

### Próximos chats sugeridos

| Chat | Foco | Input pro Claude |
|------|------|------------------|
| **2** | Adaptar n8n do WK | Workflow n8n exportado + canonico/padrao-tracking.md |
| **3** | Apps Script Purchase do WK | playbook/caso-WK.md + canonico/padrao-tracking.md |
| **4** | Construir canonico/padrao-tracking.md completo | conversa-inicial.md + caso-WK |
| **5** | Construir implementacoes/sheets.md completo | caso-WK |
| **6** | Implementacoes/crm-kommo.md | Brief de cliente real ou fictício |
| **7** | Aula slides.html final | canonico + playbooks completos |
| **8** | Piloto da aula (refino) | Feedback dos primeiros operadores |

### Princípio dos próximos chats

Cada chat **lê o que está em `growth-engineer/`** primeiro, faz **uma coisa específica**, e atualiza os arquivos correspondentes.

---

## Aprendizados importantes pra próximos clientes

1. **Token CAPI em screenshots = vazamento real** — operadores precisam aprender isso na aula
2. **Test Event Code esquecido em produção** = todos os eventos viram teste — incluir no checklist
3. **`inheritEventName: true` (BOOLEAN) não funciona no template stape** — incluir nos erros conhecidos
4. **`gtm.formSubmit` falha em forms AJAX** (landingpage.app.br é caso) — sempre usar /obrigado
5. **Variáveis JS no DOM falham na /obrigado** (form não existe lá) — sempre usar sessionStorage
6. **Apps Script automático > config manual** — pro tempo de implementação cair
