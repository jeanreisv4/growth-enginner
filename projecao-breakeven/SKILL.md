---
name: projecao-breakeven
description: Projeção de breakeven de mídia paga a partir do histórico do cliente (planilha padrão V4, CRM, export de mídia e GA4). Use sempre que o usuário pedir projeção de breakeven, payback de mídia, "em que mês o projeto se paga", ou enviar a planilha de indicadores de um cliente querendo saber se a meta de breakeven é realista. Conduz a entrevista (fonte, modelo, fee, mídia, mês-alvo), calcula as taxas efetivas, dá o veredito de realismo e preenche o template (inside sales ou e-commerce) sozinha.
---

# Projeção de breakeven

**Versão 7.4 (23/09/2026).** O histórico está em `CHANGELOG.md`. Os caminhos abaixo são relativos à pasta da skill (`.claude/skills/projecao-breakeven/`).

A skill tem duas metades. A primeira é a entrevista: ela **conduz**, e não espera o usuário lembrar o que precisa informar. A segunda é a execução automática: com as premissas confirmadas, ela roda o piloto, dá o veredito e preenche o template, sem etapa manual.

**Antes de começar, leia a referência do modelo:** `referencias/ecommerce.md` ou `referencias/inside_sales.md`. Elas trazem as armadilhas das planilhas reais e os casos que servem para calibrar se o resultado faz sentido.

## 1. Entrevista (sempre nesta ordem, uma pergunta por vez)

**1.0 Frentes contratadas.** Antes de tudo, pergunte o que o contrato cobre, porque cada frente acrescenta um bloco à projeção e tem perguntas próprias: mídia paga (sempre), SEO e tráfego orgânico (1.6.1), CRM e base (1.6.2), social e conteúdo, remarketing (1.6.3) e a operação comercial (inside sales). Só entra na projeção o que está contratado e medido; o resto vira observação. Pergunte também o que o fee cobre e se alguma frente entra depois (ex.: CRM a partir de outubro, com `--fee-plano`).

**1.1 Fonte da verdade.** Pergunte de onde vêm os dados históricos. Opções aceitas: planilha padrão V4 (aba `Indicadores`, mensal), export do CRM (Kommo ou HubSpot, por lead), export de mídia (Meta ou Google, diário). Se o usuário mandar um link do Google Sheets, use o `gid` da URL como aba. Planilha privada (o export dá 401): leia pelo conector do Google Drive (`read_file_content`), salve a aba Indicadores como `indicadores.csv` na pasta do cliente e passe o CSV ao piloto (multimídia automotiva). Se mandar arquivo, use o arquivo. Nunca invente dados que não estejam na fonte.

**1.1.0 Qual fonte manda.** Se existir mais de uma planilha (ou mais de uma aba) com o mesmo mês, **pergunte qual manda antes de ler qualquer número** e registre a resposta nas observações. Não concilie por conta própria: na indústria de plásticos, janeiro aparecia com R$ 13.074 numa aba e R$ 45.759 na outra, e a projeção inteira muda conforme a escolha. Pergunte também **o que não é fonte** — planilhas paradas, abas congeladas, bases que deixaram de atualizar. Depois de escolhida, a fonte é uma só: nunca some número de duas.

**1.1.0.1 Como as vendas são contadas.** Antes de projetar, pergunte três coisas sobre a linha de vendas da fonte: (a) vem de **lançamento manual ou do CRM**; (b) é por **data de criação ou de fechamento** do negócio; (c) inclui **recompra da base** ou só cliente novo. As três mudam o número na casa das dezenas de por cento — lançamento manual costuma subcontar, e criação contra fechamento desloca a venda de mês. Se a fonte for manual e existir CRM, diga ao usuário que o número está provavelmente abaixo do real e ofereça refazer pelo CRM.

**1.1.1 E-commerce.** O funil da planilha fica no bloco GA4 e é do site inteiro. A receita atribuída fica em "Receita Captada V4". Meses com conversão sem valor não servem de histórico: aponte e proponha `--desde`. Detalhes em `referencias/ecommerce.md`.

**1.1.2 GA4.** Se o servidor `analytics-mcp` estiver configurado, pergunte se o cliente tem GA4 e localize a propriedade (`get_account_summaries`). Rode `python3 scripts/ga4_resumo.py --propriedade <id> --meses <mês/ano,...> --ate <último dia da planilha no mês corrente> --out ga4.json` e passe `--ga4 ga4.json` ao piloto.
- O corte do mês corrente é o mesmo da planilha. Confira comparando os cliques do Google Ads no GA4 com os cliques da fonte.
- Com o GA4, o piloto separa Google (funil por CPM, CTR e connect) e Meta (verba ÷ custo por sessão).
- Carrinho e checkout do pago passam a ser medidos, e as sessões não pagas vêm do GA4.
- Pedidos e receita continuam da fonte, na atribuição das plataformas.

