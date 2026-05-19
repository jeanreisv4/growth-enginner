---
skill: tracking-web-and-capi
owner: growth-engineer
latest: v1.0.0
status: active
segment:
  - b2b
  - b2c
  - b2b2c
tier:
  - starter
  - growth
  - scale
software:
  - gtm-web
  - gtm-server
  - stape
  - meta-events-manager
  - google-ads
  - ga4
  - google-sheets
  - apps-script
  - n8n
  - kommo
  - rd-crm
  - hubspot
specialization:
  - inside-sales
  - local-business
  - ecom
  - infoproduto
created: 2026-05-17
updated: 2026-05-17
---

## Propósito

Padrão único de tracking da V4 Company. Cobre todo o ciclo: planejar a implementação, executar a implementação, auditar setups existentes e diagnosticar problemas. Aplica-se a qualquer cliente, independente de ele ter CRM ou usar planilha como storage.

## Quando usar

- **Novo cliente** entrando na operação (modo `planejar`)
- **Antes do go-live** de qualquer cliente (modo `auditar`)
- **Setup quebrou** em produção (modo `troubleshoot`)
- **Coordenador** revisando implementação de operador (modo `auditar`)

## Quando NÃO usar

- Mudanças pontuais de criativo/copy (→ `gestor-de-trafego`)
- Análises de performance de campanha (→ `gestor-de-trafego/analise-de-performance`)
- Setup de campanha Meta/Google (→ `gestor-de-trafego/meta-ads-setup`)

## Modos de uso

Esta skill tem 3 modos. O Claude pergunta o modo antes de seguir.

### 1. `planejar` — Antes da implementação
**Cenário:** novo cliente, setup do zero.
**Output:** plano de implementação + JSONs de GTM prontos + scripts de automação.

### 2. `auditar` — Após implementação, antes do go-live
**Cenário:** coordenador valida setup do operador antes de publicar.
**Output:** relatório de auditoria com decisão (✅ aprovado / ❌ bloqueado por X).

### 3. `troubleshoot` — Setup com problema
**Cenário:** algo não dispara, EMQ baixo, deduplicação quebrou, etc.
**Output:** diagnóstico de causa raiz + correção sugerida.

## Inputs esperados

Varia por modo. Veja `latest.md` para inputs específicos. Em todos os modos:

- `cliente_nome` — nome do cliente
- `cliente_segmento` — b2b / b2c / b2b2c
- `cliente_nicho` — inside-sales | ecom | local-business | infoproduto
- `tem_crm` — sim/não (define implementação A ou B)
- `crm_ferramenta` — se sim: kommo | rd-crm | hubspot | pipedrive | outro
- `ticket_medio` — R$
- `taxas_funil` — Lead→MQL, MQL→SQL, SQL→Venda (% ou "uso benchmark")

## Output esperado

Markdown estruturado:
- Estado atual (se aplicável)
- Recomendação ou diagnóstico
- Próximos passos numerados
- Arquivos gerados (JSONs, scripts) anexados

## Conhecimento de referência

- `canonico/padrao-tracking.md` — contrato de dados + stack obrigatória
- `canonico/checklist-auditoria.md` — critérios objetivos de validação
- `implementacoes/sheets.md` — passo a passo cliente sem CRM
- `implementacoes/crm-kommo.md` — passo a passo cliente com Kommo
- `playbook/caso-WK.md` — caso real piloto (referência)

## Agentes que usam esta skill

- `owner`: growth-engineer (executa setup, troubleshoot)
- `consumers`:
  - `coordenador` (modo auditar)
  - `gestor-de-trafego` (consulta para alinhar tags de conversão)

## Versões disponíveis

| Versão | Data | Status | Resumo |
|--------|------|--------|--------|
| v1.0.0 | 2026-05-17 | latest | Versão inicial, baseada no caso piloto WK Carpetes |
