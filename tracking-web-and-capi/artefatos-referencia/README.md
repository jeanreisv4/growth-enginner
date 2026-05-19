# Artefatos de Referência

> Arquivos do caso piloto **WK Carpetes** usados como referência canônica.
> Não são templates plug-and-play — são exemplos reais para inspiração.

## Conteúdo

### Documentação do caso
- `conversa-inicial.md` — resumo da conversa que originou todo o projeto (briefing pros próximos chats)
- `caso-wk-carpetes.md` — documentação detalhada do caso WK (decisões, valores, estrutura)

### Planilha (storage de leads)
- `setup-planilha-automatico.gs` — Apps Script que monta a planilha inteira em 1 clique
- `template-leads-WK.csv` — cabeçalhos da aba `Leads` (24 colunas)
- `template-dropdowns-WK.csv` — valores controlados (origem, ambiente, metragem, status, motivo)
- `INSTRUCOES-importar-planilha-WK.md` — passo a passo manual (caso queira sem Apps Script)
- `template-planilha-leads-WK.md` — documentação completa do schema

### GTM (containers)
- `gtm/GTM-KG7X38D6_workspace4_FIXED.json` — container Web pronto (Pixel, GA4, Google Ads, CAPI relay)
- `gtm/GTM-PNKWBGFC_workspace2_BUILT.json` — container Server (Meta CAPI deduplicado)

### Scripts auxiliares (Python — usados nos ajustes)
- `scripts/fix_gtm_container.py` — aplica correções no JSON do GTM Web
- `scripts/add_values_to_tags.py` — adiciona value+currency nas tags de conversão
- `scripts/fix_web_sessionstorage.py` — adiciona tag HTML de persist + reescreve variáveis JS
- `scripts/build_server_gtm.py` — constrói o JSON do GTM Server do zero
- `scripts/improve_emq.py` — adiciona external_id, country, state para subir EMQ

---

## Como usar estes arquivos

Quando estiver implementando tracking para **um novo cliente sem CRM** (Implementação A — Sheets):

1. **Leia** `caso-wk-carpetes.md` para entender o padrão completo
2. **Adapte** `setup-planilha-automatico.gs` com:
   - Nomes dos vendedores do cliente (aba Configuracao)
   - Critérios MQL específicos do nicho do cliente
3. **Use** os scripts Python como inspiração — adaptar os IDs (Pixel, Google Ads, GA4) pro cliente
4. **Importe** os JSONs do GTM como template, e ajuste:
   - IDs de Pixel, Google Ads, GA4
   - URL do SSGTM (do cliente)
   - Critérios MQL (variáveis JS)

⚠️ **Nunca importe direto sem ajustar IDs.** Os JSONs têm IDs do WK Carpetes.

---

## Limitações conhecidas (do caso WK)

- ❌ Custom domain SSGTM pendente (cliente sem acesso ao DNS)
- ❌ Back-pass de Purchase (Apps Script) ainda em construção
- ❌ Workflow n8n ainda não adaptado para nova planilha
- ⚠️ Token CAPI foi exposto várias vezes em prints durante a implementação (lições aprendidas)
