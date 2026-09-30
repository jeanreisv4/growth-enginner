# Armadilhas (cada uma já custou um diagnóstico errado)

Formato: o que aconteceu · como detectar · o que fazer. Cliente entre parênteses (anonimizado na cópia pública).

## Fontes e contagem

- **Mesma métrica, três números.** Vendas do mês podiam ser lançamento manual, CRM por criação ou CRM por
  fechamento, com diferença de 50%+ (indústria de plásticos). Detectar: comparar as três. Fazer: faturamento = data de
  fechamento; safra (eficiência de mídia) = data de criação; declarar no documento.
- **"Ganha" que não é venda.** Pipeline de pré-vendas marcava "Ganha" na passagem para qualificação, com valor
  padrão (indústria de plásticos: 68% exatamente R$ 1.500). Fazer: filtrar só os pipelines de venda antes de calcular ticket.
- **Aba congelada.** Abas bd CRM / bd Analytics paradas meses atrás, com números plausíveis (indústria de plásticos, brindes personalizados).
  Detectar: último dia com dado por base. Fazer: "não medido", nunca zero, e perguntar qual fonte manda.
- **CPL sobre todos os leads.** Dividir a verba por todas as pessoas (inclusive diretas, orgânicas e de outra conta)
  deu R$ 74; o CPL real, só com pessoas únicas da mídia paga V4, é R$ 116 (SaaS de diário de obra). Fazer: CPL = verba ÷ pessoas únicas
  com origem paga da V4, mês a mês e por canal; mostrar o "sem origem" à parte.
- **Linha ≠ pessoa.** Reenvio de formulário, trial + clique em "comprar" e testes da equipe inflam leads
  (SaaS de diário de obra: 152 linhas → 131 pessoas; 65 registros de teste no painel). Fazer: `scripts/leads.py`.
- **Telefone BR.** Comparar últimos dígitos casa 20 de 420; tirar +55 e comparar DDD + 8 finais casa 220
  (indústria de plásticos). Cadastros antigos não têm o 9.
- **Sigla ambígua.** "LT de 3 meses" era tempo de casa, não vida do assinante (SaaS de diário de obra). Perguntar sempre.
- **Duas planilhas com "realizado".** A planilha de projeção tinha um realizado próprio (errado: Google 14× a
  conta) e o oficial estava no Growth Pack, contado à mão (distribuidora de peças automotivas). Detectar: perguntar qual planilha é o realizado
  antes do primeiro gráfico. Fazer: realizado só da fonte oficial; a outra entra só com o projetado.
- **Venda V4 por etiqueta do CRM ≠ contagem manual.** Etiqueta "Lead V4" some quando o vendedor não marca, e safra
  (mês de criação) ≠ mês do ganho (distribuidora de peças automotivas: 16 × 23 em agosto). Fazer: mostrar o número oficial e a conciliação
  mês a mês, pelo mês do ganho.
- **Mix de cliente escondendo a causa.** "Entrada estável e taxa caindo" parecia fechamento; era a recompra da base
  (cliente antigo fecha ~30%, lead novo 2–4%) que caiu de 328 para 100 negócios (distribuidora de peças automotivas). Fazer: sempre separar lead novo
  (negócio aberto no dia do cadastro) de cliente antigo antes de falar em conversão; comparar V4 com lead novo.
- **Etiqueta de origem manual e atrasada.** "Lead V4" posta à mão com 7,8 dias de mediana (distribuidora de peças automotivas): o mês corrente
  sempre parece pior. Detectar: histórico do lead (quem e quando adicionou a etiqueta). Fazer: automação de etiqueta.
- **Disparo em massa inflando conversas.** 4.246 conversas num dia (distribuidora de peças automotivas). Ver distribuição por dia antes de concluir.
- **CRM como registro, não processo.** 1 em 3 negócios nasce já em orçamento/pago; ganho de cliente antigo em 1 min.
  Tempo por etapa só vale para lead novo.
- **Receita sem fonte completa.** Painel sem status de pago e lista de assinantes vista pela metade (SaaS de diário de obra).
  Fazer: reportar piso ("pelo menos 2") e o limite, nunca extrapolar.