**1.2 Modelo.** Pergunte qual template preencher: `inside_sales` (lead → conexão → MQL → SQL → venda) ou `ecommerce` (clique → sessão → carrinho → checkout → pedido). Se a fonte só tem as linhas de um dos dois, sugira esse e peça confirmação.

**1.3 Fee e mídia.** Rode `python3 scripts/breakeven_pilot.py detectar --fonte <arquivo ou URL> --aba Indicadores --modelo <modelo>` e apresente o que foi lido: meses fechados, mês corrente, fee, mídia planejada, mídia realizada média e margem.
- **Peça confirmação explícita do fee e da verba mensal**, mesmo que tenham sido detectados. O usuário pode corrigir (renegociação de fee, plano de mídia novo). Nunca projete com valores não confirmados. Se o fee do contrato diverge da linha Fee V4 da fonte (EZ: R$ 6.901 no contrato, R$ 9.000 no Growth Pack), use `--fee-historico` para aplicar o fee certo também no déficit e no realizado, e avise que a fonte precisa ser corrigida.
- Pergunte o plano de verba. Pode ser crescimento mensal com teto (`--crescimento-midia`, `--midia-teto`) ou degraus mês a mês (`--verba-plano 2000,4000,5000,5000`), que ficam editáveis mês a mês na planilha. Sem isso a projeção fica chapada e o ROAS não varia. Quando a margem por real de mídia passa de R$ 1, mostre o efeito de subir a verba e sugira degraus: sobe, confere custo por lead e SQLs, e só então sobe de novo.
- Sem a linha `Gross Margin`, a margem vira pergunta obrigatória. Sem a linha `Conexões`, a cadeia segue Leads → MQLs, e isso é dito ao usuário.

**1.3.1 Custo de mídia: sempre a campanha atual.** CPM, CTR de link e clique → lead saem da campanha que está no ar, não de uma média com meses de outro objetivo (multimídia automotiva: agosto, com catálogo e mensagem, tinha CPM de R$ 3,79; o formulário de setembro, R$ 7,43). Use `--fixar cpm=... ctr=... clique_lead=...` e confira contra o mercado, CTR de link só com CTR de link. Pergunte ainda:
- **o CPM sobe com a escala?** O público local satura quando a verba cresce (`--cpm-crescimento g --cpm-crescimento-ate K`, com `--cpm-teto`). Não há benchmark disso: é premissa do usuário e entra assim na aba Premissas. Mostre a faixa (ex.: base em R$ 7,43, R$ 8,00, R$ 8,50, R$ 10) com o mês de payback de cada uma e pare no valor mais duro que ainda fecha.
- **quanto da verba vai para remarketing?** O CPM dessa fatia é maior (cerca de +15%); o ganho de conversão não entra.
- **tem eleição, Black Friday ou data comemorativa no horizonte?** Vão como multiplicadores mês a mês (`--sazonalidade-cpm`). Antes de supor efeito de eleição, olhe o CPM diário da própria conta antes e depois do início do impulsionamento.

**1.4 Margem e take rate.** Confirme a margem de contribuição. Pergunte se a receita registrada já é do cliente (comissão = 1) ou se é GMV sobre o qual ele recebe comissão (ex.: agência de turismo). **Confirme a margem em reais, com uma venda concreta:** "numa venda de R$ 22 mil, quanto sobra para o cliente depois de pagar fornecedor e custos da venda?". Percentual solto é ambíguo. Na EZ, a margem passou por três leituras (15% × 40% = 6%, depois 20% sobre o valor cheio, depois 15% × 20% = 3%), e cada uma trocou o veredito. Só a pergunta em reais fechou a dúvida. Quando a comissão já é a margem, a planilha esconde a linha de margem. Se a margem varia por produto, pergunte de que produto vieram as vendas da V4.

**1.4.1 Horizonte.** Por padrão, a projeção vai do Mês 1 até dezembro do ano corrente (`--horizonte`), sem meses do ano seguinte. Se o acumulado só zera depois de dezembro, ofereça estender a planilha até o mês do payback (no máximo 12 meses). Nesse caso a meta passa a ser esse mês (`--mes-alvo`), mas a rampa mantém o fim combinado (`--rampa-ate`), para os números não mudarem só porque a meta andou. Foi o que o usuário pediu na EZ: "me entrega até o mês que ela breakeva". Se o cliente entrou na V4 num mês específico, esse é o Mês 1 (`--inicio-contrato`), e os meses anteriores ficam como "antes da V4".

**1.4.2 Legado: o que já foi feito.** Pergunte **se o cliente quer o histórico dentro da própria tabela de projeção** ou só a projeção daqui para frente. Com o legado dentro, a tabela vira o acompanhamento de verdade: os meses vividos entram pela coluna Realizado e os seguintes são projeção, numa linha só. Se sim, pergunte **de que mês o legado começa** (`--inicio-contrato`) — lembrando que a tabela tem 12 colunas, então legado longo come o horizonte da projeção, e vale dizer isso ao usuário antes de ele escolher.

