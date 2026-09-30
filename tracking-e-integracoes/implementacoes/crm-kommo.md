# Implementação B: CRM Kommo (devolução das etapas às plataformas)

> Cliente com Kommo. O lead entra no CRM; quando o comercial muda a etapa, o evento volta ao Meta e ao Google Ads.

**Status:** ✅ Em uso (v1.2.0)
**Última revisão:** 2026-09-30
**Ferramentas:** `scripts/devolucao.py`, `templates/devolucao/nucleo.js`, bloco `devolucao` do brief, `gerar_containers.py`

---

## Por que não é só GTM

A mudança de etapa acontece no Kommo, sem ninguém na página: o GTM Web não vê nada. E o webhook do Kommo manda
pouco (id do lead, etapa, funil; o do Digital Pipeline nem campos personalizados). Telefone, e-mail, `lead_id` do
Meta e gclid estão no lead e no contato, e só a API devolve. Por isso tem um n8n no meio.

```
Kommo (etapa mudou) ──webhook──► n8n: responde 200 na hora, lê lead + contato na API, monta o evento
                                   ├─► sGTM /data (Data Client) ──► tag "00.5 | Meta CAPI - SQL" … (token só no sGTM)
                                   ├─► Google Ads: Data Manager API (events:ingest), gclid + e-mail/telefone com hash
                                   └─► nota no lead: "[Devolução Meta] SQL entregue ao sGTM (HTTP 200)"
```

- **Meta pelo sGTM:** o token da CAPI já mora no GTM Server (regra da skill); as tags seguem o padrão de nomes;
  versão e histórico ficam no GTM.
- **Google direto do n8n:** a Google Ads API **não aceita mais quem começa a importar conversão offline**
  (desde 15/06/2026 devolve `CUSTOMER_NOT_ALLOWLISTED_FOR_THIS_FEATURE` para token sem upload offline no semestre
  anterior). O caminho é a Data Manager API, `POST https://datamanager.googleapis.com/v1/events:ingest`.

### Modo direto (sem sGTM)

`"meta_via": "direto"` no bloco: o n8n manda o evento direto para
`POST https://graph.facebook.com/<graph_versao>/<pixel>/events` (padrão v24.0), com o hash feito no próprio núcleo
(`metaGraph`: em, ph, fn, ln, country e external_id em SHA-256; lead_id, fbc, fbp, IP e navegador crus). Credencial
**Query Auth** no n8n (`access_token` = token da CAPI), restrita a `graph.facebook.com`. Test Event Code em
`meta_test_event_code` só durante o teste. Usar quando o cliente não tem sGTM ou o container da Stape caiu (distribuidora de automatizadores,
30/09/2026: plano gratuito desativado, `/healthy` 404). O sGTM continua sendo o padrão quando está de pé.

### Id do lead do formulário buscado no Meta (`meta_leadgen`)

Quando o CRM não guarda o `leadgen_id` (o lead nasce na IA do SDR, na planilha do Meta, no Make), a devolução pergunta
ao Meta: `"meta_leadgen": {"pagina": "<page_id>", "credencial": "<id>", "dias": 90}`. Nós "Meta | Token da página"
(credencial **Facebook Lead Ads OAuth2** conectada à página, uma vez por execução) e "Casar id do lead" (lê
`/{página}/leadgen_forms` e `/{formulário}/leads` dos últimos N dias, paginando, e casa pelo telefone DDD + 8 dígitos
com `acharLeadId`). Achou, o evento sai com `lead_id`; não achou ou deu erro, sai só com telefone e a nota do lead diz
por quê. Sem fluxo de captura, sem armazenamento e sem disputa pelo webhook do app (o Meta aceita um por app).

App próprio do cliente (distribuidora de automatizadores, 30/09/2026): caso de uso "Capturar e gerenciar leads" + `pages_manage_metadata`
(senão "Invalid Scopes"), domínio do n8n em **Domínios do app** (senão erro 1349048), o `OAuth Redirect URL` que o
n8n mostra na credencial em **Login do Facebook para Empresas → URIs de redirecionamento**, política de privacidade e
categoria preenchidas, app publicado. Credencial pela API exige `serverUrl: ""`, `sendAdditionalBodyProperties: false`
e `additionalBodyProperties: "{}"`; o Connect é só pela interface.

## Pré-requisitos

