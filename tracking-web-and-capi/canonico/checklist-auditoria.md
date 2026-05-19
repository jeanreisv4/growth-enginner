# Checklist de Auditoria — tracking-web-and-capi

> Critérios objetivos pra aprovar (ou bloquear) um setup antes do go-live.
> Coordenador usa este checklist no modo `auditar` da skill.

**Status:** 📝 Em construção
**Última revisão:** 2026-05-17

---

## Como usar

Para cada item:
- ✅ **Conforme** — atende o padrão
- ⚠️ **Atenção** — não bloqueia, mas vale corrigir
- ❌ **Bloqueante** — impede go-live até corrigir

Pontuação:
- 0 ❌ → **APROVADO**
- 1+ ❌ → **BLOQUEADO**

---

## 1. Stack instalada

- [ ] GTM Web publicado em produção (versão ≥ v1)
- [ ] GTM Web carrega na LP (validar via console: `google_tag_manager['GTM-XXX']`)
- [ ] GTM Server (stape) status: Running
- [ ] GTM Server publicado em produção (versão ≥ v1)
- [ ] Cliente GA4 configurado no GTM Server

## 2. Pixel + CAPI deduplicados

- [ ] Tags Pixel e CAPI compartilham mesmo `event_id` via variável dedicada
- [ ] Token CAPI configurado no GTM Server (não placeholder)
- [ ] Pixel ID correto nos 2 lados (Web e Server)
- [ ] Tag CAPI não está pausada
- [ ] Tag CAPI tem trigger atribuído

## 3. Eventos disparando

- [ ] PageView dispara em todas páginas (Pixel + CAPI)
- [ ] Lead dispara na página /obrigado (não no formSubmit)
- [ ] MQL dispara quando `is_mql=true` (se aplicável)
- [ ] Contact dispara no clique do WhatsApp
- [ ] Tags GA4 e Google Ads também disparam nos mesmos triggers

## 4. Advanced Matching / User Data

- [ ] Pixel envia `em` + `ph` + `fn` (mínimo)
- [ ] CAPI envia `em` + `ph` + `fn` (mesmos campos)
- [ ] EMQ Lead ≥ 7/10 (ideal ≥ 9)
- [ ] EMQ MQL ≥ 7/10

## 5. Values + Currency

- [ ] Tags Lead têm `value` + `currency` (BRL)
- [ ] Tags MQL têm `value` + `currency` (BRL)
- [ ] Valores diferenciados por canal (Modelo A — lucro proxy)
- [ ] Google Ads usa `conversionValue` + `currencyCode`
- [ ] Meta Pixel usa `objectProperties`
- [ ] CAPI usa `eventSettingsTable` com value/currency

## 6. Storage de leads

- [ ] Planilha ou CRM segue schema padrão (`canonico/padrao-tracking.md` seção 4)
- [ ] Coluna `status` com dropdown único (não checkboxes)
- [ ] Coluna `motivo_perdido` separada de `observacao`
- [ ] Coluna `lead_id` presente (chave única)
- [ ] Campos UTM presentes
- [ ] `gclid` + `fbclid` capturados quando aplicável

## 7. Back-pass do funil (Lead → SQL → Venda)

- [ ] Apps Script (sheets) ou webhook (CRM) configurado
- [ ] Status=Cliente dispara Purchase event no SSGTM
- [ ] Purchase event tem `value` real (faturamento)
- [ ] Purchase event tem `lead_id` para atribuição

## 8. Segurança

- [ ] Token CAPI NÃO está em prints, screenshots ou commits
- [ ] Test Event Code apagado (variável vazia) em produção
- [ ] Planilha com permissão restrita (não pública)
- [ ] Variáveis de tokens no GTM Server protegidas (Stape Secrets ou similar)

## 9. Validação end-to-end

- [ ] Fez 1 lead de teste via Preview Mode (Web + Server)
- [ ] Evento chegou no Meta Events Manager
- [ ] Evento chegou no GA4 Realtime
- [ ] Evento chegou no Google Ads (pode demorar 3-24h)
- [ ] Dedup Browser+Server visível na "Visão Geral" do Pixel
- [ ] Cliente fictício "Cliente" feito → Purchase chegou no Meta

## 10. Documentação

- [ ] Versão GTM Web tem nome claro (não "Versão N")
- [ ] Versão GTM Server tem nome claro
- [ ] Documentação do cliente em `playbook/caso-<cliente>.md` (opcional mas recomendado)

## 11. Templates limpos (zero placeholder do WK)

Após gerar os JSONs a partir do template canônico, verificar que NENHUM valor do WK Carpetes sobreviveu no GTM do cliente. Qualquer ❌ aqui é BLOQUEANTE — é vazamento de template entre clientes.

- [ ] Nenhuma string `444617535160623` (Meta Pixel ID do WK)
- [ ] Nenhuma string `1066377963` (Google Ads ID do WK)
- [ ] Nenhuma string `G-SQ2HXLBL2E` (GA4 ID do WK)
- [ ] Nenhuma string `u7Y1CP2rlZccEOvFvvwD`, `6ZwcCOztp64cEOvFvvwD`, `KG5qCLWhj5ccEOvFvvwD` (Conversion Labels do WK)
- [ ] Nenhuma string `whhhlqap.sac.stape.io` (SSGTM do WK)
- [ ] Nenhuma referência a `wkcarpetes.com.br` ou `lp.wkcarpetes.com.br`
- [ ] Nenhuma referência a `5511976262557` (WhatsApp do WK)
- [ ] Selectors do form ajustados ao form do cliente (não `seu-nome`, `seu-e-mail`, `seu-telefonewhatsapp`, `seu-ambiente`, `sua-metragem`)
- [ ] Nome dos containers = `WEB | <dominio_cliente>` e `sGTM | <dominio_cliente>`
- [ ] Critério em `cJS - is_mql` reflete a regra do cliente (não a do WK)
- [ ] Nomenclatura de tags/triggers/variáveis e emojis das pastas preservados (não alterar o canônico)

---

## Notas importantes

- Itens da seção 7 (back-pass) podem ser ⚠️ se o cliente ainda não tem fluxo de vendas operando, mas devem virar ❌ quando começar a operar.
- Item 8 (segurança) é sempre ❌ bloqueante.
- Item 9 (validação) deve ser ❌ se não foi feito.
- Item 11 (templates limpos) é sempre ❌ bloqueante — vazamento de dados entre clientes é falha crítica.