**1.4.3 Projeção anterior: o que foi prometido.** Pergunte se **já existe uma projeção anterior** para esse cliente e peça o projetado mês a mês. Com ele, a aba Premissas ganha o bloco **projetado × realizado** (`--legado arquivo.json`), que mostra o atingimento de cada métrica e cada mês. Isso serve a três coisas: calibra a conversa ("a projeção passada entregou 38% do faturamento prometido em janeiro"), explica por que o cliente desconfia de projeção, e impede repetir a promessa. Na indústria de plásticos a projeção anterior pedia 83 vendas por mês contra 23 do melhor mês real — o atingimento de faturamento foi de 5% a 57% em sete dos nove meses. **Se não existir projeção anterior, diga que a comparação não vai existir, em vez de inventar uma linha de base.**

**1.5 Mês-alvo e déficit.** Pergunte em que mês o projeto precisa breakevar. Antes, calcule e informe o acumulado histórico dos meses fechados (faturamento × margem − fee − mídia) e diga se o projeto já breakevou. O usuário decide se o déficit entra na projeção (`--acumulado-inicial`, negativo) ou se ela começa do zero.

**1.5.1 Prazo do cliente e cenário-meta.** Pergunte se existe prazo ("tem que breakevar até dezembro"). Se o plano realista não fecha nesse prazo, não force a premissa: monte um **cenário-meta** ao lado (rampa mais curta, alavancas que estão dentro do mercado e ainda não foram usadas, verba em degraus), diga o que precisa ser verdade em cada mês e entregue como aba extra (`--extra`), com o plano base como compromisso. O gráfico de resultado acumulado passa a mostrar as duas linhas.

**1.5.2 Capacidade da operação.** A projeção define volumes: leads, contatos e vendas por mês. Pergunte quantos leads o time consegue contatar e quantas vendas consegue fechar e instalar por mês. Se o plano pede 900 contatos e 45 vendas e a loja faz 50 contatos, a conversa é de equipe, não de mídia.

**1.6 Período comparável.** Pergunte a partir de que mês fechado o histórico é comparável com a operação atual (mudança de canal, campanha ou oferta). Esse mês vira `--desde`. Sem resposta, o período é todo o histórico fechado. Se só uma etapa mudou no meio da janela (ex.: a campanha trocou e o clique → lead caiu de 19,5% para 7%), mostre as taxas mês a mês, pergunte e fixe essa etapa na taxa da campanha atual (`--fixar clique_lead=0.0615`). O alerta fica na aba Premissas.

**1.6.1 Tráfego orgânico: SEO, social e indicação (inside sales).** Pergunte **de onde** vem o orgânico e **o que é contado na entrada** antes de perguntar o volume — em cliente sem site a entrada não é "visita": pode ser clique no link da bio, conversa iniciada no direct ou indicação. Rode com `--organico-origem "social orgânico" --organico-metrica "cliques no link da bio"`, que trocam os rótulos das linhas e da premissa. Se o projeto inclui SEO, pergunte a curva de visitas orgânicas: quando começa (o primeiro mês costuma ser de preparação) e quantas visitas por mês no fim do horizonte. Sem GA4, a curva é premissa e precisa vir do usuário; mostre antes quanto vale cada visita (conversão × lead → venda × ticket × margem) e quantas visitas fechariam o mês. Rode com `--organico-visitas v1,v2,... --organico-conversao <taxa>`: os leads orgânicos entram somados aos pagos antes de lead → MQL, no piloto e na planilha (linhas de visitas orgânicas editáveis, conversão, leads orgânicos e leads totais). A conversão padrão é a clique → lead atual, a pedido do usuário; avise que um site costuma converter menos que o formulário nativo.

**Atenção à atribuição, não só ao volume.** Se o cliente não mede a origem do lead, a venda vinda do orgânico entra na linha de vendas sem origem e melhora artificialmente o custo por venda da mídia paga. Antes de projetar orgânico, confirme que existe como separar: no site, GA4; no social sem site, alcance orgânico, visitas ao perfil e cliques no link da bio nos insights do Instagram/Facebook, mais a marcação da origem no atendimento. Sem isso, não projete: registre como lacuna de medição e diga o que precisa entrar no Growth Pack. Para mostrar o SEO crescendo, estenda o horizonte para depois de dezembro.

**1.6.2 CRM Marketing: recompra e reativação da base (inside sales).** Se o projeto inclui CRM (WhatsApp, e-mail, reativação, remarketing da base, pós-venda), a projeção separa **[1] novos leads**, **[2] recompra da base** e **[3] reativação**.
- **Pergunte ao usuário:**
  - a base por recência de compra: menos de 6 meses, de 6 a 12 meses, inativos com mais de 12 meses;
  - os clientes recorrentes;
  - os leads sem compra;
  - os contatos com WhatsApp e e-mail;
  - o custo do CRM (entra no fee?) e o ticket da recompra;
  - a cadência: e-mails, reativação e cross-sell por mês.
  Sem os dados da base histórica, use só a base da V4 no Growth Pack e deixe os campos em branco, editáveis.
