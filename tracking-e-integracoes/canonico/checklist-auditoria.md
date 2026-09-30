# Checklist de Auditoria — tracking-e-integracoes

> Critérios objetivos pra aprovar (ou bloquear) um setup antes do go-live.
> Coordenador usa este checklist no modo `auditar` da skill.

**Status:** 📝 Em construção
**Última revisão:** 2026-09-28

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

## 11. Containers gerados pelo template (zero marcador)

Os templates de `templates/gtm/` não têm ID de nenhum cliente: só marcadores. O item bloqueia se o container veio
de outro caminho (cópia do container de outro cliente) ou se a validação do gerador não passou.

- [ ] Containers gerados por `scripts/gerar_containers.py` com `--producao`, `resumo.md` anexado e zero BLOQUEANTE
- [ ] Nenhum marcador `__...__` no container importado
- [ ] IDs conferidos contra as contas do cliente (Pixel, Google Ads, GA4), não contra o brief
- [ ] Rótulos copiados da conta, letra a letra (G1 do `gtm_auditoria.py` limpo)
- [ ] Seletores do formulário testados no formulário do cliente (`teste_formulario.py`)
- [ ] Nome dos containers = `wGTM | <dominio_cliente>` e `sGTM | <dominio_cliente>`
- [ ] `cJS - is_mql` com a regra do cliente, ou tags de MQL removidas quando não há critério
- [ ] Nomenclatura de tags/acionadores/variáveis e emojis das pastas preservados

## 12. Conta de anúncios e GA4

- [ ] Uma conversão **principal** por etapa do funil no Google Ads; as demais secundárias (⚠️ se houver duas na mesma categoria)
- [ ] A categoria da conversão principal está nas metas usadas pelas campanhas (`campaign_conversion_goal`)
- [ ] Conversões automáticas de ligação/WhatsApp do Google como secundárias
- [ ] Tag GA4 do servidor não dispara nos eventos do Meta (G2)
- [ ] Key events do GA4 = eventos que de fato disparam
- [ ] UTMs do Meta sem ID em `utm_source`/`utm_medium`
- [ ] Clique no WhatsApp medido também quando vem de widget ou popup

## 13. Origem até o CRM e volta da venda

- [ ] GTM carrega antes do aceite de cookies ou com Consent Mode v2 (não fica preso no banner)
- [ ] Formulário leva UTM, gclid e fbclid em campos ocultos até o Make/n8n/CRM (`teste_formulario.py`)
- [ ] Origem do lead gravada por automação, não por etiqueta manual
- [ ] Venda iniciada no WhatsApp: tracking de CTWA ligado no CRM
- [ ] Venda volta às plataformas (CAPI Purchase; Google Ads offline pela Data Manager API ou CSV agendado)
- [ ] Lead do formulário instantâneo grava o `leadgen_id` (15-17 dígitos) num campo do lead no CRM
- [ ] Tags de CRM no sGTM: `system_generated`, `generateFbp` desligado, IP/UA do lead (nunca o do n8n), `event_time` da etapa
- [ ] Acionador do Data Client exige a chave e o Client Name; evento do CRM com nome de evento do site não dispara a tag do site
- [ ] Webhook do CRM responde na hora (Kommo: até 2 s) e cada envio vira nota no lead


## 14. Integrações (modo integrar)

- [ ] Todo lead do formulário/LP vira lead no CRM: `auditar_entrada.py` sem semana com >20% fora (❌ se houver)
- [ ] Quem cria o lead no CRM é conhecido e falha visível (execução com erro, não "success" gravando zero)
- [ ] Lead Ads chega com id do lead e campanha/conjunto/anúncio reais (não "utm_source" literal)
- [ ] App do Meta (se houver) publicado, inscrito em `leadgen`, um webhook por app, credencial conectada
- [ ] Token/segredo não escrito em nó de código nem em header fixo: credencial do n8n
- [ ] Etapas de SQL e venda mapeadas **por funil**; webhook de etapa ativo e o workflow que recebe respondendo na hora
- [ ] Devolução testada sem gravar (código de teste do Meta, `validateOnly` do Google) e notas no negócio a cada envio
- [ ] Google: conversões UPLOAD_CLICKS (secundárias até decisão), conversões otimizadas para leads, gclid no CRM
- [ ] Conversacional: índice em cache (zero leitura por evento), append com nova tentativa espaçada, erros na semana
- [ ] Automações do cliente revisadas: backup, só as em uso ativas, nenhuma obsoleta com segredo no código
- [ ] Retroativos enviados no dia em que a devolução ligou (`retroativos.py`), com a hora real da etapa
- [ ] Uma conversão principal por etapa no Google (a que tem histórico); colunas "Funil CRM" no Meta e no Google
- [ ] Venda do CRM separada da venda da loja no Meta (conversão personalizada com `event_source` = crm)
- [ ] Conexões com data de vencimento anotadas (OAuth do Meta, app do Google publicado, token do CRM) e aviso de erro

---

## Notas importantes

- Itens da seção 7 (back-pass) podem ser ⚠️ se o cliente ainda não tem fluxo de vendas operando, mas devem virar ❌ quando começar a operar.
- Item 8 (segurança) é sempre ❌ bloqueante.
- Item 9 (validação) deve ser ❌ se não foi feito.
- Item 11 (containers pelo template) é sempre ❌ bloqueante — vazamento de dados entre clientes é falha crítica.
- Item 14: lead fora do CRM é sempre ❌; o resto é ⚠️ na primeira auditoria e ❌ depois.
- Itens 12 e 13 são ⚠️ na primeira auditoria e viram ❌ quando a campanha já otimiza por essa conversão.