| Onde | O quê |
|---|---|
| Kommo | O Kommo já traz campos de rastreio nativos no lead (tipo `tracking_data`: `gclid`, `fbclid`, `gclientid`, `utm_*`): use os ids deles antes de criar campo novo. Campos no **lead** (tipo texto) para o que não pode se perder: `meta_lead_id` (Lead Ads), `fbclid` ou `fbc`, `fbp`, `gclid`, `gbraid`, `wbraid`, `external_id` (o mesmo do site). IP e navegador do lead, se o formulário tiver. |
| Entrada do lead | Quem cria o lead no Kommo (n8n, Make, integração nativa) **grava esses campos**. Lead Ads: o `leadgen_id` (15-17 dígitos). Site: campos ocultos com gclid, fbclid e os cookies `_fbc`, `_fbp`, `_gcl_aw`. |
| Kommo | Token de longa duração (Configurações → Integrações → integração privada). No n8n: credencial Header Auth `Authorization: Bearer <token>`. |
| Meta | Pixel/dataset conectado como **fonte CRM** (Gerenciador de Eventos → Conectar fontes de dados → CRM) para entrar na otimização por lead de conversão. Sem isso o evento chega, mas não conta para a integração. |
| Google Ads | Uma conversion action **Importação** (UPLOAD_CLICKS) por evento; termos de dados do cliente aceitos e conversões otimizadas para leads ligadas. No n8n: credencial OAuth2 com o escopo `https://www.googleapis.com/auth/datamanager`. |
| sGTM | Stape com o domínio do cliente; a tag CAPI da Stape já instalada (template do site). |

## Regras do Meta para lead de CRM (Conversion Leads)

- `action_source = system_generated`, `custom_data.event_source = "crm"`, `custom_data.lead_event_source = "Kommo"`.
- `user_data.lead_id` = id do lead do formulário instantâneo, **15 a 17 dígitos**; inválido faz o Meta recusar o
  evento. Vai como texto (17 dígitos estouram o inteiro do JavaScript).
- `event_name` é livre: o nome da etapa. Mínimo 2 etapas, de preferência 3 ou mais, incluindo a de entrada.
- `event_time` no máximo **7 dias** antes do envio e depois da criação do lead. Não falsificar a hora para caber.
- Pelo menos 200 leads por mês e a etapa otimizada acontecendo em até 28 dias.
- Envio no mínimo diário; aqui é na hora.

## Passo a passo

### 1. Ids do Kommo

`GET /api/v4/leads/pipelines` (funis e `status_id` de cada etapa; 142 = ganho e 143 = perdido em todos os funis) e
`GET /api/v4/leads/custom_fields` (ids dos campos). **Host:** se o `.kommo.com` der 403 em HTML do nginx a partir do
n8n, use o alias `https://<subdominio>.amocrm.com/api/v4` (mesma conta, mesma API).

### 2. Bloco `devolucao` no brief

Modelo em `templates/brief_exemplo.json`:

```json
"devolucao": {
  "kommo_api": "https://<subdominio>.kommo.com/api/v4",
  "funis": [1234567],
  "etapas": {"7654321": "SQL", "142": "Purchase"},
  "valores": {"SQL": 900},
  "campos": {"meta_lead_id": 900001, "fbclid": 900002, "fbp": 900003, "gclid": 900004, "gbraid": 900005, "external_id": 900006},
  "google": {"customer_id": "1234567890", "acoes": {"SQL": "111111111", "Purchase": "222222222"}, "fuso": "-03:00",
             "validar_apenas": true},
  "n8n": {"credencial_kommo": "<id>", "credencial_google": "<id>"}
}
```

Valor: SQL usa o proxy de `valores` (Modelo A); Purchase usa o valor do lead no Kommo (`price`), senão
`valor_venda_padrao`. Sem `google`, só o Meta recebe. **Token nunca entra no brief** (o script bloqueia).

### 3. Gerar

```
python3 scripts/devolucao.py --brief clientes/<c>/brief.json --out saida/<c>
```

Sai `n8n-devolucao-<c>.json`, `sgtm-devolucao-<c>.json`, `resumo-devolucao.md` e `saida/<c>/.chave_devolucao`
(segredo entre n8n e sGTM, 600, reaproveitado nas próximas gerações). Container novo: `gerar_containers.py` já
inclui as peças no sGTM.

### 4. sGTM

Peças (container novo já vem com elas; container existente: aplicar pela MCP do GTM, com ok):

- Template **Data Client** (Stape) e o cliente `Data Client | CRM` (caminho `/data`). O template **não está na galeria**:
  importar `templates/gtm/data-client.tpl` à mão no container (Modelos → Modelos de cliente → Novo → ⋮ → Importar).
- Variáveis `00 - Devolução - Chave`, `00 - Devolução - CRM` e as de dados do evento `ED - chave`, `ED - event_time`,
  `ED - lead_ip`, `ED - lead_user_agent`.
- Acionador `CRM - Event Name = <evento>`: evento + Client Name = Data Client | CRM + `ED - chave` igual à chave.
  O Data Client não tem autenticação: sem a chave, qualquer um manda Purchase para o Pixel.