- **Toda taxa vem de benchmark verificado:** use `referencias/crm_turismo_benchmarks.json` (turismo, conferido em 18/09/2026). Para outro setor, pesquise de novo, abra a página de cada número e registre fonte, benchmark, período, taxa e justificativa. Número sem fonte primária não entra. Quando não houver benchmark do modelo exato, use o segmento mais próximo e escreva que é aproximação.
- **Cada frente atua sobre um grupo sem sobreposição:** WhatsApp para clientes de 6 a 12 meses, cross-sell para clientes com menos de 6 meses, e-mail para leads sem compra, reativação para inativos com mais de 12 meses. Os clientes envelhecem por coorte. A base de leads cresce com os leads novos e perde contatos pelo descadastro.
- **Como rodar:**
  - `--crm crm.json` e, se o fee muda, `--fee-plano` no piloto;
  - `python3 scripts/metodologia_crm.py --crm crm.json --comissao C --margem G --custo-crm X --out metodologia_crm.json`;
  - `--metodologia-extra metodologia_crm.json` no gerador.

  A aba Premissas ganha a análise, a tabela "Premissa | Fonte | Benchmark | Período | Taxa utilizada | Justificativa", os benchmarks descartados e, no fim da aba, as fontes com link.
- **Na resposta, mostre o que o CRM rende e o que custa:** quanto cada contato rende por mês e que base pagaria o custo do CRM. Com margem baixa, o CRM aumenta o faturamento sem pagar o próprio custo (EZ: +31% de GMV em 9 meses, R$ 7 mil de margem contra R$ 24 mil de custo).

**1.6.3 Histórico curto: dados de mercado.** Quando o cliente tem um ou dois meses e poucas vendas, e o usuário precisa de um mês-alvo (multimídia automotiva: "tem que breakevar até dezembro"), as etapas sem histórico suficiente recebem alvo de mercado.
- Pesquise com subagentes e abra cada página; o formato é o de `referencias/multimidia_automotiva_benchmarks.json` (Premissa | Fonte | Benchmark | Período | Taxa utilizada | Justificativa, descartados e fontes com link). Número sem fonte primária não entra; segmento aproximado é dito como aproximação.
- Compare o cliente com o mercado etapa por etapa. Onde ele já está dentro do mercado, a etapa segue o histórico; onde está fora, o alvo da rampa é o benchmark (`--alvo sql_venda=0.283`, `--alvo ticket=2000`). Com a linha Conexões, `--alvo conexao=0.69` sobe lead → MQL na mesma proporção e a planilha mostra a conexão mês a mês.
- **Custo de mídia primeiro.** CPM, CTR e clique → lead partem da campanha atual, não de uma média com meses de outros objetivos (multimídia automotiva: agosto com catálogo e mensagem tinha CPM de R$ 3,79; o formulário de setembro, R$ 7,43, e o custo por lead ia de R$ 10 para R$ 16). Compare CPM e CTR com o mercado do Brasil, e CTR de link só com CTR de link (os benchmarks de 1,7% a 2,6% contam todos os cliques). Nunca suponha CPM mais barato ao escalar a verba; mostre o estresse com CPM maior.
- **Sazonalidade só com dado do produto.** Meça a demanda do termo exato no Google Trends (pytrends, geo BR, 5 anos: mês contra a média do ano e semana da Black Friday contra as 8 semanas anteriores) e use `--sazonalidade-demanda` e `--sazonalidade-cpm` (multiplicadores mês a mês, editáveis na planilha). multimídia automotiva: central multimídia sobe cerca de 5% na Black Friday; os +90% são de smart TV. Estratégia de Black entra no texto, não como ganho, sem dado primário de conversão.
- **CPM ao longo do ano.** O CPM base pode subir com a saturação do público (`--cpm-crescimento g --cpm-crescimento-ate K`, premissa do usuário, sem benchmark) e recebe multiplicadores mês a mês (`--sazonalidade-cpm`: eleição, datas comemorativas, remarketing). Antes de supor efeito de eleição, olhe o CPM diário da própria conta antes e depois do início do impulsionamento (multimídia automotiva: R$ 2,54 → R$ 2,61, sem efeito). A projeção mostra só a linha "CPM" (o CPM usado no mês); a decomposição em base, multiplicador e CPM usado fica numa tabela da aba Premissas. O usuário não quer métricas de explicação na projeção.
- **Confira todas as taxas, não só as que vão ao mercado.** Etapa por etapa (CPM, CTR de link, clique → lead, contato, MQL → SQL, SQL → venda, ticket, margem) e, no fim, o lead → venda resultante contra o do setor. Somar ganho em todas as etapas passa do realista.
- **Meta mais agressiva que o plano:** quando o usuário pergunta se dá para breakevar antes (multimídia automotiva: acumulado zerado em dezembro), procure o cenário mais defensável (rampa mais curta, alavancas dentro do mercado, verba em degraus), mostre o que precisa ser verdade e o risco de cada condição, e entregue como aba extra (`--extra`) ao lado do plano base, que continua sendo o compromisso.
- Rode o cenário conservador e o médio antes de propor: se nem o médio fecha, diga. Calcule a verba que fecha o mês-alvo em cada combinação (ticket, verba) e pergunte ao usuário qual plano entra na planilha; ticket e verba são decisão do cliente.
- `scripts/metodologia_mercado.py --benchmarks ... --analise analise.json` monta as seções da aba Premissas (análise, tabela, descartados, fontes no fim) para o `--metodologia-extra`.

