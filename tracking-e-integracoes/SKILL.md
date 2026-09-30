---
name: tracking-e-integracoes
description: Tracking e integrações de growth do cliente, da página à venda de volta nas plataformas — GTM web e server (Stape), Meta Pixel/CAPI, Google Ads, GA4, Lead Ads do Meta direto no n8n (app próprio), formulário/LP → CRM (Kommo, RD Station CRM, HubSpot, Pipedrive, DataCrazy, NectarCRM, GoHighLevel), eventos de WhatsApp/Chatwoot, e a devolução das etapas do CRM (SQL, venda) ao Meta pela CAPI e ao Google Ads pela Data Manager API. Use para implementar tracking do zero, auditar antes do go-live, diagnosticar evento/conversão/deduplicação/EMQ, integrar formulário ou Lead Ads ao CRM, devolver dados do CRM para Meta e Google (inclusive os retroativos que ainda cabem na janela), montar as colunas de SQL e venda, descobrir leads que não entraram no CRM, ou revisar as automações do n8n de um cliente. Tem agentes por frente (CRM, Meta, Google Ads, conversacional).
---

# Tracking e Integrações

**Versão 2.1.0 (30/09/2026).** Antes `tracking-web-and-capi`. Histórico em `CHANGELOG.md`; desenho do fluxo em
`README.md`. Caminhos relativos à pasta da skill. Dados de cliente em `clientes/<cliente>/` (git local, fora da
cópia pública).

## Fonte Principal

[latest.md](latest.md) é o protocolo operacional completo. Arquivos de apoio:

- [referencias/armadilhas.md](referencias/armadilhas.md): erros já vistos em cliente, com como detectar e o que fazer. **Ler antes de qualquer modo.**
- [canonico/padrao-tracking.md](canonico/padrao-tracking.md) (contrato de dados) e [canonico/checklist-auditoria.md](canonico/checklist-auditoria.md).
- Implementações: [crm-kommo.md](implementacoes/crm-kommo.md) (devolução), [meta-lead-ads.md](implementacoes/meta-lead-ads.md)
  (app próprio, Lead Ads direto no n8n, recuperação), [google-ads-offline.md](implementacoes/google-ads-offline.md)
  (Data Manager), [conversacional-chatwoot.md](implementacoes/conversacional-chatwoot.md),
  [crm-conectores.md](implementacoes/crm-conectores.md) (contrato de CRM e pegadinhas de cada um), [sheets.md](implementacoes/sheets.md).
- [referencias/contrato_integracao.md](referencias/contrato_integracao.md): o que os agentes devolvem.
- [playbook/caso-piloto-carpetes.md](playbook/caso-piloto-carpetes.md), [PLAYBOOK_TRACKING_ORIENTADO_A_SKILL.md](PLAYBOOK_TRACKING_ORIENTADO_A_SKILL.md), [context.md](context.md).

Ferramentas:

- `scripts/gerar_containers.py` + `templates/gtm/`: containers canônicos com marcadores, preenchidos pelo brief e validados.
- `scripts/devolucao.py` + `templates/devolucao/nucleo.js`: devolução das etapas do CRM (Kommo → n8n → Meta direto ou
  pelo sGTM, Google pela Data Manager, id do lead do formulário buscado no Meta pelo telefone), do bloco `devolucao` do brief.
- `scripts/auditar_entrada.py`: formulário × CRM semana a semana e por origem (acha a semana em que a integração quebrou).
- `scripts/n8n_meta_leads.py`: leads dos formulários pela credencial de Lead Ads no n8n (sem nome/telefone completo).
- `scripts/retroativos.py`: etapas de antes da devolução que ainda cabem na janela (Meta 7 dias, Google 90/63), enviadas
  pela devolução no ar com a hora real da etapa (só com ok).
- `scripts/instalar_agentes.py`: instala os agentes `integracao-*` em `.claude/agents/` (fonte: `agentes/`).
- Da skill irmã `sprint-growth`: `gtm_auditoria.py`, `teste_disparo.py`, `teste_formulario.py`, `datacrazy.py` e as MCPs
  do n8n (GTM, Google Ads, GA4 Admin).
- `tests/regressao.py`: rodar depois de qualquer mudança.

## Regra De Uso

Ler [latest.md](latest.md) e perguntar o modo:

1. `planejar`: tracking de cliente novo ou do zero.
2. `auditar`: validar setup existente antes do go-live.
3. `troubleshoot`: diagnosticar o que não funciona.
4. `integrar`: entrada do lead no CRM (formulário, LP, Lead Ads, WhatsApp), devolução do CRM às plataformas, revisão
   das automações do cliente. Auditoria pelos agentes em paralelo: `integracao-crm`, `integracao-meta`,
   `integracao-google-ads`, `integracao-conversacional` (`python3 scripts/instalar_agentes.py --conferir` antes).

Não assumir valores críticos: pedir IDs, URLs, rótulos, CRM, etapas, seletores, eventos e evidências.

Nunca: segredo (token da CAPI, do CRM, chave de app, API do n8n) em arquivo do repositório, brief, chat ou print —
vai para `~/.config/<pasta>/` com `pbpaste >` ou direto na interface; publicar GTM, ligar workflow, gravar em CRM ou
conta de anúncios sem ok explícito do usuário para aquela mudança; excluir sem backup; ligar sem testar antes sem
gravar; contornar o modo automático do Claude Code quando ele negar (script por caminho absoluto em `~/Cursor/...` é
o caminho previsto).

## Fechamento

Todo erro novo visto em cliente vai para `referencias/armadilhas.md` (e para a tabela do `latest.md`, o checklist e o
guia de implementação, se couber); rode `python3 tests/regressao.py`, registre no `CHANGELOG.md`, commit e tag.
Publicação: `python3 scripts/publicar.py --destino <pasta>` e `--conferir <pasta>`, regressão dentro da cópia, push.
