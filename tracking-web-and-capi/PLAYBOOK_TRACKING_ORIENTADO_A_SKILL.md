# Playbook Tracking orientado à skill `tracking-web-and-capi`

## Objetivo

Implementar, auditar e diagnosticar tracking web e server-side com um padrão único para a operação.

Este playbook orienta o uso da skill `tracking-web-and-capi`. A skill cobre GTM Web, GTM Server, Stape, Meta Pixel, Meta CAPI, Google Ads, GA4, Google Sheets, Apps Script, n8n e CRM.

O objetivo final é garantir que eventos, leads, UTMs, click IDs, status comerciais e receita sejam rastreáveis de ponta a ponta:

```text
clique -> landing page -> evento -> lead -> CRM/planilha -> SQL -> venda -> receita -> plataformas/relatório
```

## Como acionar a skill

Sempre começar informando o modo:

```text
Use a skill tracking-web-and-capi no modo [planejar/auditar/troubleshoot].
```

A skill tem 3 modos:

- `planejar`: criar o plano de tracking para um cliente novo ou setup do zero.
- `auditar`: validar um setup existente antes do go-live.
- `troubleshoot`: diagnosticar algo que não está funcionando.

## Modo `planejar`

Usar quando o cliente ainda vai implementar tracking ou quando a estrutura atual precisa ser redesenhada.

Enviar para a skill:

- nome do cliente;
- segmento: `b2b`, `b2c` ou `b2b2c`;
- nicho: `inside-sales`, `ecom`, `local-business` ou `infoproduto`;
- ticket médio;
- margem bruta, se houver;
- taxas de funil: Lead -> MQL, MQL -> SQL, SQL -> Venda;
- URL da LP;
- plataforma da LP;
- CRM usado, se existir;
- alternativa de storage, como Google Sheets;
- Meta Pixel ID;
- Google Ads ID;
- GA4 Measurement ID;
- conversion labels do Google Ads;
- URL do GTM Server/Stape;
- domínio do cliente;
- página de obrigado;
- WhatsApp principal;
- seletores de formulário e botões;
- critério de MQL, se for automatizado na LP.

Output esperado:

- plano de implementação;
- stack final;
- eventos a implementar;
- valores proxy por evento;
- diferenciação por canal;
- próximos passos numerados;
- indicação dos JSONs, scripts ou ajustes necessários.

## Modo `auditar`

Usar depois da implementação e antes do go-live.

Enviar evidências reais, não apenas descrição:

- link da LP;
- GTM Web ID;
- GTM Server URL;
- prints ou export dos containers Web e Server;
- Meta Pixel ID;
- evidência do Meta Events Manager;
- GA4 Realtime ou DebugView;
- Google Ads conversions;
- exemplo de lead teste;
- planilha ou CRM com campos recebidos;
- payload de webhook, Apps Script ou n8n;
- evidência de deduplicação Browser + Server;
- evidência de `event_id`;
- evidência de `gclid`, `fbclid` e UTMs quando aplicável.

A auditoria deve usar o checklist:

```text
canonico/checklist-auditoria.md
```

Critério:

- `Aprovado`: zero item bloqueante.
- `Bloqueado`: um ou mais itens bloqueantes.
- `Atenção`: não bloqueia, mas deve ser corrigido ou documentado.

Itens normalmente bloqueantes:

- GTM Web não carrega na LP;
- GTM Server não está rodando;
- Pixel e CAPI não deduplicam pelo mesmo `event_id`;
- CAPI sem token ou sem trigger;
- Lead não dispara;
- dados de usuário não chegam para advanced matching;
- `value` e `currency` ausentes nos eventos principais;
- planilha/CRM sem `lead_id`;
- UTMs ou click IDs ausentes;
- back-pass de SQL/Venda inexistente quando já deveria operar;
- token exposto em print, commit ou documento público;
- Test Event Code ativo em produção;
- lead teste end-to-end não foi executado;
- template de outro cliente vazou no setup.