**1.6.4 Datas comemorativas e ofertas.** Meça a sazonalidade do produto, não do varejo em geral: Google Trends do termo exato (geo BR, 5 anos, mês contra a média do ano e semana da Black Friday contra as 8 anteriores) e IBGE PMC do setor. Entra como `--sazonalidade-demanda`. Ganho de oferta (desconto, brinde, parcelamento) não entra sem dado de conversão: vira estratégia no texto. multimídia automotiva: central multimídia sobe cerca de 5% na Black Friday, e os +90% são de smart TV.

**1.7 Ticket e ciclo de venda (só se necessário).** Se a fonte não tem vendas suficientes, peça o ticket. Se o usuário souber o ciclo de venda, pergunte a fração das vendas que fecha ainda no mês do lead (`--lag`). Sem isso, use 1,0 e registre como premissa; com 1,0 a linha "vendas originadas pelos SQLs do mês" some da aba, porque seria cópia de "vendas fechadas no mês".

**1.7.1 Landing page (inside sales).** Pergunte se a campanha manda o clique para uma página ou usa formulário nativo da plataforma. Com página, o connect rate (cliques → visitas) entra como alavanca: ele vem da linha de visitas da fonte ("Visitas", "Visitas LP", "Visualizações da Página de Destino", "Sessões - Pago") ou, se a fonte não tiver a linha, de `--connect-rate` com a taxa medida no Meta/GA4. Com formulário nativo não há página: a linha não entra e o funil vai do clique direto ao lead. **Não invente connect rate para preencher a linha.**

A etapa só entra quando o connect rate é **mensurável**: a linha tem dado em todos os meses da janela e as visitas não passam dos cliques. Se a linha estiver vazia em algum mês da janela, ou se a página receber tráfego de outra origem (visitas > cliques), o piloto derruba a etapa, volta ao clique → lead e avisa — travar a taxa em 100% encolheria o funil projetado sem ninguém perceber. Quando a fonte já mede, `--connect-rate` é recusado: para sobrescrever a taxa medida use `--fixar connect=VALOR`. Com `--connect-rate` as visitas do histórico são calculadas (cliques × taxa) e aparecem assim rotuladas na aba Premissas, e a coluna Realizado dessas linhas fica em branco, porque o número não foi medido.

## 2. Regras de cálculo (declaradas no cabeçalho de toda saída)

**Taxas e breakeven**
- **Breakeven** = margem de contribuição cobrindo fee + mídia. A definição só muda com o usuário ciente e fica registrada (`--definicao-breakeven`). Quando o critério vira receita cobrindo fee + mídia, a margem entra como 100% no modelo, e a margem real vira linha informativa (`--margem-informativa`).
- **Taxas atuais** = média ponderada por volume do último quarter fechado (3 meses). A janela só muda com pedido explícito (`--janela N`). O mês corrente não entra na janela por conta própria: ele aparece como projeção, com o realizado ao lado. Só entra na janela com pedido explícito (`--incluir-corrente`), marcado como parcial.
- **Etapa com menos de 30 eventos na origem ou 10 no destino** recebe alerta de amostra frágil e é reportada como hipótese.
- **Nenhuma taxa de etapa passa de 100%.** Taxa acima disso significa denominador subcontado na fonte (outro canal, outra plataforma). Ela é travada com alerta e a causa é explicada ao usuário.

**Trava de sanidade: a projeção contra o melhor mês real**
- O piloto calcula o **melhor mês fechado de receita** da fonte e compara com a receita projetada no mês-alvo. Quando a projeção pede **mais de 1,2x** esse mês, sai um alerta com o múltiplo e com a verba dos dois meses, e ele entra no texto do veredito na aba Premissas.
- O teto é de **receita, não de capacidade**: passar dele é legítimo quando a verba subiu, e o alerta diz isso ("com 2,4x a verba daquele mês"). O que ele impede é a promessa silenciosa — pedir o dobro do melhor mês com a mesma verba, que foi exatamente o caso da indústria de plásticos.
- Com menos de quatro meses fechados o alerta avisa que o teto é frágil. Nunca use o alerta para baixar a projeção sozinho: ele obriga a **dizer de onde vem a diferença**.