- **Leads da plataforma × pessoas únicas.** 137 leads do Meta contra 110 pessoas únicas pareciam "15 perdidos";
  pelas linhas do backup, junho e julho estavam completos (reenvios) e a perda real eram ~9 leads de agosto, com a aba
  vazia de 22 a 31/08 e o Meta gastando todo dia (empresa de revestimento industrial). Fazer: plataforma × LINHAS do backup por dia; dia com
  gasto e sem linha = perda. Recuperar só pelo export da Central de Leads (90 dias).
- **Ticket circular na projeção.** Ticket de R$ 72.581 era exatamente custo ÷ margem (R$ 7.258 ÷ 10%), com ticket
  histórico R$ 0: a projeção fechava o breakeven com 1 venda por construção e marcava "breakeven em jul/26" sem venda
  (empresa de revestimento industrial). Detectar: ticket × (fee + mídia) ÷ margem; projeção feita com 1 mês. Fazer: ticket do CRM (média e
  mediana) e refazer pela skill `projecao-breakeven`.

## Mídia

- **Conta invadida.** 26 campanhas criadas em 43 minutos com 3.150 palavras de cassino e páginas de golpe
  (SaaS de diário de obra). Detectar: `ads_auditoria.py` A4. Fazer: revisar acessos, 2 etapas; o histórico de alterações da API
  só volta 30 dias.
- **Âncora que não existe.** 12 sitelinks para `#1`…`#6` caíam todos no topo (SaaS de diário de obra). A8.
- **Troca de destino que derruba lead.** Anúncios trocados do site para a LP: R$ 849 → 1 lead, contra ~R$ 176
  por lead no site (SaaS de diário de obra). A9. Comparar custo por lead por destino antes de trocar.
- **Promessa que a página não sustenta.** "50% Off nos Planos" sem desconto na página (SaaS de diário de obra). Risco de
  reprovação por declaração enganosa e nota baixa de página.
- **Grátis não é negativa** quando o produto tem teste grátis ("diário de obra gratuito" converteu — SaaS de diário de obra).
- **Marca colada ≠ produto.** "diariodeobra" é concorrente; "diario de obra" é o produto (SaaS de diário de obra).
- **Renomeação.** "Lead Ads | Interesses" era a mesma campanha "03 - [V4]…" renomeada — só o ID prova (SaaS de diário de obra).
- **Segunda conta de anúncios.** IDs de campanha com sufixo diferente dos da V4 (…0325 × …0769) e leads "sem
  permissão" no formulário (SaaS de diário de obra).
- **Público quente mais caro que o frio.** R$ 133 × R$ 52 por lead (SaaS de diário de obra). Checar antes de escalar remarketing.
- **Criativo com CTR alto e sem verba.** O algoritmo não entregou (R$ 47) — testar com orçamento próprio antes
  de descartar (SaaS de diário de obra).
- **Métrica quebrada × dado quebrado.** Se só as métricas com um certo denominador variam 10x, o denominador é
  suspeito (projeção, cliente de climatização).

- **Resíduo da invasão na conta nova.** A conta criada depois da invasão herdou um telefone da Holanda ativo no nível
  da conta e ficou com as campanhas suspensas; o GTM seguia mandando conversões e remarketing para a conta invadida
  (empresa de revestimento industrial). Detectar: `customer_asset` CALL com país ≠ BR; conversion ID das tags × conta que está no ar. Fazer:
  desvincular o ativo (fica na biblioteca, dá para voltar) e apontar o GTM para a conta nova.
- **Verba concentrada no pior anúncio.** O CBO pôs 100% de agosto num anúncio de R$ 48/lead com o de R$ 19 inativo;
  CPL 29 → 120 em quatro meses, com CPM subindo junto com a verba (empresa de revestimento industrial). Comparar custo por lead por anúncio no
  mesmo conjunto e mês antes de culpar público.
- **Conjunto "de região" que não entrega a região.** Conjunto "Interesse Indústria Sudeste" com 56% dos leads de fora
  pelo DDD (empresa de revestimento industrial). Detectar: DDD dos leads por conjunto. Fazer: conferir a localização e perguntar a UF.

## Medição

- **Rótulo com um caractere a menos.** A tag disparava, mas o rótulo não existia: "00.2 Lead" zerou o trimestre
  e o Google só aprendia com o MQL (SaaS de diário de obra). `gtm_auditoria.py` G1 + `teste_disparo.py`.
- **Mesmo acionador como disparo e como exceção.** A tag do Google Ads do pop-up de WhatsApp tinha o evento do
  pop-up nos dois campos: a exceção vence e a conversão nunca saiu, enquanto Meta e GA4 contavam (distribuidora de peças automotivas).
  `gtm_auditoria.py` G5 + `teste_disparo.py` depois de publicar.
