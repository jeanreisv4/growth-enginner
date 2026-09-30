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
- **Integração nativa da loja com a mesma conta do Google Ads.** A Nuvemshop carrega AW-… pela fila `dataLayerTN` e as
  tags do Google Ads do GTM não enviam, nem o remarketing (distribuidora de peças automotivas). Escolher um caminho e pausar o outro.
- **Container copiado de outro cliente.** Constantes com ID "111", rótulo com o número da conta, transporte "editar" e
  variáveis de outra empresa (distribuidora de peças automotivas). O gerador de containers evita isso; em container herdado, conferir cada constante.
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
  Qual fica principal: a que tem histórico (`metrics.all_conversions` por ação e mês, 12 meses), não a "melhor" no
  papel. Na distribuidora de automatizadores a MQL nunca tinha registrado conversão (Lead: 61 de mar a jun); virar a MQL principal deixaria o lance
  sem dado. A que nunca disparou é sinal de tag quebrada: conferir antes de otimizar por ela.
- **Conversão secundária some da coluna "Conversões".** As importações do CRM nascem secundárias e só aparecem em
  "Todas as conv." (distribuidora de automatizadores). Fazer: coluna personalizada = "Todas as conv." filtrada pela ação (e "Valor de todas as
  conv." para a venda), salva num conjunto "Funil CRM". Coluna personalizada é só leitura na API: o usuário cria.
- **Purchase da loja misturado com a venda do CRM.** O Pixel já recebe Purchase da integração da loja (Tray na distribuidora de automatizadores):
  a coluna "Compras" soma as duas. Fazer: conversão personalizada "CRM | Venda" = Purchase com o parâmetro
  `event_source` contendo `crm` (a devolução manda), e "CRM | SQL" = evento SQL (evento personalizado não vira coluna
  sem ela). A predefinição de colunas do Gerenciador de Anúncios é da interface, não da API: o usuário salva.
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
- **Upload offline em conta nova.** A API recusa conversões offline sem a Data Manager API (SaaS de diário de obra). Desde
  15/06/2026 a Google Ads API (`UploadClickConversions`) não aceita quem não importava offline no semestre anterior:
  `CUSTOMER_NOT_ALLOWLISTED_FOR_THIS_FEATURE`. Fazer: Data Manager API (`events:ingest`, escopo
  `auth/datamanager`), já no `scripts/devolucao.py`; CSV agendado só como plano B.
- **Conta sob gerente na Data Manager.** Só `operatingAccount` numa conta que a credencial acessa pela MCC devolve
  403 "The caller does not have permission" em `destinations[0]` — parece falta de acesso, mas é o `loginAccount`
  (fabricante de acessórios para cortina, 30/09/2026). Fazer: `loginAccount` = MCC (`login_customer_id` no brief,
  `--mcc` no `devolucao_planilha.py`).
- **Ação de conversão recém-criada.** Logo depois de criar a importação, a Data Manager responde 400
  `destination_references NOT_FOUND` de 10 a 35 min (12 e 35 nos dois casos reais). Não é erro de id: validar de 5
  em 5 min e só enviar quando o `validateOnly` der 200.
- **Sem CRM, a qualificação está na planilha.** Quando o MQL é uma resposta do formulário (ex.: linha = alto padrão)
  e o comercial não atualiza status, o sinal de qualidade que dá para devolver é essa resposta, desde que a LP grave
  gclid/gbraid/wbraid na planilha. Fazer: `scripts/devolucao_planilha.py` numa importação secundária; sem hora na
  planilha, 23:59 do dia do lead (nunca antes do clique; lead de hoje espera amanhã).
- **Back-pass que nunca foi ligado.** Tracking "pronto" só com Lead: as plataformas otimizam para volume, não para
  venda (cliente piloto (carpetes B2B), pendente). O checklist bloqueia quando a venda já acontece.
- **IP do n8n chegando ao Meta como IP do lead.** O Data Client da Stape preenche `ip_override` e `user_agent` com
  quem faz a chamada; a tag CAPI manda isso como `client_ip_address`: todo evento de CRM sai com o IP do servidor
  (visto no código dos templates antes do go-live da distribuidora de automatizadores). Fazer: `userDataList` da tag de CRM sobrescreve os dois
  com `{{ED - lead_ip}}`/`{{ED - lead_user_agent}}` (vazio = não manda). O gerador já faz.
- **`fbp` inventado no evento de CRM.** Com `generateFbp` ligado e sem cookie no pedido do n8n, a tag cria um
  navegador novo a cada evento. Fazer: desligado nas tags de CRM.
- **Hora do envio no lugar da hora da etapa.** A tag usa "agora" se o `event_time` não for sobrescrito; em lote,
  tudo cai no mesmo minuto. Fazer: `serverEventDataList` com `{{ED - event_time}}`. O Meta aceita até 7 dias.
- **Data Client aberto.** O template não tem autenticação: quem souber a URL manda Purchase para o Pixel. Fazer:
  acionador exige `{{ED - chave}}` igual à constante `00 - Devolução - Chave` e o Client Name do Data Client.
- **Data Client responde 200 mesmo com a tag falhando.** O "200" do n8n só prova que o sGTM recebeu. Fazer: a nota
  no lead diz "entregue ao sGTM"; a prova é o Gerenciador de Eventos.
- **Evento do CRM com o nome de um evento do site.** Etapa "Lead" (a de entrada, que o Conversion Leads pede)
  dispara também a tag de Lead do site, como `website`. Fazer: acionador do site exige o cliente GA4 (container
  novo já sai assim; container existente, ajustar pela MCP).
- **Lead do formulário instantâneo sem `leadgen_id` no CRM.** A planilha/automação guarda telefone, nome e UTM, mas
  não o id do lead do Meta (distribuidora de automatizadores: aba do formulário nativo sem a coluna). Sem ele o evento casa só por
  telefone/e-mail e não entra na otimização por lead de conversão. Fazer: gravar o `leadgen_id` num campo do lead
  na entrada.
- **`lead_id` de 17 dígitos virando número.** Passa do inteiro seguro do JavaScript e perde o final; o Meta recusa
  `lead_id` inválido. Fazer: texto, validado com 15-17 dígitos (o núcleo já faz).
- **Host `.kommo.com` bloqueado para o IP do n8n.** O edge do Kommo devolve 403 em HTML do nginx, com e sem token,
  antes da aplicação (distribuidora de automatizadores, 10/09/2026). Fazer: alias `https://<subdominio>.amocrm.com/api/v4`, mesma conta e API.
- **Webhook do Kommo desligado sozinho.** Resposta acima de 2 s ou fora de 2xx conta como inválida; mais de 100 em
  2 h desliga o webhook. Fazer: webhook do n8n com resposta imediata (`onReceived`) e o processamento depois.
- **Data Client da Stape fora da galeria do GTM.** O README diz "Not listed": `import_from_gallery` devolve 404 "Not found
  or permission denied" (não é permissão). Fazer: importar `templates/gtm/data-client.tpl` à mão (Modelos → Novo →
  Importar) uma vez por container; o resto (cliente, variáveis, acionadores, tags) vai pela MCP (distribuidora de automatizadores, 30/09/2026).