**Funil**
- **O funil corre só sobre o tráfego pago.** As taxas do piloto são do pago. Aplicá-las ao total do site (ou às visitas orgânicas da landing page) infla a receita atribuída à V4. Sessões ou visitas não pagas aparecem só como contexto.
- **Connect rate (cliques → visitas/sessões):** só entra quando existe. E-commerce: com GA4, medido na janela (sessões Google ÷ cliques do Google Ads); sem GA4, informado (`--connect-rate`, tipicamente 85% a 90%) e registrado. Inside sales: medido pela linha de visitas da fonte ou informado com `--connect-rate`; sem nenhum dos dois, a etapa não existe e o funil vai do clique ao lead.
- **Sessões não pagas** vêm do GA4 ou da linha da fonte, nunca zeradas por conveniência. A base projetada é a média dos meses fechados.

**Cenários**
- Sempre dois. O **cenário base** mantém as taxas atuais constantes: é a linha de base, nunca o plano.
- A **rampa** leva cada alavanca, linearmente até o mês-alvo, do nível atual até a **mediana do período comparável**, nunca piorando nenhuma. A mediana é o alvo porque o melhor mês estica a projeção quando a base é pequena.
- O **mês de referência** (o mês fechado com mais vendas por real de mídia) é citado como evidência de que o nível já foi atingido. Ele nunca é um mês parcial.
- A rampa entregue no template usa alpha 1. Ir além da mediana só como cenário pedido explicitamente.

**Meses vividos**
- Não recebem projeção. A linha de resultado consolidado usa o **realizado onde existe** e o projetado à frente, e alimenta KPIs, payback e gráficos. O piloto faz o mesmo no veredito: o resultado dos meses vividos (a partir do mês corrente, ou de `--inicio` quando o Mês 1 é o início do contrato) entra pelo realizado, para o status, o payback e as datas baterem com a planilha.
- Linha calculada não tem coluna Realizado: o par Projetado | Realizado (e o de totais) é mesclado numa célula só. Só tem coluna Realizado quem é campo de digitação.

## 3. Veredito de realismo

Rode o piloto com as premissas confirmadas:

`python3 scripts/breakeven_pilot.py projetar --fonte ... --aba ... --modelo ... --fee F --midia M --margem G --comissao C --mes-alvo K --horizonte H [--crescimento-midia X --midia-teto T] [--desde mês/ano] [--incluir-corrente --janela N] [--acumulado-inicial D] [--lag L] [--ticket T] [--fixar alavanca=valor] [--ga4 ga4.json] [--definicao-breakeven "..."] --out premissas.json`

O veredito vem na resposta, antes do template, e sempre traz **duas datas**, mesmo quando caem depois de dezembro:
- **no azul a partir de:** o mês a partir do qual todo mês fecha com resultado ≥ 0 (o breakeven do mês, sustentado);
- **acumulado zera em:** o payback, contando o déficit inicial.

As duas consideram o realizado dos meses já vividos e a projeção à frente, estendida por 48 meses (`resultados_48m` no premissas.json). O gerador põe essas datas no subtítulo, no cartão "No azul a partir de" e na Metodologia. Nunca entregue só "irrealista".

- **REALISTA:** o payback com as taxas atuais cai no mês-alvo ou antes.
- **REALISTA COM RAMPA:** a meta só fecha percorrendo uma fração (`alpha` ≤ 100%) do caminho até a mediana. Diga qual fração.
- **IRREALISTA:** a meta exigiria ir além da mediana. O template recebe a rampa completa, e o veredito diz em que mês o breakeven acontece de fato (ou que não acontece no horizonte) e qual alavanca tem mais folga.

Cite o mês de referência e por que ele foi escolhido. Escreva em primeira pessoa, como analista, sem suavizar.

**Quando a meta não fecha, mostre o caminho.** O piloto grava `caminho` no premissas.json: o valor de cada alavanca, sozinha, que faz o mês-alvo fechar no zero, comparado com o melhor mês fechado; o fee que fecharia; a margem por real de mídia e a verba que cobriria o fee; e o primeiro mês positivo sem teto de verba. Traga isso em tabela na resposta, antes do template. Comece pela conta da estrutura: quantas vendas o fee exige contra quantas o cliente faz. Se a margem por real de mídia está perto de R$ 1, diga que mais verba não resolve e que a conversa é de estrutura (fee ou remuneração).

**Compare a projeção com o ritmo atual.** A rampa por alavanca pode juntar o melhor de meses diferentes. Se os leads ou SQLs projetados para o mês corrente ficam muito acima do ritmo real, diga que a projeção é otimista no topo do funil.

## 4. Preenchimento do template

Rode:

`python3 scripts/gerar_template.py --premissas premissas.json --modelo <modelo> --cliente "<nome>" --cenario Realista --out <Cliente>_projecao_<modelo>.xlsx [--inicio-contrato mês/ano] [--faturamento-total "mês/ano=valor,..."] [--margem-informativa 0.05] [--sem-etapa-venda] [--obs "..."]`

O atalho chama `gerador/build_workbook.py`, que lê o `premissas.json` como fonte única. Guarde a execução de cada cliente em `projecao-template/clientes/<cliente>/` (premissas.json, ga4.json e o xlsx), fora da skill, e copie o xlsx para `~/Downloads`.

