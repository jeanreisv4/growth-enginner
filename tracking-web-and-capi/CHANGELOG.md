# Changelog — tracking-web-and-capi

## v1.1.0 — 2026-09-28

Aprendizados de cinco sprints growth (SaaS de obra, indústria, brindes, distribuidora de peças, móveis planejados)
e de auditorias de GTM levados para a skill, e o repositório público limpo de dados do cliente piloto.

### Segurança
- **Nenhum ID de cliente no repositório.** Os containers do piloto viraram `templates/gtm/web.json` e
  `templates/gtm/server.json`, com marcadores (`__META_PIXEL_ID__`, `__LABEL_LEAD__`, `__SSGTM_URL__`,
  `__REGRA_MQL__`...) no lugar de Pixel, Google Ads, GA4, rótulos, Stape, domínio, Clarity e Test Event Code. O caso
  real fica em `clientes/` (git local, fora da cópia pública). A seção 11 do checklist deixou de listar os IDs
  reais e passou a exigir container gerado pelo template.
- O brief do gerador recusa token da CAPI: o token vai direto no GTM Server.

### Adicionado
- `scripts/gerar_containers.py`: preenche os marcadores a partir do brief e valida antes de entregar. Bloqueia
  marcador sobrando, formato de Pixel/Ads/GA4, rótulo vazio, só com dígitos (ID e rótulo trocados) ou repetido, URL
  do servidor de exemplo ou sem https, Test Event Code em produção, seletor vazio, contagem de pastas e tags,
  `inheritEventName` diferente de `"override"`. Sem critério de MQL, tira tags, variável e acionador de MQL.
- `templates/brief_exemplo.json` e `templates/planilha/` (planilha de leads e Apps Script, sem dado do piloto).
- `referencias/armadilhas.md`: 25 erros vistos em cliente em quatro grupos (tags e containers, página e
  consentimento, conta de anúncios e GA4, volta da venda), cada um com como detectar e o que fazer.
- `tests/regressao.py`: 36 casos sem rede (anonimato dos templates, cada validação, sem MQL, Clarity, a regra de
  MQL executada em JavaScript, CLI ponta a ponta).
- `README.md` com o desenho do workflow (três modos, saída de cada fase na seta, o loop fechando em
  "erro novo vira armadilha e teste").
- `playbook/caso-piloto-carpetes.md`: o caso piloto sem identificadores.

### Alterado
- `latest.md`: Fase 4 pelo gerador; Modo 2 com os testes automáticos da `sprint-growth` (`gtm_auditoria.py`,
  `teste_disparo.py`, `teste_formulario.py`) e as MCPs do n8n; 10 erros novos na tabela do troubleshoot.
- `canonico/checklist-auditoria.md`: seções 12 (conta de anúncios e GA4) e 13 (origem até o CRM e volta da venda).
- `SKILL.md`: versão, ferramentas, regras de segurança e fechamento.
- Removidos `v1.0.0.md` (fica na tag `v1.0.0`) e `artefatos-referencia/` (virou `templates/` e `clientes/`).

## v1.0.0 — 2026-05-17

### Adicionado
- Skill inicial com 3 modos: planejar, auditar, troubleshoot
- Contrato de dados (canonico/padrao-tracking.md) — em construção
- Checklist de auditoria (canonico/checklist-auditoria.md) — em construção
- Implementação A (Sheets) — em construção, baseada no caso piloto
- Implementação B (CRM Kommo) — em construção
- Playbook caso cliente piloto (carpetes B2B) — em construção
- Aula teórica em slides — em construção
- Base de conhecimento de erros conhecidos (em latest.md)

### Refinamento — 2026-05-17 (pós-criação)

- **Skill renomeada** para `tracking-web-and-capi` (era `tracking-stack`; passou brevemente por `tracking-inside-sales-web-and-api`). Nome final reflete escopo geral: web pixel + CAPI server, aplicável a qualquer nicho.
- **Terminologia corrigida**: "agência" → "V4 Company" em 10 referências internas (V4 é assessoria, não agência). Mantida apenas em `aula/slides.md` L22 onde o contexto é mercado em geral.
- **MODO 1 — Fase 1, Bloco D ampliado** (de 4 inputs para 7 sub-blocos):
  - D.1 Identificadores das plataformas (Pixel, Google Ads, GA4)
  - D.2 Conversion Labels (Lead, MQL, Contact)
  - D.3 Meta CAPI (Access Token com aviso de segurança + Test Event Code)
  - D.4 SSGTM (URL, plano, custom domain)
  - D.5 Cliente (domínio, LP, obrigado, WhatsApp)
  - D.6 Selectors do form
  - D.7 Critério MQL (com opção "não aplicável")
- **MODO 1 — Fase 4 reescrita** como "Geração dos JSONs (Web + Server)":
  - Princípio canônico explícito (nomenclatura, emojis e estrutura de pastas **não mudam** entre clientes)
  - Mapa formal de substituição Web (13 placeholders → Bloco D)
  - Mapa formal de substituição Server (4 placeholders → Bloco D)
  - 5 validações pré-entrega obrigatórias (grep zero-placeholder, contagem de tags, emojis presentes, JSON válido, `inheritEventName: "override"`)
  - Entrega definida: `gtm-web-<cliente>.json` + `gtm-server-<cliente>.json` + resumo auditável
- **Checklist de auditoria — Seção 11 nova**: "Templates limpos (zero placeholder do piloto)" com 11 itens, todos bloqueantes. Previne vazamento de IDs/tokens/selectors do piloto em outros clientes.
- **v1.0.0.md sincronizado** com latest.md (mesma versão durante a fase de construção).

### Notas
- Versão inicial baseada no caso piloto cliente piloto (carpetes B2B)
- Artefatos de referência em `artefatos-referencia/`
- Conteúdo de canonico/ e implementacoes/ a ser preenchido nas próximas iterações
