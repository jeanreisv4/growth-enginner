# Implementação B: CRM Kommo

> Cliente com Kommo configurado. Back-pass via webhook nativo do CRM.

**Status:** 📝 Em construção
**Última revisão:** 2026-05-17

---

## Quando usar

- Cliente tem Kommo configurado e operando
- Time comercial já usa Kommo no dia a dia
- Pipeline de vendas está mapeado (etapas claras)

## Pré-requisitos

> **TODO próximo chat:** listar pré-requisitos do lado do Kommo
> - Pipeline padronizado
> - Campos custom criados (lead_id, gclid, fbclid, etc.)
> - Permissão pra criar webhooks

---

## Visão geral

```
[LP] → form submit → /obrigado → GTM Web → CAPI/Pixel/GA4/Ads

[Kommo recebe lead] → campos custom preenchidos
                         ↓
[Lead muda pra etapa "Cliente" no Kommo] → webhook dispara
                         ↓
[Webhook → SSGTM] → [Meta, Google, GA4] (Purchase event)
```

## Passo a passo

### 1. Configurar campos custom no Kommo

Campos obrigatórios:
- `lead_id` (chave única)
- `gclid` (Google Click ID)
- `fbclid` (Facebook Click ID)
- `origem` (canal de origem)
- `meta_lead_id` (se vier de Lead Ads)

> **TODO próximo chat:** detalhar criação de campos no Kommo

### 2. Configurar integração LP → Kommo

> **TODO:** documentar via n8n ou nativo

### 3. Configurar webhook na etapa "Cliente"

> **TODO:** documentar como apontar webhook do Kommo pro SSGTM

### 4. Validação

- Lead de teste → confirma chegada no Kommo
- Mover pra "Cliente" → confirma Purchase no Meta/Google

---

## Diferenças vs Implementação A (Sheets)

| | A (Sheets) | B (Kommo) |
|---|---|---|
| Storage | Planilha Google | CRM Kommo |
| Back-pass Purchase | Apps Script onEdit | Webhook nativo |
| Custo extra | R$ 0 | Mensalidade Kommo |
| Escalabilidade | Limitada | Alta |
| Pipeline visual | Não | Sim |

---

## Caso de referência

> **TODO:** documentar caso real (cliente real ou fictício "Pisos Premium")