**Modelo padrão de dados (não fuja dele).** A aba de projeção mostra a cadeia padrão do modelo e, em cada linha, **o valor usado no mês**. Premissa que varia (CPM com saturação, multiplicador de eleição, datas e remarketing, sazonalidade de demanda) não vira linha na projeção: ela já está embutida no valor usado, e a decomposição (base, multiplicador, valor usado) vai para a aba Premissas, em tabela mês a mês. O efeito continua em cascata; o que muda é onde o cliente lê a explicação. Linha nova na projeção só quando o cliente precisa editar o número mês a mês (verba, taxas da rampa, ticket).

**Aba do cliente, nesta ordem:** premissas, resultado executivo, meta de breakeven, projeção mês a mês (Projetado | Realizado) e, por último, os gráficos.
- Gráficos: receita da mídia com crescimento mês a mês (barras e linha, como o Power BI do cliente), resultado acumulado, curva de payback, participação da mídia no faturamento (quando houver `--faturamento-total`) e funil.
- Nada de bloco de instruções na aba do cliente, nem azul em célula alguma. Amarelo é editável e vermelho-claro é realizado.
- Comissão, GMV e margem só aparecem para cliente que tem esses elementos. Com receita própria (comissão 1, sem CRM), a linha de faturamento é vendas × ticket e as linhas de comissão e "receita da agência" saem.

**Aba Premissas (`Premissas · <aba>`, a segunda aba):** veredito, caminho para o breakeven (quando a meta não fecha), fonte e janela (incluindo a propriedade GA4 e a data da extração), curva da projeção, alertas, premissas assumidas pelo gerador, observações, histórico com o mês de referência, envelope com o alvo da rampa e cenário base em valores. Gráficos, KPIs e o realizado leem uma aba de apoio oculta (`_apoio_<aba>`).

**O que o gerador faz**
- Células amarelas recebem fee, verba, margem, comissão e, mês a mês, as taxas e o ticket da rampa. Células brancas mantêm fórmulas vivas, nunca valores colados.
- O bloco "Meta de breakeven" calcula por fórmula as vendas necessárias, as projetadas e o gap. A coluna PILOTO ao lado traz os mesmos números do piloto, para conferência.
- Os rótulos acompanham o número de meses; nada de "12 MESES" fixo.

**Mapeamento das cadeias**
- **Inside sales:** com landing page medida, o funil é clique → visita (connect rate) → lead; sem ela (formulário nativo ou fonte sem a linha de visitas), começa em clique → lead. **As linhas de Leads conectados e MQLs conectados aparecem sempre** (o usuário acompanha essa visão). Com "Conexões" na fonte, conexão MQL é 100% e Lead → MQL = (Leads → Conexões) × (Conexões → MQLs). Se a linha Conexões conta só leads conectados e o cliente não mede MQL conectado (multimídia automotiva), use `--conexao-so-lead` no gerador: a conexão lead vem da fonte e a de MQL fica em branco para preencher. Sem ela, **nenhuma taxa é inventada**: a conexão de lead e a de MQL ficam em branco (amarelo, para preencher quando o cliente medir), as linhas de conectados ficam informativas, o realizado fica aberto e o funil segue MQL → SQL sem mudar a projeção. A demo (turismo do painel antigo) mantém todas as linhas.
- **E-commerce:** o template tem View Item e Pedido → Venda. O gerador usa 100% nas duas, porque o GA4 conta view item em eventos. O ticket faturado é igual ao do piloto, a verba cresce pelo percentual e pelo teto, e a comissão multiplica a margem quando é diferente de 1.
- **Com GA4** (`split` no premissas.json), a aba de e-commerce ganha os blocos "Tráfego pago · Google", "Tráfego pago · Meta" e "Sessões do site", mais a participação do Meta na verba como premissa editável.

**Como a aba se lê (v7.1).** A projeção é dividida em blocos com cor própria e tarja vertical na coluna A: **investimento** (cinza), **marketing** (vermelho V4, da verba ao lead), **vendas** (âmbar, do lead à receita), **financeiro** (verde) e **resultado** (preto). Todo rótulo começa pela unidade — `[R$]`, `[%]`, `[QNTD]` ou `[X]` — e a linha inteira de uma alavanca (rótulo, meses e total) fica pintada na cor da alavanca, para o cliente saber de relance o que pode mexer.

**Quem vira SQL é quem foi conectado.** A oportunidade nasce de alguém ter falado com a pessoa, não de ela ter sido marcada MQL. Com a linha `Conexões` na fonte, a cadeia é **lead → conexão → SQL → venda**, e a conexão é uma linha só (`CONEXÃO (LEAD OU MQL)`): todo MQL já é um lead, então separar as duas contaria a mesma pessoa duas vezes — e a conexão vale para os dois, lead e MQL. Sem a linha `Conexões` não há conexão medida e o funil volta a lead → MQL → SQL. **A conexão se mede sobre os leads, não sobre os MQLs.** Parece natural encadear lead → MQL → conexão, mas o time conecta lead que nunca virou MQL, então conexões costumam passar do número de MQLs e a taxa fica impossível: na multimídia automotiva, agosto teve 23 MQLs e 86 conexões (374%). Antes de aceitar `MQL → conexão`, divida conexões por MQLs em cada mês do histórico; se passar de 100% em algum, a conexão é sobre o lead. Checagem no sentido contrário: compare MQLs com conexões no mesmo mês — setembro teve 46 MQLs e 9 conexões, e o modelo antigo gerava SQL a partir dos 46.