## Modo `troubleshoot`

Usar quando algo quebrou ou não está performando como esperado.

Enviar:

- sintoma observado;
- onde o problema aparece: GTM Preview, Meta Events Manager, GA4, Google Ads, CRM, planilha ou dashboard;
- quando começou;
- mudanças recentes;
- URL testada;
- prints/logs de erro;
- nome do evento afetado;
- se afeta Web, Server ou ambos;
- exemplo de lead ou evento com problema.

Sintomas comuns:

- evento não dispara;
- evento dispara duplicado;
- CAPI não chega;
- deduplicação falhou;
- EMQ baixo;
- Lead chega sem UTM;
- CRM recebe lead incompleto;
- Purchase não volta para Meta/Google;
- Google Ads não registra conversão;
- GA4 mostra evento, mas mídia não;
- planilha desloca colunas;
- webhook retorna sucesso, mas não grava destino.

Output esperado:

- causa provável;
- teste para confirmar;
- correção recomendada;
- risco se não corrigir;
- checklist de validação após ajuste.

## Eventos mínimos

Todo setup deve prever:

```text
PageView
Lead
MQL, se aplicável
Contact
SQL
Purchase
```

Regra:

- `PageView`: todas as páginas.
- `Lead`: envio de formulário ou página de obrigado.
- `MQL`: quando houver critério automatizado.
- `Contact`: clique em WhatsApp.
- `SQL`: avanço comercial via CRM/planilha/back-pass.
- `Purchase`: venda fechada com valor real.

## Dados mínimos

Todo lead deve preservar:

```text
lead_id
created_at
name
phone
email
utm_source
utm_medium
utm_campaign
utm_content
utm_term
gclid
gbraid
wbraid
fbclid
status
revenue
ticket
owner
```

Se o setup tiver CRM, esses campos devem estar em propriedades próprias. Se não houver CRM, devem estar na planilha padrão.

## Segurança

Nunca colocar em chat, print, commit ou documento público:

- token Meta CAPI;
- secrets do Stape;
- tokens de API;
- credenciais de CRM;
- credenciais de planilha;
- cookies ou headers autenticados.

Tokens devem ficar no gerenciador de senhas do cliente ou em secrets da ferramenta.

## Teste obrigatório antes do go-live

Antes de publicar ou validar a implementação:

1. Abrir a LP com UTMs de teste.
2. Validar GTM Web em Preview Mode.
3. Validar GTM Server em Preview Mode.
4. Enviar um lead teste.
5. Confirmar `PageView` e `Lead` no Meta Events Manager.
6. Confirmar evento no GA4 Realtime ou DebugView.
7. Confirmar conversão no Google Ads, considerando atraso da plataforma.
8. Confirmar lead na planilha ou CRM.
9. Confirmar UTMs e click IDs no lead.
10. Simular avanço para SQL ou Cliente quando o back-pass existir.
11. Confirmar `Purchase` com valor real quando aplicável.
12. Confirmar deduplicação Browser + Server.

## Prompt recomendado

```text
Use a skill tracking-web-and-capi no modo [planejar/auditar/troubleshoot].

Cliente:
Segmento:
Nicho:
LP:
CRM:
Storage final:
GTM Web:
GTM Server:
Meta Pixel:
Google Ads:
GA4:
Eventos configurados:
Evidências disponíveis:
Problema ou objetivo:
```

## Relação com a skill `audit-utms`

Usar `tracking-web-and-capi` para implementar, auditar ou diagnosticar tracking completo.

Usar `audit-utms` quando o foco específico for validar se UTMs e click IDs estão corretos entre:

```text
Google/Meta -> LP -> formulário -> CRM -> n8n/planilha/base final
```

Na prática:

- `tracking-web-and-capi`: eventos, Pixel, CAPI, GTM, GA4, Google Ads, server-side, deduplicação e back-pass.
- `audit-utms`: taxonomia, URL Parameters, tracking template, campos ocultos, CRM, payload e preservação das UTMs.

