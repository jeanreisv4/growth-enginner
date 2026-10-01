---
skill: tracking-e-integracoes
owner: growth-engineer
latest: v1.2.0
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
  - pipedrive
  - datacrazy
  - nectarcrm
  - gohighlevel
  - chatwoot
  - meta-lead-ads
  - google-data-manager
specialization:
  - inside-sales
  - local-business
  - ecom
  - infoproduto
created: 2026-05-17
updated: 2026-09-30
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

Esta skill tem 4 modos. O Claude pergunta o modo antes de seguir.

### 1. `planejar` — Antes da implementação
**Cenário:** novo cliente, setup do zero.
**Output:** plano de implementação + JSONs de GTM prontos + scripts de automação.

### 2. `auditar` — Após implementação, antes do go-live
**Cenário:** coordenador valida setup do operador antes de publicar.
**Output:** relatório de auditoria com decisão (✅ aprovado / ❌ bloqueado por X).

### 4. `integrar` — Lead no CRM e venda de volta
**Cenário:** formulário/LP/Lead Ads/WhatsApp → CRM, devolução do CRM ao Meta e ao Google, revisão das automações.
**Output:** mapa pelos agentes `integracao-*`, fluxos montados desligados, teste sem gravar, ligação com ok, recuperação do que ficou fora.

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
- `playbook/caso-piloto-carpetes.md` — caso real piloto (referência)
- `referencias/armadilhas.md` — erros já vistos em cliente, com como detectar e o que fazer
- `templates/gtm/` + `scripts/gerar_containers.py` — containers canônicos com marcadores e o gerador que valida

## Agentes que usam esta skill

- `owner`: growth-engineer (executa setup, troubleshoot)
- `consumers`:
  - `coordenador` (modo auditar)
  - `gestor-de-trafego` (consulta para alinhar tags de conversão)

## Versões disponíveis

| Versão | Data | Status | Resumo |
|--------|------|--------|--------|
| v1.2.0 | 2026-09-30 | tag git | Devolução do CRM (Kommo → n8n → sGTM/Meta e Data Manager/Google) |
| v2.3.0 | 2026-09-30 | latest | Devolução do RD Station CRM ao Google (devolucao_rd.py), conector RD documentado |
| v2.1.0 | 2026-09-30 | — | Retroativos, colunas Funil CRM, principal única pelo histórico, conexões que vencem |
| v2.0.0 | 2026-09-30 | — | Renomeada; modo integrar, 4 agentes, Lead Ads direto, Data Manager, conversacional, auditoria de entrada |
| v1.1.0 | 2026-09-28 | tag git | Templates com marcadores, gerador com validações, armadilhas das sprints, testes e desenho |
| v1.0.0 | 2026-05-17 | tag git `v1.0.0` | Versão inicial, baseada no caso piloto |