- **Constante vazia recusada pela API do GTM.** `vendorTemplate.parameter.value: The value must not be empty`: a variável
  do Test Event Code não pode ser criada vazia pela MCP. Fazer: no container existente, sem `testId` na tag; no teste,
  pôr o código direto na tag e tirar depois.
- **142 não é venda em todo funil.** O status 142 é o "ganho" de qualquer funil, mas cada funil dá o nome que quer
  (distribuidora de automatizadores: "Pedido ganho" no de vendas, "reengajamento" no pós-venda). Fazer: `devolucao.funis` sempre preenchido.
- **Lead que só nasce no CRM quando qualifica.** A IA do SDR atende no WhatsApp e cria o lead no Kommo já como MQL: o
  lead bruto do formulário não existe no CRM e o `leadgen_id` se perde. Fazer: guardar o `leadgen_id` por telefone na
  captura (n8n) e a devolução buscar por telefone; não criar lead antes da IA, senão duplica a negociação.
- **Container da Stape desativado sem ninguém ver.** Plano gratuito parado: o endereço do sGTM responde "404 page not
  found" em tudo, até no `/healthy` (que num sGTM vivo responde `ok`), o Preview do GTM não abre e a CAPI do site para;
  no Pixel só sobram os eventos de servidor da integração da loja (distribuidora de automatizadores, 30/09/2026: nenhum Lead/Contact/MQL de
  servidor em 14 dias). Detectar: `curl <sgtm>/healthy` antes de qualquer auditoria. Fazer: reativar e conferir o
  status "Running" no painel; para a devolução do CRM, o modo direto (`meta_via: "direto"`) não depende da Stape.
