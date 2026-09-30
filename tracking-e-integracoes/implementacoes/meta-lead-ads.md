# Implementação: Lead Ads do Meta direto no n8n (app próprio do cliente)

> Formulário instantâneo → n8n → CRM (+ planilha de backup), na hora, sem Make e sem planilha no meio.

**Status:** ✅ Em uso (v2.0.0) · **Caso:** distribuidora de automatizadores (distribuidora de automatizadores), 30/09/2026
**Relacionados:** `crm-kommo.md` (devolução), `crm-conectores.md` (outros CRMs), agente `integracao-meta`

---

## Por que tirar o Make (ou a automação nativa) do caminho

O cenário "Meta → planilha → CRM" pode quebrar **pela metade e em silêncio**: no caso de referência a planilha
continuou recebendo 815 de 816 leads, mas a criação no CRM parou em 31/08 e **57 de 66 leads de 16 a 30/09 não
estavam no CRM**. Ninguém viu porque a planilha parecia saudável. Além disso, a planilha gravava `utm_source` literal
em 1.308 de 1.317 linhas (os parâmetros de URL do anúncio não eram preenchidos).

Direto no n8n: o lead chega pelo webhook do app, com o **id do lead** (serve para a devolução casar 100%), campanha,
conjunto, anúncio e plataforma de verdade, e a falha no CRM vira **erro visível** na execução.

## 1. O app (developers.facebook.com, feito pelo usuário; ~10 min)

1. **Criar app** → caso de uso **"Capturar e gerenciar leads de anúncios com a API de Marketing"** (só ele; o de
   "criar anúncios" não é preciso) → tipo Empresa → **portfólio do cliente**. App do próprio cliente, com quem conecta
   sendo admin do app e da página, usa **Acesso padrão**: não precisa de Revisão do app.
2. **Caso de uso → Personalizar**: `leads_retrieval`, `pages_show_list`, **`pages_manage_metadata`**, `pages_manage_ads`,
   `pages_read_engagement`, `business_management`. Sem `pages_manage_metadata` o login falha com
   **"Invalid Scopes: pages_manage_metadata"** (erro 100). Se não aparecer, adicionar o caso de uso "Gerenciar tudo na sua Página".
3. **Configurações → Básico**: domínio do n8n em **Domínios do app** (sem ele: **erro 1349048** "O domínio dessa URL
   não está incluído nos domínios do app"); política de privacidade e termos (páginas reais do site do cliente);
   categoria "Negócios e páginas". Plataforma **Site** com a URL do n8n.
4. **Login do Facebook para Empresas → Configurações**: em **URIs de redirecionamento do OAuth válidos**, o valor
   exato que o n8n mostra em **"OAuth Redirect URL"** na credencial (`https://<n8n>/rest/oauth2-credential/callback`);
   Login OAuth do cliente e da Web = Sim.
5. **Publicar** o app. Em desenvolvimento, o webhook de lead não entrega lead real.
6. Business do cliente → **Integrações → Acesso aos leads**: o app liberado (padrão: todos).

## 2. Credencial no n8n

Tipo `facebookLeadAdsOAuth2Api`. Pela API pública do n8n o esquema exige, além de `clientId`/`clientSecret`:
`serverUrl: ""`, `sendAdditionalBodyProperties: false`, `additionalBodyProperties: "{}"`. O **Connect** é só pela
interface (o usuário). A chave secreta vai para `~/.config/<pasta>/<cliente>_meta_app.key` com `pbpaste >`, nunca no chat.

**Testar antes de ligar**: "Unable to sign without access token" no primeiro nó = o Connect não terminou. Um
workflow temporário (webhook → HTTP `/{página}?fields=access_token` com a credencial → `/{página}/leadgen_forms`)
devolve só contagens e é apagado no fim.

## 3. O fluxo

```
Lead Ads Trigger (página + formulário) → Config → Token da página (1x) → Ids dos leads
  → Detalhe do lead: /{leadgen_id}?fields=id,created_time,field_data,ad_name,adset_name,campaign_name,platform,form_id
  → Normalizar (ignora lead de teste do Meta; telefone DDD+8) → CRM: buscar contato → conferir DDD → negociações
  → decidir (criar / completar origem / nova negociação no contato) → gravar → Conferir gravação (erro visível)
  → Planilha de backup (nó DESLIGADO até a automação antiga sair: senão duplica linha)
```

- **Um webhook por app**: o Meta aceita um único endereço de callback por app. Um fluxo por app; mais clientes no
  mesmo app = fluxo central que roteia por página/formulário. O gatilho do n8n é por formulário: formulário novo =
  atualizar o gatilho (ou um webhook próprio inscrito em `leadgen` da página, que pega todos).
- Ao ativar, conferir a inscrição: `/{página}/subscribed_apps` mostra o app com `subscribed_fields: ["leadgen"]`.
- Regras do CRM (casamento, duplicidade, etapa de entrada, idade máxima para criar negociação): **as do cliente**,
  decididas com o usuário. No caso de referência: funil do SDR de IA, etapa de entrada, contato buscado pelos 8
  dígitos e conferido pelo DDD, negociação aberta só recebe origem, todas fechadas → negociação nova no contato,
  lead com mais de 30 dias não vira negociação (a IA abordaria contato frio).
- Respostas do formulário vão para os campos do CRM que a LP já usa (perfil, volume, CNPJ) e o e-mail para o contato.

## 4. Testar sem gravar

Cópia do fluxo com gatilho webhook (`?id=<leadgen_id>`) e o nó de gravação **desligado**: roda com um lead real que
não está no CRM (deve dar "criar") e um que está (deve dar "nada a fazer"), mostra só a decisão e é apagada.

## 5. Recuperar o que ficou fora

1. **Medir** (ver "Auditoria de entrada"): leads do formulário por semana × contatos do CRM por telefone.
2. Lista dos ids que não têm lead no CRM depois do formulário (+ os que só têm negociação antiga).
3. Cópia do fluxo com gatilho `POST {ids:[...]}` e **etiqueta própria** ("… - recuperado"), em lotes de 20.
4. Conferir no CRM (etiqueta, etapa, campos) e cruzar de novo.
5. **Espaçar os lotes** quando houver automação reagindo ao lead criado (IA de SDR, régua de WhatsApp): 73 leads
   de uma vez viraram uma rajada de conversas e derrubaram a gravação do Chatwoot por cota do Sheets.

## 6. Auditoria de entrada (formulário × CRM)

Pergunta: **todo lead do formulário virou lead no CRM, e quando?** Fonte da verdade é o Meta
(`/{formulário}/leads`, 90 dias, com `created_time`), não a planilha. Casar por telefone (DDD + 8 dígitos) e ver,
semana a semana, a **origem** do lead no CRM (ex.: "[V4] make", "SDR IA", "API"): a semana em que uma origem some é a
semana em que a integração quebrou. Script: `scripts/auditar_entrada.py`.

## 7. Depois de ligar

- Primeiro lead real: execução com sucesso, lead na etapa certa, campos preenchidos.
- A automação antiga desligada pelo usuário → ligar o nó da planilha.
- Cruzamento semanal (auditoria de entrada) até estabilizar.
