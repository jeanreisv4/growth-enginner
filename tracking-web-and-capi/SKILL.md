---
name: tracking-web-and-capi
description: Planejar, auditar e diagnosticar tracking web e server-side para clientes, cobrindo GTM Web, GTM Server, Stape, Meta Pixel/CAPI, Google Ads, GA4, Google Sheets, Apps Script, n8n e CRM. Use quando precisar implementar tracking do zero, validar setup antes do go-live ou investigar problemas de eventos, deduplicação, EMQ, conversões, CRM e planilhas.
---

# Tracking Web And CAPI

## Fonte Principal

Esta skill usa [latest.md](latest.md) como protocolo operacional completo.

Arquivos de apoio:

- [PLAYBOOK_TRACKING_ORIENTADO_A_SKILL.md](PLAYBOOK_TRACKING_ORIENTADO_A_SKILL.md): guia prático de uso da skill por modo.
- [context.md](context.md): propósito, escopo, modos e inputs esperados.
- [canonico/padrao-tracking.md](canonico/padrao-tracking.md): padrão canônico de tracking.
- [canonico/checklist-auditoria.md](canonico/checklist-auditoria.md): checklist de auditoria.
- [implementacoes/crm-kommo.md](implementacoes/crm-kommo.md): implementação com Kommo.
- [implementacoes/sheets.md](implementacoes/sheets.md): implementação com Google Sheets.

## Regra De Uso

Ao ser acionada, ler primeiro [latest.md](latest.md) e perguntar o modo:

1. `planejar`: implementar tracking para cliente novo ou do zero.
2. `auditar`: validar setup existente antes do go-live.
3. `troubleshoot`: diagnosticar algo que não está funcionando.

Não assumir valores críticos. Pedir IDs, URLs, labels, CRM, stack, selectors, eventos e evidências conforme o modo escolhido.