- **Kommo responde `application/hal+json` e o n8n lê como texto.** O lead chega como string em `data`, o nó seguinte
  não acha `_embedded.contacts` e o evento sai sem telefone (distribuidora de automatizadores, teste de 30/09/2026). Fazer: "Response Format: JSON"
  em todo nó HTTP do Kommo (o gerador já põe) e o código tolerante a texto.
- **Celular sem o 9º dígito.** Contato criado pelo WhatsApp fica `55 DD 8 dígitos`; o cadastro da pessoa no Meta tem o
  9. Fazer: no modo direto, `ph` vai com as duas versões (o núcleo já faz).
- **Lead do formulário sem id no CRM, mas o Meta tem.** Os leads ficam 90 dias na Graph API (`/{formulário}/leads`):
  a devolução acha o id pelo telefone na hora de enviar (`meta_leadgen`). Na distribuidora de automatizadores, 91 dos 220 telefones do Funil de
  vendas (60 dias) estavam no formulário; os outros vieram por WhatsApp direto ou são mais antigos.
- **Credencial OAuth "conectada" sem token.** "Unable to sign without access token" no primeiro nó = o Connect não
  terminou (erro no Facebook que fechou a janela). Testar com um workflow temporário que lê a página antes de ligar.
- **Integração que para de criar lead no CRM sem erro visível.** O cenário do Make seguia gravando na planilha, mas
  parou de criar o lead no Kommo em 31/08/2026: 57 de 66 leads do formulário de 16 a 30/09 não estavam no CRM (distribuidora de automatizadores).
  Detectar: cruzar os leads do formulário pela Graph API (`/{formulário}/leads`) com os contatos do CRM por telefone
  (DDD + 8 dígitos), semana a semana, por origem do lead. Fazer: entrada direta Meta → n8n (app próprio) com falha
  virando erro, e o cruzamento como checagem periódica.
- **Recuperação em massa derruba a gravação em planilha.** 73 leads recuperados de uma vez → a IA do SDR abordou
  todos → rajada de eventos do Chatwoot → 20 escritas perdidas por cota do Google Sheets, mesmo com 5 tentativas de 5 s
  (distribuidora de automatizadores, 30/09/2026). Fazer: gravação com saída de erro → espera sorteada (20–80 s, depois 2–4 min) → nova tentativa;
  e recuperar em lotes espaçados quando houver automação reagindo aos leads criados.
- **Devolução ligada sem os retroativos.** Ela só manda as mudanças de etapa novas; o que aconteceu antes fica fora, e
  a janela fecha rápido: Meta 7 dias, Google 90 com gclid e 63 só com dados do usuário (distribuidora de automatizadores, 30/09/2026: das 59
  entradas em SQL e 37 vendas em 90 dias, 1 + 1 ainda cabiam no Meta, uma a 1 h de vencer; nenhuma com gclid).
  Fazer: `scripts/retroativos.py` no dia em que a devolução liga, mais velho primeiro, com a hora real da etapa
  (`last_modified` no webhook) — mandar com a hora do envio seria atribuir a venda ao anúncio errado.
- **Script de teste imprimindo o evento montado.** O resultado do nó "Montar eventos" tem nome e telefone em texto;
  mostrar a saída do n8n inteira expõe o lead no terminal (distribuidora de automatizadores). Fazer: resumir (evento, hora, tem `lead_id`, valor,
  o que faltou), nunca o `user_data`.
- **Conexão que vence depois da entrega.** O fluxo não quebra, a credencial sim: token de usuário do OAuth do Meta
  (em geral ~60 dias, conferir no Depurador de token), app do Google Cloud "Em teste" (o refresh token vence em 7
  dias: publicar o app), token do CRM com validade escolhida na criação, e troca de token que passou pelo chat feita
  só no CRM/Meta e não no n8n. Fazer: na entrega, tabela com cada conexão e a data; fluxo de erro do n8n avisando.