- **Plataforma de loja carregando a mesma conta do Google Ads.** A integração nativa da Nuvemshop inicia AW-… numa fila
  própria (`dataLayerTN`) e as tags do Google Ads do GTM param de enviar, até o remarketing de PageView (distribuidora de peças automotivas). Detectar:
  depurar os hits (o parâmetro `gtm=` mostra de onde saem). Fazer: escolher um caminho (nativo ou GTM) e pausar o outro.
- **Container copiado de outro cliente.** Variáveis de outra empresa (nome, domínio, Pixel, UA), ID de conta "111" e
  transporte "editar" (distribuidora de peças automotivas, template da outro cliente). Conferir o valor de cada variável constante, não só o nome.
- **Duas conversões principais na mesma categoria.** Lead e MQL principais = cada MQL conta 2 (SaaS de diário de obra). A2.
- **Categoria sem lance.** "Enviar formulário" não era biddable na meta da conta; as campanhas só contavam ligação
  (indústria de plásticos). Conferir `campaign_conversion_goal`.
- **GA4 do servidor duplicando.** Tag GA4 no sGTM disparando em PageView/Lead/Contact/MQL do Meta (SaaS de diário de obra). G2.
- **GTM preso no banner de cookies.** Construtor de página (GreatPages) carrega GTM e script de atribuição só
  depois do aceite de marketing: GA4 vê ~25% da LP e o lead chega sem UTM (SaaS de diário de obra). `teste_formulario.py`.
  Correção fica no construtor (tirar da categoria Marketing / Consent Mode), não no GTM.
- **UTM do Meta com ID.** utm_source e utm_medium com ID de campanha/conjunto → GA4 "Unassigned" (SaaS de diário de obra).
- **Eventos principais que nunca disparam.** GA4 com key events de template e os eventos reais desmarcados (SaaS de diário de obra).
- **Pixel com evento fantasma.** Meta reportando add-to-cart em página sem carrinho (brindes personalizados).
- **Mídia apontando para o site errado.** Julho inteiro no site B2B sem checkout (brindes personalizados).
- **Clarity não é histórico.** A Data Export API só devolve as últimas 24–72 h e 10 chamadas por projeto por dia
  (a cota é do projeto: outra ferramenta usando o mesmo token come a sua). Colete no primeiro dia da sprint e
  todo dia depois; com menos de 7 dias acumulados, a confiabilidade é média. `clarity.py` não repete chamada do dia.
- **Campo do Clarity com nome não documentado.** A documentação só mostra os campos de Traffic; os de fricção são
  lidos pelo padrão do nome. Se o resumo listar campo não reconhecido, ajuste `clarity.linhas()` antes de concluir.

- **Filtro que esconde credencial morta.** O fluxo do n8n rodava a cada 10 min com "success", mas o filtro devolvia 0
  itens e nunca chamava o CRM; a credencial do Kommo dava 401 havia dias (empresa de revestimento industrial). Execução com sucesso não prova
  integração: testar a credencial com um GET direto.
- **Ferramenta de terceiros muda o layout da planilha.** O Make passou a gravar o ID do lead do Meta na coluna de
  controle "Enviado ao Kommo" e o n8n tratou a linha como enviada (empresa de revestimento industrial). Coluna de controle aceita só o
  marcador no formato do próprio fluxo (regex), nunca "preenchida = enviada".
- **LP sem destino por semanas.** A aba da LP não teve nenhuma linha de 22/06 a 20/08 com o Google gastando: o fluxo
  foi criado depois do início da mídia e os leads ficaram só no construtor (empresa de revestimento industrial). Cruzar dias com gasto × dias
  com linha; recuperar pelo export do construtor.
- **Site institucional com GA4 de outra conta.** O site tinha GA4 próprio fora do acesso da V4 e nenhum GTM, e o
  WhatsApp dele era o mesmo que fechava as vendas "sem origem" (empresa de revestimento industrial). Pedir acesso e medir antes de mandar mídia.

## Funil e comercial

- **Canal que gera lead e não alimenta a etapa seguinte.** 57 de 59 leads do formulário nativo do Meta nunca
  entraram no painel de trial (SaaS de diário de obra).
