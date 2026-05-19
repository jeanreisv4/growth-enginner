# Implementação A: Google Sheets (cliente sem CRM)

> Caso majoritário da V4 Company. Cliente não tem CRM — usa planilha como storage de leads.

**Status:** 📝 Em construção (rascunho do caso WK)
**Última revisão:** 2026-05-17

---

## Quando usar

- Cliente não tem CRM contratado
- Cliente usa planilha (qualquer estrutura atual) para anotar leads/vendas
- Cliente provavelmente vai migrar pra CRM no futuro (mas não agora)

## Pré-requisitos

- LP do cliente com GTM Web instalado
- GTM Server (stape.io) criado e funcionando
- Pixel ID, GA4 Measurement ID, Google Ads ID disponíveis
- Access Token Meta CAPI gerado e seguro

---

## Visão geral

```
[LP do cliente] → form submit → /obrigado
                         ↓
              [GTM Web: tags Lead/MQL]
                         ↓
              [GTM Server (stape)] → [Meta, Google, GA4]

[n8n / form integration] → escreve linha na planilha
                         ↓
[Vendedor altera status] → Apps Script onEdit detecta
                         ↓
[Status = Cliente]
                         ↓
[Apps Script envia Purchase] → [GTM Server (stape)] → [Meta, Google, GA4]
```

## Passo a passo

### 1. Estrutura da planilha

Use o script automático `artefatos-referencia/setup-planilha-automatico.gs` (referência: caso WK).

> **TODO próximo chat:** documentar o passo a passo com prints reais do caso WK.

### 2. Integração form da LP → planilha

Opções:
- **n8n** (recomendado): workflow que recebe webhook do form e escreve na planilha
- **Form direto pra Sheets**: usando integração nativa do builder (limitado)
- **Zapier/Make**: alternativas pagas

> **TODO próximo chat:** trazer o workflow n8n do WK como modelo.

### 3. Apps Script: status=Cliente → Purchase event

> **TODO próximo chat:** construir o Apps Script de envio Purchase.

Esqueleto esperado:

```javascript
function onEditCheckPurchase(e) {
  // 1. Detectar mudança de status para "Cliente"
  // 2. Pegar dados da linha (lead_id, email, whatsapp, faturamento)
  // 3. Fazer POST para o endpoint do SSGTM
  // 4. Marcar coluna sincronizado_capi = TRUE
}
```

### 4. Validação

- Faz lead de teste → confirma chegada na planilha
- Muda status pra Cliente → confirma chegada Purchase no Meta/Google

---

## Caso de referência

Ver `playbook/caso-WK.md` para o caso real implementado.

## Artefatos disponíveis

Em `artefatos-referencia/`:
- `setup-planilha-automatico.gs` — script que monta a planilha
- `template-leads-WK.csv` — cabeçalhos
- `template-dropdowns-WK.csv` — valores de dropdowns
- `INSTRUCOES-importar-planilha-WK.md` — passo a passo de import manual
- `template-planilha-leads-WK.md` — documentação completa

## Erros comuns

> **TODO:** listar erros conhecidos baseados em iterações reais com clientes
