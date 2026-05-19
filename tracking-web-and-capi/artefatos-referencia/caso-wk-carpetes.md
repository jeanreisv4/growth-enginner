# Caso WK Carpetes — Documentação Detalhada

> Referência canônica do caso piloto. Use pra entender padrão completo.

**Cliente:** WK Carpetes
**Segmento:** B2B / inside-sales
**Implementação:** A (Google Sheets, sem CRM)
**Data:** 2026-05-17

---

## IDs e credenciais (placeholders)

| Item | Valor |
|------|-------|
| GTM Web | `GTM-KG7X38D6` |
| GTM Server | `GTM-PNKWBGFC` |
| SSGTM URL | `https://whhhlqap.sac.stape.io` |
| Meta Pixel | `444617535160623` |
| Google Ads | `1066377963` |
| GA4 | `G-SQ2HXLBL2E` |
| Conversion Label Lead | `u7Y1CP2rlZccEOvFvvwD` |
| Conversion Label MQL | `6ZwcCOztp64cEOvFvvwD` |
| Conversion Label WhatsApp | `KG5qCLWhj5ccEOvFvvwD` |
| Token Meta CAPI | ⚠️ rotacionado várias vezes — vazou em prints |

## URL da LP

`https://lp.wkcarpetes.com.br/carpete-em-placas`
Plataforma: **landingpage.app.br**

## Selectors do form (LP)

```
input[name="seu-nome"]
input[name="seu-e-mail"]
input[name="seu-telefonewhatsapp"]
select[name="seu-ambiente"]
select[name="sua-metragem"]
```

## Critérios MQL (qualificação automática)

Lead vira MQL quando:
- `ambiente` ≠ `residencial (quarto, sala, home office)` E
- `metragem` ∈ `{entre 50 e 75m², entre 75 e 100m², acima de 100m²}`

## Página de obrigado

`https://lp.wkcarpetes.com.br/obrigado`

WhatsApp configurado: `+55 11 97626-2557` (após correção do placeholder `5511000000000`)

## Funil e valores (Modelo A — lucro proxy)

| Etapa | Definição | Valor Google | Valor Meta | Valor GA4 |
|-------|-----------|-------------|-----------|-----------|
| Lead | submit form | R$ 190 | R$ 120 | R$ 150 |
| MQL | qualificou na LP | R$ 630 | R$ 400 | R$ 500 |
| SQL | qualificou no comercial | (futuro) | (futuro) | (futuro) |
| Cliente | venda fechada | lucro real | lucro real | receita real |

Taxas reais coletadas do cliente:
- MQL → SQL Google: **50%**
- MQL → SQL Meta: **31,81%**
- Demais: benchmark (30%)

## Eventos disparando

| Evento | Trigger | Tags |
|--------|---------|------|
| PageView | All Pages | GA4, Google Ads, Meta Pixel, CAPI |
| Lead | Page URL `/obrigado` | GA4, Google Ads, Meta Pixel, CAPI |
| MQL | Page URL `/obrigado` AND `cJS - is_mql = true` | GA4, Google Ads, Meta Pixel, CAPI |
| Contact | Click URL contém `wa.me/` OU `api.whatsapp.com/send` | GA4, Google Ads, Meta Pixel, CAPI |

## Aprendizados (gravar pro próximo chat sempre lembrar)

### Bug crítico do template Meta CAPI (stape-io)
`inheritEventName` é **SELECT** com valores `"inherit"` ou `"override"`, NÃO BOOLEAN.
Setar `inheritEventName: true` quebra silenciosamente (event_name nunca é enviado).
**Fix:** sempre setar `inheritEventName: "override"` + `eventName: "standard"` + `eventNameStandard: "PageView/Lead/Contact"` ou `eventName: "custom"` + `eventNameCustom: "MQL"`.

### Trigger Lead na /obrigado, não no formSubmit
`gtm.formSubmit` é nativo do GTM mas FALHA em forms AJAX (caso landingpage.app.br).
**Fix:** usar trigger PAGEVIEW filtrando por `Page URL contém /obrigado`.

### sessionStorage para persistir dados do form
Variáveis JS com `querySelector` no DOM falham na /obrigado (form não existe lá).
**Fix:** tag HTML no submit → salva nome/email/whatsapp/ambiente/metragem em `sessionStorage.wk_lead_data`.
Variáveis JS leem do sessionStorage.

### Quick wins EMQ (8.0 → 9.5)
Adicionar em `user_data` do CAPI:
- `external_id` = client_id do GA4 (via Event Data)
- `country` = `br` (hardcoded — cliente só vende BR)
- `st` (state) = `event_location.region` (vem do GA4 geo)

### Test Event Code
Adicionado pra validar dedup Browser+Server. **OBRIGATÓRIO apagar antes de produção.**
Se ficar em produção, todos eventos viram teste e não contam como conversão.

### Token CAPI em prints é vazamento real
Aconteceu várias vezes durante a implementação. Tokens precisam ser rotacionados após qualquer exposição.

---

## Pendências (do caso WK específico, não bloqueiam o padrão)

1. [ ] Apps Script `onEdit` que envia Purchase pro SSGTM quando status=Cliente
2. [ ] Adaptar workflow n8n pra escrever na aba `Leads` unificada
3. [ ] Migrar 8 leads históricos das abas antigas (LP 1 - MQL V1 + FORMS - MQL V1)
4. [ ] Custom domain `gtm.wkcarpetes.com.br` (aguardando DNS do cliente)
5. [ ] Regenerar token Meta CAPI final (em prod) — após validação

## Estrutura da planilha do cliente

**Nova planilha:** `[OFICIAL] Leads - WK Carpetes`
**ID:** `1HkLg9806RLXVfoOSFuPgDQq3o2gLwxU9M037ScVceAg`

24 colunas, 1 aba `Leads` + 1 aba `Configuracao` (dropdowns).
Configurada via `setup-planilha-automatico.gs` em 1 clique.

## Workflow n8n (cliente)

URL: `https://automation.opscap.collieassociados.com/workflow/FEaBKVCghE04vfi7`
Fonte de leads: Meta Lead Ads (FORMS - MQL V1)
Pendente: adaptar pra escrever na nova aba `Leads`.