- **Follow-up parado.** Último "em contato" em 28/08; 7 pessoas clicaram em "assinar" e ninguém falou com elas
  (SaaS de diário de obra). As 2 vendas vieram de leads contatados.
- **Capacidade comercial é a restrição.** Correlação leads × vendas negativa; mais verba não vira venda
  (indústria de plásticos). Testar lead × capacidade antes de pedir verba.
- **IA de primeiro atendimento sem segundo toque.** 77 negócios parados em "Ativado IA" (indústria de plásticos).

- **Busca por nome no CRM falha em card de WhatsApp.** No Kommo, o contato do WhatsApp tem outro nome: por nome
  deu 3 leads "fora do CRM", pelo telefone era 1 (empresa de revestimento industrial). Casar sempre por DDD + 8 dígitos.
- **Caixa de entrada fora da API padrão.** No Kommo, a etapa "Leads de entrada" não vem no `/leads` padrão (filtrar
  por etapa); havia 111 conversas nunca triadas, 44 com o cliente falando por último (empresa de revestimento industrial).
- **Data de criação retroativa e perda em lote.** Cards criados por automação com hora fixa (13:17) e 92 perdidos no
  mesmo minuto: "Sem resposta" e tempo até o primeiro contato não medem nada nesses cards (empresa de revestimento industrial).
- **Formulário sem nenhum toque no CRM.** 130 de 151 leads de formulário da V4 sem mensagem, nota ou tarefa, 0 venda,
  enquanto o WhatsApp respondido fechava 8,6% (empresa de revestimento industrial). A restrição era contato, não mídia.
- **Régua de MQL que aprova quase todos.** O formulário perguntava 3 dos 6 critérios e a régua reescalava para 100:
  81% viravam MQL (empresa de revestimento industrial). Taxa de MQL acima de 60% = régua sem poder de corte; perguntar o que falta.
- **Negócio com logística.** Serviço em campo (equipe vai ao cliente) × galpão (peça viaja com frete de ida e volta
  pago pelo cliente): lead de fora da região só serve em campo e com porte grande (empresa de revestimento industrial: 54 de 74 leads de
  fora eram peça de galpão). Qualificar por região × modalidade, não só por região.

## Execução

- **Agente não conversa.** O agente de frente não pergunta ao usuário; o que falta vem em `perguntas` no JSON.
  Não o use para validar mudança nem para pedir ok: execução é sempre da conversa principal.
- **Agente novo só aparece em conversa nova.** Depois de `instalar_agentes.py`, a conversa aberta não enxerga o
  agente; até lá, rode a frente com `general-purpose` passando o arquivo do agente como instrução.

- **Publicar GTM, criar fluxo no n8n, extrair código de painel**: o modo automático pode negar. Parar, explicar,
  deixar com o usuário. Nunca contornar.
- **Upload de conversão offline** em conta nova: API recusa (Data Manager API). Gerar CSV para upload manual.
- **Conversões do YouTube** não mudam pela API. Nem as do Google hospedadas (ações locais, ligações de campanha
  inteligente, metas do Universal Analytics, instalação de app): MUTATE_NOT_ALLOWED. Tire do lance pela meta da
  campanha (`campaign_conversion_goal.biddable = false` por categoria), que a API aceita (distribuidora de peças automotivas).
- **Workspace do GTM usado** depois de criar versão: pegar o workspace novo antes de editar.
- **n8n corta resposta grande** (IncompleteRead) ou devolve 502: `mcp_http.py` tenta de novo; reduza a consulta.
- **Credencial nova no n8n pela API** exige `allowedHttpRequestDomains` (use `domains` + o domínio do CRM).
- **Arquivo bruto com segredo.** O dump do GTM gravava o token da API de Conversões em texto; `gtm_auditoria.py` agora
  mascara segredos antes de gravar. Arquivo bruto de cliente nunca vai para o documento nem para o GitHub.
- **Token do GA4 renovado e MCP ainda com o antigo.** Depois do `gcloud auth application-default login`, o
  `analytics-mcp` já aberto na conversa segue com `invalid_grant`: use um processo novo (`ga4_resumo.py`) ou conversa nova.
- **ID real em teste ou exemplo.** Um teste da regressão levou o ID real de um Pixel e de um GA4 para o GitHub; o
  mapa de nomes não pega ID. `publicar.py --conferir` agora cruza a cópia com todos os IDs dos `config.json` de clientes.