- Tag `00.5 | Meta CAPI - SQL`, `00.6 | Meta CAPI - Purchase`… com `system_generated`, `generateFbp` desligado,
  `client_ip_address`/`client_user_agent` sobrescritos pelos do lead (vazio = não manda), `event_time` da etapa e
  `event_source`/`lead_event_source` no custom data.
- Se um evento do CRM tem o nome de um evento do site (`Lead`), o acionador do site passa a exigir o cliente GA4.

### 5. n8n

Importar **inativo**, escolher as credenciais e conferir o caminho do webhook no `resumo-devolucao.md`. Nós:

1. `Kommo | Mudança de etapa`: webhook POST, responde na hora (o Kommo exige resposta em até 2 s e desliga o
   webhook depois de 100 respostas inválidas em 2 h).
2. `Ler mudança de etapa`: lê os dois formatos (webhook da conta e Digital Pipeline), fica só com etapa mapeada e
   o que ainda não foi enviado.
3. `Kommo | Lead e contatos` e `Kommo | Contato principal`: API.
4. `Montar eventos`: núcleo (`nucleo.js`): telefone E.164, e-mail normalizado, `fbc` a partir do `fbclid`, SHA-256
   para o Google, `event_id = kommo-<lead>-<evento>` (o mesmo em toda repetição: o Meta deduplica por ele e o Google
   pelo `transactionId`).
5. `Só com Meta` → `sGTM | Meta CAPI` → `Meta | Registrar`; `Só com Google` → `Google Ads | Data Manager` →
   `Google | Registrar`. Registrar marca o envio que deu certo (não manda de novo) e escreve a nota no lead.

A nota do Meta diz "entregue ao sGTM": o Data Client responde 200 mesmo se a tag falhar. A prova é o Gerenciador de
Eventos.

### 6. Webhook no Kommo

Configurações → Integrações → Webhooks → URL do n8n, evento **"Etapa do lead alterada"** (dispara em toda mudança; o
n8n filtra). Alternativa por etapa: Leads → Automatizar → etapa → "Send webhook" (Digital Pipeline), uma em cada
etapa mapeada.

### 7. Validação

1. Test Event Code na variável do sGTM; `validar_apenas: true` no Google.
2. Um lead de teste (com `lead_id`/gclid de verdade, ou só telefone) movido para cada etapa mapeada.
3. Meta: Gerenciador de Eventos → Eventos de teste mostra SQL/Purchase com `lead_id`, `system_generated`, **sem**
   IP do servidor do n8n. Nota "entregue ao sGTM" no lead.
4. Google: nota "aceito pela Data Manager API". Depois `validar_apenas: false`, gerar de novo e reimportar.
5. Tirar o Test Event Code, publicar o sGTM com nome claro, ativar o workflow, ligar o webhook.
6. D+2: diagnóstico do dataset no Meta e status da ação de importação no Google.

### 8. Retroativos (no dia em que liga)

`python3 scripts/retroativos.py --brief <brief> --kommo-token <arquivo>` lê `/events` (`lead_status_changed` com
`value_after` por funil e etapa do brief), marca quem tem gclid/gbraid/wbraid e lista o que ainda cabe: Meta até 7
dias, Google até 90 com clique ou 63 com `sem_clique`. Com `--enviar --webhook-url`, cada item vai ao webhook da
devolução no formato do próprio Kommo, com `leads[status][0][last_modified]` = hora da etapa (o núcleo usa como
`event_time`). Mais velho primeiro; 3 s entre envios; nota no lead como qualquer envio; `event_id` repetido não sai
de novo. Só com ok do usuário.

### 9. Colunas no Gerenciador de Anúncios

Nenhuma API salva a predefinição de colunas: o usuário faz. Gerenciador de Eventos → Conversões personalizadas:
"CRM | SQL" (evento SQL; evento personalizado não vira coluna sem ela) e "CRM | Venda" (Purchase com o parâmetro
`event_source` contendo `crm`, porque a loja/e-commerce também manda Purchase ao mesmo Pixel). Depois Colunas →
Personalizar → resultados, custo e valor das duas → salvar como "Funil CRM".

## Diferenças vs Implementação A (Sheets)

| | A (Sheets) | B (Kommo) |
|---|---|---|
| Storage | Planilha Google | CRM Kommo |
| Gatilho da volta | Apps Script onEdit | Webhook do Kommo → n8n |
| Meta | CAPI | sGTM (Data Client → tag CAPI de CRM) |
| Google Ads | CSV agendado ou Data Manager API | Data Manager API |
| Pipeline visual | Não | Sim |

## Armadilhas desta implementação

Em `referencias/armadilhas.md`, seção "Volta da venda": IP do n8n no evento, `fbp` inventado, hora do envio no
lugar da hora da etapa, Data Client aberto, Google Ads API fechada para novos, lead do Lead Ads sem `leadgen_id` no
CRM, host `.kommo.com` bloqueado para o IP do n8n, `lead_id` de 17 dígitos.
