# Playbook: caso piloto (Implementação A, Google Sheets)

> Caso real que deu origem ao padrão: fornecedor B2B de carpetes corporativos, sem CRM, venda consultiva.
> Os containers dele viraram os templates de `templates/gtm/` (com marcadores no lugar dos IDs).

**Data:** 17/05/2026 · **Implementação:** A (planilha)

## Contexto

- **Segmento:** B2B, inside sales
- **Produto:** carpete em placas (corporativo, hotelaria, institucional)
- **Ticket médio:** R$ 12.000 · **Margem bruta:** ~35% (estimativa)
- **LP:** construtor landingpage.app.br, formulário AJAX, página de obrigado em `/obrigado`
- **Armazenamento:** planilha Google (sem CRM), leads do Meta Lead Ads chegando por n8n

## Stack

GTM Web + GTM Server no Stape (plano Free) + Pixel e CAPI deduplicados por `event_id` + Google Ads
(Lead, MQL e WhatsApp) + GA4 (web e repasse pelo servidor) + planilha com Apps Script.

## Critério de MQL (na LP)

Lead vira MQL quando o ambiente **não** é residencial **e** a metragem é de 50 m² para cima. No template, a regra
virou o marcador `__REGRA_MQL__`, escrito em JavaScript sobre `d.qualif_1` e `d.qualif_2`.

## Valores proxy (Modelo A, lucro)

| Evento | Google Ads | Meta Ads | GA4 |
|---|---|---|---|
| Lead | R$ 190 | R$ 120 | R$ 150 |
| MQL | R$ 630 | R$ 400 | R$ 500 |

Base: lucro por venda R$ 12.000 × 35% = R$ 4.200; MQL → SQL de 50% no Google e 31,81% no Meta (taxas reais do
cliente); Lead → MQL e SQL → Venda por benchmark (30%).

## Eventos

| Evento | Acionador | Tags |
|---|---|---|
| PageView | All Pages | GA4, Google Ads, Pixel, CAPI |
| Lead | Page URL contém `/obrigado` | GA4, Google Ads, Pixel, CAPI |
| MQL | `/obrigado` e `cJS - is_mql = true` | GA4, Google Ads, Pixel, CAPI |
| Contact | Click URL contém `wa.me/` ou `api.whatsapp.com/send`, ou evento `JoinChat` | GA4, Google Ads, Pixel, CAPI |

## Resultado depois do go-live

- EMQ 8,0/10 em Lead e MQL; com `external_id`, `country` e `st` no `user_data`, 9,5 esperado.
- Deduplicação navegador + servidor funcionando; eventos chegando no Meta, no Google e no GA4.
- Custo extra: R$ 0 (Stape Free + planilha).

## Lições (todas em `referencias/armadilhas.md`)

1. `inheritEventName` do template da CAPI é SELECT: `"override"`, nunca `true`.
2. `gtm.formSubmit` falha em formulário AJAX: Lead na página de obrigado.
3. Variável que lê o DOM falha na página de obrigado: `sessionStorage` gravado no envio.
4. Token da CAPI apareceu em print várias vezes: token exposto é token trocado.
5. Test Event Code esquecido em produção transforma todo evento em teste.

## O que ficou pendente no piloto

- Apps Script que manda Purchase ao servidor quando o status vira Cliente (o back-pass).
- Domínio próprio no GTM Server (dependia do DNS do cliente).
- Adaptar o n8n para a aba única de leads e migrar os leads antigos.
