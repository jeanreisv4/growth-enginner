# Playbook — Caso WK Carpetes (Implementação A: Sheets)

> Caso piloto real. Cliente de carpetes B2B sem CRM. Usado como referência canônica.

**Status:** 📝 Em construção (estrutura base — conteúdo a expandir)
**Cliente:** WK Carpetes
**Data:** 2026-05-17
**Implementação:** A (Google Sheets)

---

## Contexto do cliente

- **Segmento:** B2B
- **Nicho:** inside-sales (venda consultiva)
- **Produto:** carpete em placas (corporativo, hotelaria, institucional)
- **Ticket médio:** R$ 12.000
- **Margem bruta:** ~35% (estimativa)
- **CRM:** não tem (usa planilha Google Sheets)

## Stack implementada

- **GTM Web:** `GTM-KG7X38D6`
- **GTM Server:** `GTM-PNKWBGFC` via stape.io
- **SSGTM URL:** `https://whhhlqap.sac.stape.io`
- **Meta Pixel:** `444617535160623`
- **Google Ads:** `1066377963`
- **GA4:** `G-SQ2HXLBL2E`

## Critérios MQL (qualificação na LP)

Lead vira MQL automaticamente se:
- `ambiente` ≠ "residencial (quarto, sala, home office)"
- `metragem` ∈ {"entre 50 e 75m²", "entre 75 e 100m²", "acima de 100m²"}

## Valores proxy (Modelo A — lucro)

| Evento | Google Ads | Meta Ads | GA4 |
|--------|-----------|----------|-----|
| Lead | R$ 190 | R$ 120 | R$ 150 |
| MQL | R$ 630 | R$ 400 | R$ 500 |

Cálculos baseados em:
- Lucro/venda: R$ 12.000 × 35% = R$ 4.200
- Taxa MQL→SQL Google: 50% (taxa real do cliente)
- Taxa MQL→SQL Meta: 31,81% (taxa real do cliente)
- Demais taxas: benchmark (Lead→MQL 30%, SQL→Venda 30%)

## Implementação

> **TODO próximo chat:** detalhar passo a passo com prints reais

### Fase 1 — GTM Web
- Importar JSON: `artefatos-referencia/gtm/GTM-KG7X38D6_workspace4_FIXED.json`
- Tag HTML "Persist Form Data" salva dados do form em sessionStorage
- Trigger Lead/MQL na página `/obrigado`
- Advanced Matching: ph + fn + em

### Fase 2 — GTM Server
- Container ID: `GTM-PNKWBGFC`
- Template instalado: Facebook Conversion API (stape-io)
- 4 tags Meta CAPI: PageView, Lead, Contact, MQL
- ⚠️ `inheritEventName: "override"` (não BOOLEAN!) + setar `eventNameStandard/Custom`

### Fase 3 — Stape
- Plano: Free (10k req/mês)
- URL: `https://whhhlqap.sac.stape.io`
- Domínio custom: pendente (aguardando DNS do cliente)

### Fase 4 — Planilha
- Nova planilha com estrutura padrão (24 colunas)
- Apps Script automático cria estrutura + dropdowns + cores + datas automáticas
- Aba `Configuracao` com listas
- Permissão: restrito (LGPD)

### Fase 5 — Back-pass Purchase
- **PENDENTE:** Apps Script que detecta status=Cliente e envia Purchase pro SSGTM
- Será desenvolvido em chat separado

## Resultados após go-live

- EMQ: **8.0/10** (Lead e MQL) — depois de quick wins: 9.5/10 esperado
- Dedup Browser+Server: ✅ funcionando
- Eventos chegando no Meta, Google e GA4: ✅
- Custo extra mensal: R$ 0 (stape Free + planilha Google)

## Aprendizados (lições da implementação real)

1. **Template do stape com `inheritEventName: true` (BOOLEAN) não funciona** — usar string `"override"` + setar event names manualmente
2. **Trigger `gtm.formSubmit` falha em LPs AJAX** (landingpage.app.br é caso) — usar PAGEVIEW `/obrigado`
3. **Variáveis JS no DOM falham na /obrigado** (form não existe lá) — usar sessionStorage via tag HTML no submit
4. **Token CAPI em screenshots é vazamento real** — operadores precisam de treinamento sobre isso
5. **Test Event Code esquecido em produção = todos os eventos viram teste** — verificar SEMPRE antes de publicar

## Próximos passos (do projeto WK)

1. [ ] Finalizar Apps Script de Purchase
2. [ ] Adaptar n8n pra escrever na nova planilha
3. [ ] Migrar 8 leads históricos
4. [ ] Renomear abas antigas como [HISTÓRICO]
5. [ ] Configurar custom domain `gtm.wkcarpetes.com.br` quando tiver DNS
6. [ ] Regenerar token Meta (vazou várias vezes em prints)
7. [ ] Validar EMQ subiu para 9.5+ após quick wins
