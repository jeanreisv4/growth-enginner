---
name: tracking-web-and-capi
description: Planejar, auditar e diagnosticar tracking web e server-side para clientes, cobrindo GTM Web, GTM Server, Stape, Meta Pixel/CAPI, Google Ads, GA4, Google Sheets, Apps Script, n8n e CRM. Use quando precisar implementar tracking do zero, validar setup antes do go-live ou investigar problemas de eventos, deduplicação, EMQ, conversões, CRM e planilhas.
---

# Tracking Web And CAPI

**Versão 1.1.1 (28/09/2026).** Histórico em `CHANGELOG.md`; desenho do fluxo em `README.md`. Caminhos relativos à
pasta da skill. Dados de cliente em `clientes/<cliente>/` (git local, fora da cópia pública).

## Fonte Principal

Esta skill usa [latest.md](latest.md) como protocolo operacional completo.

Arquivos de apoio:

- [referencias/armadilhas.md](referencias/armadilhas.md): erros já vistos em cliente, com como detectar e o que fazer. **Ler antes de qualquer modo.**
- [PLAYBOOK_TRACKING_ORIENTADO_A_SKILL.md](PLAYBOOK_TRACKING_ORIENTADO_A_SKILL.md): guia prático de uso da skill por modo.
- [context.md](context.md): propósito, escopo, modos e inputs esperados.
- [canonico/padrao-tracking.md](canonico/padrao-tracking.md): padrão canônico de tracking.
- [canonico/checklist-auditoria.md](canonico/checklist-auditoria.md): checklist de auditoria.
- [implementacoes/crm-kommo.md](implementacoes/crm-kommo.md) e [implementacoes/sheets.md](implementacoes/sheets.md).
- [playbook/caso-piloto-carpetes.md](playbook/caso-piloto-carpetes.md): o caso que originou os templates.

Ferramentas:

- `templates/gtm/web.json` e `templates/gtm/server.json`: containers canônicos com marcadores; `templates/brief_exemplo.json`: o brief.
- `scripts/gerar_containers.py`: preenche os marcadores a partir do brief e valida (bloqueia rótulo trocado, URL de exemplo, Test Event Code em produção...).
- Da skill irmã `sprint-growth` (mesma pasta): `gtm_auditoria.py`, `teste_disparo.py`, `teste_formulario.py` e as MCPs do n8n (GTM, Google Ads, GA4 Admin).
- `tests/regressao.py`: rodar depois de qualquer mudança em template ou script.

## Regra De Uso

Ao ser acionada, ler primeiro [latest.md](latest.md) e perguntar o modo:

1. `planejar`: implementar tracking para cliente novo ou do zero.
2. `auditar`: validar setup existente antes do go-live.
3. `troubleshoot`: diagnosticar algo que não está funcionando.

Não assumir valores críticos. Pedir IDs, URLs, labels, CRM, stack, selectors, eventos e evidências conforme o modo escolhido.

Nunca: token da CAPI em arquivo, brief, chat ou print (vai direto no GTM Server); publicar GTM ou mexer em conta de
cliente sem ok explícito do usuário para aquela mudança; contornar o modo automático do Claude Code quando ele negar.

## Fechamento

Todo erro novo visto em cliente vai para `referencias/armadilhas.md` (e para a tabela de erros do `latest.md` e o
checklist, se couber); rode `python3 tests/regressao.py`, registre no `CHANGELOG.md`, commit e tag. Publicação:
`python3 scripts/publicar.py --destino <pasta>` e `--conferir <pasta>` antes do push.
