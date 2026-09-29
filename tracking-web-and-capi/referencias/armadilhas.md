# Armadilhas de tracking (cada uma já quebrou a medição de um cliente)

Formato: o que aconteceu · como detectar · o que fazer. Cliente entre parênteses (anonimizado na cópia pública).
Os scripts citados como `sprint-growth/...` ficam na skill irmã, na mesma pasta do growth-enginner.

## Tags e containers

- **`inheritEventName` booleano no template da CAPI (Stape).** O parâmetro é SELECT (`"inherit"` ou `"override"`);
  `true` faz a tag sair sem `event_name` e o Meta devolve 400 (cliente piloto (carpetes B2B)). Detectar: `gerar_containers.py`
  bloqueia. Fazer: `"override"` + `eventNameStandard` ou `eventNameCustom`.
- **`gtm.formSubmit` não dispara em formulário AJAX.** O construtor envia sem recarregar (cliente piloto (carpetes B2B)). Fazer:
  Lead na página de obrigado (PAGEVIEW) ou num evento do dataLayer que o próprio formulário empurra.
- **Variável que lê o DOM na página de obrigado.** O formulário não existe mais lá (cliente piloto (carpetes B2B)). Fazer: tag HTML
  guarda os campos em `sessionStorage` no envio; as variáveis leem de lá (já no template).
- **Rótulo de conversão com um caractere a menos.** A tag dispara, o Google não reconhece e a conversão zera por
  meses (SaaS de diário de obra: "00.2 Lead" zerado; o Google só aprendia com o MQL). Detectar: `sprint-growth/scripts/gtm_auditoria.py`
  (G1, compara com a conta) + `sprint-growth/scripts/teste_disparo.py`. `gerar_containers.py` avisa rótulo fora de
  20 caracteres.
- **ID da conta e rótulo trocados.** O número da conta no campo do rótulo e vice-versa. `gerar_containers.py`
  bloqueia rótulo só com dígitos.
- **Mesmo acionador como disparo e como exceção.** A exceção vence: a tag do Google Ads do pop-up nunca disparou,
  enquanto Meta e GA4 contavam (distribuidora de peças automotivas). Detectar: `sprint-growth/scripts/gtm_auditoria.py` G5 e o teste de disparo.
- **Mesmo rótulo em duas tags.** Duas ações contam a mesma conversão (G4). `gerar_containers.py` bloqueia.
- **URL de exemplo no transporte do servidor.** `gtm.dominio.com.br` esquecido no template: nada chega ao sGTM
  (móveis planejados). `gerar_containers.py` bloqueia URL de exemplo ou sem https.
- **GA4 do servidor repassando eventos do Meta.** Tag GA4 no sGTM disparando em PageView/Lead/Contact/MQL duplica
  eventos no GA4 (SaaS de diário de obra). G2.
- **Tag pausada ou sem acionador.** G3. Conferir antes de dizer "não chega nada".
- **Test Event Code em produção.** Todo evento vira teste e não conta (cliente piloto (carpetes B2B)). Gerar com `--producao`.
- **Token da CAPI em print.** Vazou várias vezes no piloto; token exposto = token trocado (cliente piloto (carpetes B2B)). O brief
  do gerador recusa token; ele vai direto no GTM Server.

## Página e consentimento

- **GTM preso no banner de cookies.** O construtor (GreatPages) só carrega o GTM e o script de atribuição depois do
  aceite de marketing: o GA4 vê ~25% da LP e o lead chega sem UTM (SaaS de diário de obra). Detectar:
  `sprint-growth/scripts/teste_formulario.py`. Fazer: no construtor (tirar da categoria Marketing, Consent Mode v2),
  não no GTM.
- **Botão de WhatsApp em widget ou popup.** O widget abre o `wa.me` por JavaScript, sem clique em link, e o
  acionador LINK_CLICK não pega nada (loja de tecidos). Fazer: acionador no evento do widget (o template já tem
  `JoinChat`) ou evento customizado empurrado pelo popup.
- **Formulário sem campos ocultos de origem.** UTM, gclid e fbclid não saem do formulário para o Make, n8n ou CRM:
  sem eles não existe volta de venda para as plataformas (SaaS de diário de obra, móveis planejados). Detectar: `teste_formulario.py`
  mostra o POST. Fazer: campos ocultos preenchidos da URL e dos cookies `_gcl_aw` e `_fbc`.

## Conta de anúncios e GA4

- **Duas conversões principais na mesma categoria.** Lead e MQL principais: cada MQL conta 2 e o lance otimiza
  para o número inflado (SaaS de diário de obra, móveis planejados). Fazer: uma principal por etapa do funil; as outras secundárias.
- **Categoria sem lance na meta da conta.** "Enviar formulário" fora das metas usadas pelas campanhas: a campanha
  só contava ligação (indústria de plásticos). Conferir `campaign_conversion_goal`.
- **Conversão inteligente de ligação ou WhatsApp inflando.** Ações automáticas do Google contando clique no
  telefone como conversão principal (distribuidora de peças automotivas). Fazer: secundárias até existir a venda medida.
- **Key events do GA4 que nunca disparam.** Eventos do template marcados e os reais desmarcados (SaaS de diário de obra).
- **UTM do Meta com ID.** `utm_source`/`utm_medium` com ID de campanha: GA4 joga em "Unassigned" (SaaS de diário de obra). Fazer:
  `utm_source=facebook`, `utm_medium=paid_social`, nome em `utm_campaign`, IDs em `utm_id`/`utm_content`.
- **Evento fantasma no Pixel.** Meta reportando add-to-cart em página sem carrinho (brindes personalizados). Conferir a
  aba de eventos do Pixel contra o que o site tem.

## Volta da venda (CRM → plataformas)

- **Venda que começa no WhatsApp sem origem.** O clique para o WhatsApp só guarda o anúncio se o CRM tiver o
  tracking de CTWA ligado (DataCrazy: `conversation.sourceReferral` vazio em 17 mil conversas na distribuidora de peças automotivas). Fazer:
  ligar o tracking no CRM e mandar Purchase pela CAPI a partir do negócio ganho.
- **Etiqueta de origem manual.** "Lead V4" posta à mão, metade das vezes, com 7,8 dias de mediana (distribuidora de peças automotivas): o
  mês corrente sempre parece pior. Fazer: etiqueta por automação na entrada do lead.
- **Upload offline em conta nova.** A API recusa conversões offline sem a Data Manager API (SaaS de diário de obra). Fazer: CSV
  agendado no Google Ads até liberar a API.
- **Back-pass que nunca foi ligado.** Tracking "pronto" só com Lead: as plataformas otimizam para volume, não para
  venda (cliente piloto (carpetes B2B), pendente). O checklist bloqueia quando a venda já acontece.
