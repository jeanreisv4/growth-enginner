# Ferramentas

Configuração local: `~/.config/sprint-growth/config.json` (chmod 600, fora do repositório). Formato:

    {"mcp": {"googleads_diretas": {"url": "...", "bearer_arquivo": "~/..."},
             "googleads_squad": {...}, "googleads_nayara": {...},
             "gtm": {"url": "..."}, "ga4admin": {"url": "..."}},
     "escrita_ads": {"diretas": {"url_arquivo": "~/...", "chave_arquivo": "~/..."}, "squad": {...}, "nayara": {...}},
     "n8n": {"base": "https://.../api/v1", "chave_arquivo": "~/..."}}

| Área | Ferramenta | Uso | Limites conhecidos |
| --- | --- | --- | --- |
| Google Ads leitura | MCP n8n (`mcp_http.MCP("googleads_*")`) | GAQL livre, conversões com rótulo, hierarquia de MCC | um endpoint por MCC; conta direta vs sob MCC; change_event só 30 dias; resposta grande pode cortar |
| Google Ads escrita | webhook n8n (`mcp_http.escrita_ads`) | mutate (validateOnly por padrão), upload, histórico/ideias | upload de conversão bloqueado em conta nova; Planejador exige acesso Basic |
| GTM | MCP n8n `gtm` | listar/editar tags, variáveis, versões, publicar | publicar pede ok; workspace muda depois de versionar |
| GA4 dados | `analytics-mcp` | relatórios, eventos por página | — |
| GA4 admin | MCP n8n `ga4admin` | eventos principais, vínculo com Ads, dimensões | corpo dos recursos vai como objeto |
| Meta | exports CSV do gerenciador (ou conector claude.ai, se autorizado) | gasto e resultado por anúncio | export pode vir filtrado; conferir IDs |
| Páginas | `curl` + `teste_formulario.py` / `teste_disparo.py` (Playwright via `uvx`) | on-page, envio do formulário, disparo das tags | PageSpeed API tem cota diária |
| Documento | Claude Docs | aba de diagnóstico, aba Executado, gráficos e desenhos | — |
| Mercado | Agent (general-purpose) em segundo plano | concorrentes, preços, trial | conferir à mão os preços decisivos |

## DataCrazy (CRM)
- API https://api.g1.datacrazy.io/api/v1, Bearer. **Exige User-Agent de curl** (urllib padrão → 403).
- /businesses, /leads, /conversations: take ≤ 500 + skip. /business-loss-reasons, /pipelines/{id}/stages.
- /leads/{id}/history: **sem take/skip** (com eles volta vazio); **30 req/min**. Eventos: business-created/moved
  (oldStage/newStage)/won/loss, lead-tag-added (autor = quem etiquetou), conversation-*.
- /conversations traz `instance.config` com o **token do WhatsApp** do cliente: nunca gravar em arquivo (conversas.py remove).
- Origem de anúncio de clique para WhatsApp: `sourceReferral` (sourceId, sourceUrl, ctwaId) na conversa, só com a
  automação de tracking ligada (artigo 10670775 do help DataCrazy). Docs: https://docs.datacrazy.io/llms.txt
