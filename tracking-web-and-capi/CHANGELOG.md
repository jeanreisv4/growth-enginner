# Changelog — tracking-web-and-capi

## v1.0.0 — 2026-05-17

### Adicionado
- Skill inicial com 3 modos: planejar, auditar, troubleshoot
- Contrato de dados (canonico/padrao-tracking.md) — em construção
- Checklist de auditoria (canonico/checklist-auditoria.md) — em construção
- Implementação A (Sheets) — em construção, baseada no caso WK
- Implementação B (CRM Kommo) — em construção
- Playbook caso WK Carpetes — em construção
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
- **Checklist de auditoria — Seção 11 nova**: "Templates limpos (zero placeholder do WK)" com 11 itens, todos bloqueantes. Previne vazamento de IDs/tokens/selectors do WK em outros clientes.
- **v1.0.0.md sincronizado** com latest.md (mesma versão durante a fase de construção).

### Notas
- Versão inicial baseada no caso piloto WK Carpetes
- Artefatos de referência em `artefatos-referencia/`
- Conteúdo de canonico/ e implementacoes/ a ser preenchido nas próximas iterações