**Onde termina o marketing.** O **MQL é qualificação de marketing**: o lead é qualificado por critérios do formulário, da landing page ou de onde quer que ele se inscreva — não pelo julgamento do vendedor. Então `lead → MQL` fecha o bloco de marketing ("MARKETING · DA VERBA AO MQL"), e o bloco de vendas começa no atendimento ("VENDAS · DO ATENDIMENTO À RECEITA"): conexão do lead, conexão do MQL, MQL → SQL, SQL → venda. Isso muda de quem é cada alavanca na hora de falar do caminho para o breakeven: mexer em `lead → MQL` é mexer em critério de formulário, segmentação e oferta do anúncio; mexer em `conexão` e `conexão → SQL` é mexer no time comercial. O MQL fica no marketing como qualidade do lead, fora da conta do funil.

**Um bloco financeiro só.** Nunca mostre a mesma métrica em duas versões (projetada e consolidada) na mesma aba: em mês já vivido a projetada é ficção e o cliente não tem como saber qual ler. O bloco financeiro é único, dividido em três grupos — resultado · quanto falta para zerar o mês · eficiência e retorno — e toda linha corre sobre o consolidado (realizado onde existe, projetado à frente). Linhas que só existem para alimentar fórmula ou cartão (intermediárias, flags `1 = SIM`) ficam ocultas via `hidden_rows`, não visíveis.

**Retorno em múltiplo, não em percentual.** ROI do mês, ROI da mídia e ROI do projeto saem como `[X]` (MC ÷ custo), em que **1,00x significa que o período se pagou**; abaixo de 1,00x fica vermelho, a partir de 1,00x fica verde. Percentual de retorno confunde com taxa de conversão e foi tirado da aba.

**Receita necessária para zerar o mês.** Três linhas no bloco financeiro: quanto de receita zera o custo daquele mês, quantas vendas isso significa no valor médio por venda do mês, e a sobra/falta contra o realizado-onde-existe. As três correm sobre as linhas consolidadas (`custo_cons × receita_cons ÷ mc_cons`), então valem igual para cliente de receita própria, de comissão e com CRM, e usam o realizado nos meses já vividos. A identidade que deve valer sempre: **sobra/falta × margem = resultado líquido do mês**. É o "0 a 0 do mês", sem arrastar o déficit acumulado — esse continua no bloco de meta de breakeven.

**Cenários em abas.** `--extra "premissas.json|Nome da aba|Nome do cenário|metodologia.json"` (repetível) põe cada cenário numa aba de projeção do mesmo arquivo, com a própria aba de premissas. O gráfico "Resultado acumulado mês a mês" de todas as abas mostra as linhas de todos os cenários, para comparar o payback.

Entregue o arquivo e, no chat, o veredito com os números-chave: payback, resultado acumulado, ROAS projetado contra o realizado da janela, e vendas necessárias contra projetadas.

## 5. Validação antes de entregar

Em toda planilha de cliente, recalcule as fórmulas (pycel) e confira:
1. A receita projetada no template é igual à do piloto, mês a mês.
2. Nenhuma taxa de etapa passa de 100%, no projetado nem no realizado.
3. Os meses realizados batem com a fonte.
4. Nenhuma fórmula tem erro e nenhuma célula é azul.
5. O ROAS projetado não se afasta muito do realizado da janela. Se se afastar, procure mistura de plataformas ou tráfego não pago no funil.

Depois de qualquer mudança em `scripts/` ou `gerador/`, rode `python3 tests/regressao.py`. Ele cobre inside sales, e-commerce com e sem GA4 e a demo. Registre a mudança no `CHANGELOG.md` e faça o commit no repositório da skill.

Dependências: `python3` com `pandas`, `openpyxl` e `pycel` (`python3 -m pip install --user pandas openpyxl pycel`). O GA4 precisa do `analytics-mcp` com credencial ADC.

## 6. O que a skill nunca faz

- Não projeta sem fee e verba confirmados pelo usuário.
- Não usa o mês corrente parcial como histórico sem pedido explícito, nem como mês de referência.
- Não leva taxa além da mediana do período por conta própria. Alvo de mercado só com benchmark verificado e com o usuário ciente (`--alvo`).
- Não passa tráfego não pago pelo funil pago.
- Não deixa taxa acima de 100% sem explicar a causa.
- Não deixa bloco de instruções na aba do cliente, nem usa azul.
- Não entrega veredito sem o mês em que o breakeven fica realista.
- Não troca a definição de breakeven sem avisar.
- Não preenche o template antes de mostrar o veredito.
