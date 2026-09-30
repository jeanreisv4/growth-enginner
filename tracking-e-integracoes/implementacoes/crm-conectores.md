# Conectores de CRM: o que cada um exige na entrada do lead e na devolução

> O contrato é o mesmo para todo CRM; muda como se lê, grava e recebe o aviso de etapa.

**Status:** 📝 Kommo em uso; demais com o que já foi visto em cliente (marcado) · **Agente:** `integracao-crm`

---

## O contrato (vale para qualquer CRM)

1. **Entrada**: todo lead de formulário/LP/WhatsApp vira lead no CRM, com origem (canal, campanha, conjunto,
   anúncio), ids de clique (gclid, fbclid/fbc, fbp, id do lead do Meta) e as respostas do formulário.
2. **Casamento**: pessoa × negociação pelo **telefone (DDD + 8 dígitos)**, nunca pelo nome; e-mail como segunda chave.
   Contato do WhatsApp costuma vir sem o 9º dígito.
3. **Duplicidade**: regra decidida com o usuário (negociação aberta recebe só a origem; todas fechadas → negociação
   nova no contato). Nunca criar às cegas: busca com erro (401/403/429) para o fluxo, não vira "não achei".
4. **Etapas → eventos**: `status_id`/estágio de SQL e de venda **por funil** (o "ganho" de um funil pode ser
   reengajamento em outro).
5. **Aviso de etapa**: webhook do CRM → n8n respondendo na hora; sem webhook, varredura periódica por data de alteração.
6. **Devolução**: `scripts/devolucao.py` (Meta direto ou pelo sGTM; Google pela Data Manager), nota no negócio a cada envio.
7. **Auditoria de entrada**: formulário × CRM por semana e por origem (`scripts/auditar_entrada.py`).

## Kommo (em uso)

- API v4, Bearer (token de longa duração da integração privada; muda quando a integração é salva). Até ~7 req/s;
  usar 3/s em lote. Resposta `application/hal+json` → no n8n, **Response Format: JSON** (senão vira texto).
- Host `.kommo.com` pode dar 403 para o IP do servidor: alias `<subdominio>.amocrm.com/api/v4`.
- Busca de contato vazia = **204** (o n8n marca erro no nó; tratar como "não achou").
- Campos nativos de rastreio (`tracking_data`): gclid, fbclid, gclientid, utm_*. 142 = ganho e 143 = perdido em todo
  funil, com nome diferente por funil. Etapa de entrada ("Incoming leads") não vem no `/leads` padrão.
- Webhook da conta ("etapa do lead alterada", `status_lead`) em `/api/v4/webhooks`: form-urlencoded, resposta em até
  2 s; >100 inválidas em 2 h desligam. Ação "Send webhook" do Digital Pipeline: JSON por etapa, sem campos.
- `/events?filter[type]=lead_status_changed` com `value_after` por funil/etapa: taxa etapa → venda sem varrer negócio.
- Nota: `POST /leads/notes` com `entity_id`, `note_type: common`. Tag: PATCH substitui a lista inteira.

## RD Station CRM (visto em cliente)

- `https://crm.rdstation.com/api/v1`, token na query (`?token=`), ~120 req/min, listas até 10 mil.
- **Dado do lead mora no negócio (deal custom fields)**, não no contato. PUT com um campo só mescla (não apaga os outros).
- Automação do RD Marketing → CRM pode recriar o lead horas depois como origem "Desconhecido" (gêmeos): auditar
  duplicidade por telefone e origem.
- Aviso de etapa: webhooks do RD CRM (a confirmar na primeira implementação de devolução).

## HubSpot / Pipedrive (a confirmar na primeira implementação)

- **HubSpot**: app privado (token Bearer), objetos contacts/deals, pipelines e estágios por id; webhooks via app.
- **Pipedrive**: `api_token`, deals/persons, `stage_id`; webhooks (`updated.deal`).
- Mesmo contrato acima; registrar aqui as pegadinhas na primeira vez.

## DataCrazy (visto em cliente)

- `https://api.g1.datacrazy.io/api/v1`, Bearer, **exige User-Agent de curl** (urllib padrão → 403), 30 req/min.
- CTWA: `conversation.sourceReferral` só vem com o tracking de CTWA ligado. Script: `sprint-growth/scripts/datacrazy.py`.

## NectarCRM (visto em cliente)

- `https://app.nectarcrm.com.br/crm/api/1/{modulo}/?api_token=`; módulos `oportunidades`, `contatos`; **15 por
  página fixos**; `status=1..5` (2 = Ganha) é o único jeito de ver fechados; "Ganha" em pré-vendas/SDR não é venda.

## GoHighLevel / LeadConnector (inclusive white-labels com outro nome)

- API LeadConnector (contacts, opportunities, `locationId`), não a do RD. Registrar pegadinhas na primeira devolução.
