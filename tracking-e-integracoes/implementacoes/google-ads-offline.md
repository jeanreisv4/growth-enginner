# Implementação: conversões offline no Google Ads (Data Manager API)

> Etapa do CRM (SQL, venda) → Google Ads, com gclid/gbraid/wbraid e e-mail/telefone com hash.

**Status:** ✅ Em uso (v2.0.0) · **Relacionados:** `crm-kommo.md` (bloco `google` do `devolucao`), agente `integracao-google-ads`

---

## Por que Data Manager e não a Google Ads API

Desde 15/06/2026 o `UploadClickConversions` da Google Ads API não aceita quem não importava offline no semestre
anterior: devolve `CUSTOMER_NOT_ALLOWLISTED_FOR_THIS_FEATURE`. O caminho é a **Data Manager API**:
`POST https://datamanager.googleapis.com/v1/events:ingest`, escopo `https://www.googleapis.com/auth/datamanager`,
destino = conta (`operatingAccount`) + `productDestinationId` = id da conversion action, `encoding: HEX`,
`validateOnly` para testar sem gravar.

## Passo a passo

1. **Conta**: `SELECT customer.conversion_tracking_setting.* FROM customer` — termos de dados do cliente aceitos?
   Campanhas rodando (`metrics.cost_micros` por mês)? Sem campanha, não há clique novo com gclid: montar é ok, mas
   dizer ao usuário que nada vai sair até as campanhas voltarem.
2. **Conversões de importação** (`UPLOAD_CLICKS`), uma por etapa, criadas **secundárias** (`primaryForGoal: false`)
   para não mexer no lance: SQL (categoria `QUALIFIED_LEAD`, valor proxy) e venda (`CONVERTED_LEAD`, ticket).
   `googleAds:mutate` pelo webhook de escrita com `validateOnly` antes. Virar principal é decisão do usuário, e quando
   virar, a conversão de formulário que dobra a contagem (Lead e MQL principais juntas) vira secundária.
3. **Conversões otimizadas para leads**: só pela interface (Metas → Conversões → Configurações). O campo
   `enhanced_conversions_for_leads_enabled` é só leitura na API. Necessário para mandar e-mail/telefone sem clique.
4. **Projeto do Google Cloud**: ativar a Data Manager API no projeto do cliente OAuth usado pelo n8n.
5. **Credencial n8n** `oAuth2Api` (pela API: `serverUrl: ""`, `grantType: authorizationCode`,
   `authUrl https://accounts.google.com/o/oauth2/v2/auth`, `accessTokenUrl https://oauth2.googleapis.com/token`,
   `authQueryParameters: access_type=offline&prompt=consent`, domínio permitido `datamanager.googleapis.com`).
   Connect pela interface, com a conta Google que acessa a conta de anúncios.
6. **Testar**: `validateOnly: true` numa chamada direta (HTTP 200 com `requestId` "v-…") e dentro do workflow da
   devolução (código de teste do Meta + `validar_apenas` + `sem_clique` por alguns segundos, depois volta).
7. **Brief** `devolucao.google`: `customer_id`, `acoes` {SQL, Purchase}, `fuso`, `sem_clique` (padrão false: só lead
   com clique), `validar_apenas` (false em produção).

## Fonte = planilha (sem CRM)

Quando o lead só existe na planilha (backup da LP) e o MQL é uma resposta do formulário, a devolução sai da
planilha: `scripts/devolucao_planilha.py --csv <export CSV> --filtro "utm_source=google" --filtro "<coluna>=<valor>"
--data-col ... --tel-col ... --email-col ... --customer ... --acao ... [--mcc ...] --credencial ... --n8n ... --n8n-key ...`.
Sem flag só lista; `--validar` manda com `validateOnly`; `--enviar` grava. `transactionId` estável (prefixo + data +
hash do telefone): reenviar a planilha inteira não duplica, então dá para rodar de novo sempre que entrar MQL.

## Erros da Data Manager (uso real)

| Resposta | Causa | Fazer |
|---|---|---|
| 403 `PERMISSION_DENIED`, `field_path: destinations[0]` | conta acessada pela MCC sem `loginAccount` | `login_customer_id` / `--mcc` |
| 400 `destination_references` `NOT_FOUND` | ação criada há pouco (propagação de 10 a 35 min) | validar de 5 em 5 min |
| 403 sem `destinations` | credencial sem acesso ou API desligada no projeto | Connect com a conta certa; ativar a API |

## De onde vem o gclid

- **LP**: o formulário manda a URL da página (com a query); o n8n lê `gclid`, `gbraid`, `wbraid`, `fbclid` e grava
  nos campos de rastreio do CRM (Kommo tem `gclid`/`fbclid` nativos, tipo `tracking_data`). **Só o gclid vai no campo
  gclid**: gbraid/wbraid no campo gclid seriam recusados como gclid.
- **Formulário do Meta**: não tem gclid. O Google só recebe esses leads com `sem_clique: true` (hash do e-mail e do
  telefone), e só casa se a pessoa também clicou num anúncio do Google.
- **RD Station CRM**: `scripts/devolucao_rd.py` (contínuo de hora em hora + retroativo pelo histórico de etapas).
- Janela: gclid vale 90 dias; conversão só com dados do usuário, 63 dias. Retroativos: `scripts/retroativos.py`.

## Colunas e conversão principal

- Importação secundária não entra em "Conversões": coluna personalizada "Todas as conv." filtrada pela ação (e "Valor
  de todas as conv." para a venda), num conjunto de colunas "Funil CRM". A API só lê coluna personalizada.
- Duas conversões de formulário principais (Lead e MQL) = contagem em dobro. Antes de escolher, `all_conversions` por
  ação e mês em 12 meses: fica principal a que tem histórico. `conversionActionOperation.update` com
  `updateMask: primaryForGoal`, `validateOnly` antes, conferir depois e deixar o script de desfazer.
- Venda do CRM principal só quando houver volume com clique (gclid na LP) e as campanhas estiverem rodando.
- Credencial OAuth do n8n: se o app do Google Cloud está "Em teste", o refresh token vence em 7 dias e a devolução
  para. Publicar o app (Google Auth Platform → Público) antes de entregar.
