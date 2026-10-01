---
name: projecao-breakeven
description: Projeção de breakeven de mídia paga a partir do histórico do cliente (planilha padrão V4, CRM, export de mídia e GA4). Use sempre que o usuário pedir projeção de breakeven, payback de mídia, "em que mês o projeto se paga", ou enviar a planilha de indicadores de um cliente querendo saber se a meta de breakeven é realista. Conduz a entrevista (fonte, modelo, fee, mídia, mês-alvo), calcula as taxas efetivas, dá o veredito de realismo e preenche o template (inside sales, e-commerce ou PLG — SaaS de assinatura com trial) sozinha.
---

# Projeção de breakeven

**Versão 8.3 (01/10/2026).** O histórico está em `CHANGELOG.md`. Os caminhos abaixo são relativos à pasta da skill (`.claude/skills/projecao-breakeven/`).

A skill tem duas metades. A primeira é a entrevista: ela **conduz**, e não espera o usuário lembrar o que precisa informar. A segunda é a execução automática: com as premissas confirmadas, ela roda o piloto, dá o veredito e preenche o template, sem etapa manual.

**Antes de começar, leia a referência do modelo:** `referencias/ecommerce.md`, `referencias/inside_sales.md` ou `referencias/plg.md`. Elas trazem as armadilhas das planilhas reais e os casos que servem para calibrar se o resultado faz sentido.

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

**1.2 Modelo.** Pergunte qual template preencher: `inside_sales` (lead → conexão → MQL → SQL → venda), `ecommerce` (clique → sessão → carrinho → checkout → pedido) ou `plg` (cadastro → trial → ativação → assinatura, com receita recorrente). Se a fonte só tem as linhas de um dos três, sugira esse e peça confirmação. **Se a receita é assinatura (mensalidade, plano, trial), o modelo é `plg`**, mesmo que a planilha do cliente esteja montada como inside sales: ele exige `--churn`, lê a mensalidade da linha da fonte e mostra cadastro, trial, ativação e assinatura na aba. Ativação sem medição fica neutra e rotulada como não medida. Detalhes em `referencias/plg.md`.

**1.3 Fee e mídia.** Rode `python3 scripts/breakeven_pilot.py detectar --fonte <arquivo ou URL> --aba Indicadores --modelo <modelo>` e apresente o que foi lido: meses fechados, mês corrente, fee, mídia planejada, mídia realizada média e margem.
- **Peça confirmação explícita do fee e da verba mensal**, mesmo que tenham sido detectados. O usuário pode corrigir (renegociação de fee, plano de mídia novo). Nunca projete com valores não confirmados. Se o fee do contrato diverge da linha Fee V4 da fonte (EZ: R$ 6.901 no contrato, R$ 9.000 no Growth Pack), use `--fee-historico` para aplicar o fee certo também no déficit e no realizado, e avise que a fonte precisa ser corrigida.
- Pergunte o plano de verba. Pode ser crescimento mensal com teto (`--crescimento-midia`, `--midia-teto`) ou degraus mês a mês (`--verba-plano 2000,4000,5000,5000`), que ficam editáveis mês a mês na planilha. Sem isso a projeção fica chapada e o ROAS não varia. Quando a margem por real de mídia passa de R$ 1, mostre o efeito de subir a verba e sugira degraus: sobe, confere custo por lead e SQLs, e só então sobe de novo.
- Sem a linha `Gross Margin`, a margem vira pergunta obrigatória. Sem a linha `Conexões`, a cadeia segue Leads → MQLs, e isso é dito ao usuário.

**1.3.1 Custo de mídia: sempre a campanha atual.** CPM, CTR de link e clique → lead saem da campanha que está no ar, não de uma média com meses de outro objetivo (multimídia automotiva: agosto, com catálogo e mensagem, tinha CPM de R$ 3,79; o formulário de setembro, R$ 7,43). Use `--fixar cpm=... ctr=... clique_lead=...` e confira contra o mercado, CTR de link só com CTR de link. Pergunte ainda:
- **o CPM sobe com a escala?** O público local satura quando a verba cresce (`--cpm-crescimento g --cpm-crescimento-ate K`, com `--cpm-teto`). Não há benchmark disso: é premissa do usuário e entra assim na aba Premissas. Mostre a faixa (ex.: base em R$ 7,43, R$ 8,00, R$ 8,50, R$ 10) com o mês de payback de cada uma e pare no valor mais duro que ainda fecha.
- **quanto da verba vai para remarketing?** O CPM dessa fatia é maior (cerca de +15%); o ganho de conversão não entra.
- **tem eleição, Black Friday ou data comemorativa no horizonte?** Vão como multiplicadores mês a mês (`--sazonalidade-cpm`). Antes de supor efeito de eleição, olhe o CPM diário da própria conta antes e depois do início do impulsionamento.

**1.4 Margem e take rate.** Confirme a margem de contribuição. Pergunte se a receita registrada já é do cliente (comissão = 1) ou se é GMV sobre o qual ele recebe comissão (ex.: agência de turismo). **Confirme a margem em reais, com uma venda concreta:** "numa venda de R$ 22 mil, quanto sobra para o cliente depois de pagar fornecedor e custos da venda?". Percentual solto é ambíguo. Na EZ, a margem passou por três leituras (15% × 40% = 6%, depois 20% sobre o valor cheio, depois 15% × 20% = 3%), e cada uma trocou o veredito. Só a pergunta em reais fechou a dúvida. Quando a comissão já é a margem, a planilha esconde a linha de margem. Se a margem varia por produto, pergunte de que produto vieram as vendas da V4.

**1.4.1 Horizonte.** Por padrão, a projeção vai do Mês 1 até dezembro do ano corrente (`--horizonte`), sem meses do ano seguinte. Se o acumulado só zera depois de dezembro, ofereça estender a planilha até o mês do payback. O template aceita de 1 a 18 meses: até 12 é o padrão, e de 13 a 18 quando a pergunta do usuário é o mês em que o caixa vira (SaaS de diário de obra: mês no azul só no M14). Nesse caso use `--rampa-ate` para a rampa terminar onde foi combinado, em vez de esticar com o horizonte. Nesse caso a meta passa a ser esse mês (`--mes-alvo`), mas a rampa mantém o fim combinado (`--rampa-ate`), para os números não mudarem só porque a meta andou. Foi o que o usuário pediu na EZ: "me entrega até o mês que ela breakeva". Se o cliente entrou na V4 num mês específico, esse é o Mês 1 (`--inicio-contrato`), e os meses anteriores ficam como "antes da V4".

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

**1.6.4 Sazonalidade: primeiro o histórico do próprio cliente.** Pergunte se existe o **faturamento total mensal** do cliente (ERP, DRE, a linha "Total de Faturamento" do Growth Pack) com 12 meses ou mais. Se existir, ele manda: `--sazonalidade-historico` (sem valor, procura a linha de faturamento total da fonte; ou o rótulo de outra linha; ou um CSV `mês/ano,valor`). Cada mês é comparado com a média dos meses ao redor (±6), o que tira a tendência de crescimento, e a média por mês do calendário vira o índice (média do ano = 1,00), aplicado às vendas mês a mês e mostrado em tabela na aba Premissas. Use o faturamento **total**, não o da V4, que carrega a rampa da operação. Sem 12 meses, o piloto avisa e segue sem sazonalidade — aí vale o Google Trends abaixo. Na indústria de plásticos (indústria com mês forte e mês fraco), projetar sem o sazonal do cliente fazia a projeção errar mês a mês mesmo com a média certa.

**Datas comemorativas e ofertas, sem histórico do cliente.** Meça a sazonalidade do produto, não do varejo em geral: Google Trends do termo exato (geo BR, 5 anos, mês contra a média do ano e semana da Black Friday contra as 8 anteriores) e IBGE PMC do setor. Entra como `--sazonalidade-demanda`. Ganho de oferta (desconto, brinde, parcelamento) não entra sem dado de conversão: vira estratégia no texto. multimídia automotiva: central multimídia sobe cerca de 5% na Black Friday, e os +90% são de smart TV.

**1.6.5 Assinatura (SaaS) e PLG.** Se a receita é **recorrente** (mensalidade, plano, assinatura), o modelo transacional
não serve: `vendas × ticket` cobra o cliente uma vez e esquece que ele paga de novo no mês seguinte. Rode com
`--recorrencia --churn <taxa ou plano> [--base-inicial N]`: as vendas do funil viram **assinaturas novas**, a base
acumula (`base_t = base_(t-1) × (1 − churn_t) + novas_t`) e a receita do mês é **base × mensalidade**. Pergunte:
- **a mensalidade e o plano** — qual plano as vendas reais fecharam, mensal ou anual. Não use o plano de cima como ticket
  só porque ele existe: na SaaS de diário de obra a planilha do cliente usava R$ 350 e as duas vendas reais foram R$ 169.
- **o churn mensal**, e **de onde ele vem**. Quase nunca é medido. Sem medição, use a faixa do segmento por ACV
  (SMB abaixo de US$ 1k de ACV roda 6% a 10% ao mês) e escreva que é aproximação. Churn abaixo da faixa precisa de prova.
- **a base já ativa** no Mês 1 (`--base-inicial`), contando só o que é atribuível à V4.
- **quantos assinantes ativos o fee exige.** Divida fee + verba pela MC de um assinante: é a conta de estrutura da
  assinatura, e ela costuma dar o veredito antes de qualquer taxa.

**Entregue as duas leituras, e diga o que cada uma responde.** Com `--recorrencia` a aba ganha, além do bloco
financeiro de caixa, o bloco **VALOR DE VIDA (LTV)**. O de caixa conta só o que entra dentro das colunas da planilha
e corta cada safra na borda do calendário — quem assina no último mês aparece com um mês de receita. O de LTV credita
cada assinatura nova pelo que ela vale até cancelar. **Em assinatura, a de LTV é a que diz se vale a pena adquirir;
a de caixa é a que diz quanto o contrato consome no caminho.** As duas podem discordar de sinal e as duas são verdade:
na SaaS de diário de obra, com margem de 30%, o caixa de 12 meses deu −R$ 108,8 mil e o valor de vida +R$ 142,8 mil. Nunca entregue
só uma.

**O payback sai nas duas réguas, e o subtítulo mostra as duas.** Não basta ter a linha de LTV na tabela: se as datas
de payback lerem só caixa, a planilha dá a resposta certa num lugar e a errada no outro. As duas partem do mesmo
déficit histórico e os meses já vividos entram pela MC e pelo custo realizados. Na SaaS de diário de obra deu onze meses de diferença.

**Leia a economia unitária, não só o payback de calendário.** O veredito ganha o bloco `recorrencia` com lifetime, LTV,
CAC cheio e de mídia, LTV/CAC e payback de CAC. **Com LTV/CAC abaixo de 1, mais verba aumenta o prejuízo por cliente**,
e a conversa é de preço, churn ou conversão — não de mídia. Acima de 1, a verba é o acelerador e aí os degraus valem.

**PLG não é o funil linear.** Em produto self-serve o trial converte sozinho e a demonstração é exceção, não etapa
obrigatória. Antes de mapear, olhe a **porta de entrada declarada** pelo lead: na SaaS de diário de obra, 37% pediam compra direta,
sem trial e sem demo, estável nos três meses. Cobrar trial e demo de quem já queria comprar inventa etapa no caminho de
quem estava com o cartão na mão. E **ativação é momento de produto** (primeiro uso de verdade), dentro do trial e antes
de qualquer humano — não uma etapa depois da demo.

**1.6.6 Conexão quando o time atende depois da qualificação.** A linha `Conexões` da planilha padrão entra **antes do
MQL**. Em cliente cujo MQL sai do formulário e o atendimento vem depois (SaaS com trial, por exemplo), ela ficaria no
lugar errado. **Teste antes de encaixar: divida conexões por MQLs em cada mês do histórico.** Passou de 100%, a conexão
é sobre o lead e vem antes (multimídia automotiva). Ficou abaixo com folga, ela vem **depois** do MQL — e aí não use a linha da fonte:
meça no painel ou no CRM e informe com `--conexao-lead` e `--conexao-mql` (valor único ou plano mês a mês). Isso não
muda volume, só decompõe `MQL → SQL` em `MQL → MQL conectado → SQL` e deixa as seis linhas de conexão vivas e editáveis.

**1.7 Ticket e ciclo de venda.** Se a fonte não tem vendas suficientes, peça o ticket. **Pergunte sempre o ciclo de venda** — em B2B a venda do lead de hoje cai no mês que vem, e projetar tudo no mês do lead antecipa a receita:
- **Com CRM**, meça: `python3 scripts/ciclo_crm.py --csv negocios.csv --criacao "<coluna>" --fechamento "<coluna>" [--filtro-coluna Status --filtro-valor Ganho]` devolve a curva (quanto fecha em M+0, M+1, M+2, M+3) e o `--ciclo` para o piloto (ex.: `--ciclo 0.45,0.35,0.20`). Com menos de 10 vendas com as duas datas, o script recusa e a curva vira premissa.
- **Sem CRM**, peça o ciclo médio em dias: `--ciclo-dias 45` vira curva (lead em qualquer dia do mês, fechamento D dias depois: 45 dias = 50% em M+1 e 50% em M+2). Registre como premissa.
- `--lag L` continua valendo como atalho de dois meses. Com ciclo de três meses ou mais, a aba ganha uma premissa por mês do ciclo e a linha "vendas fechadas no mês" soma as safras; a seção "Ciclo de vendas" da aba Premissas diz a origem (medido ou premissa).
- Sem ciclo nenhum, a venda fecha no mês do lead e a linha "vendas originadas pelos SQLs do mês" some, porque seria cópia de "vendas fechadas".

**1.7.1 Landing page (inside sales).** Pergunte se a campanha manda o clique para uma página ou usa formulário nativo da plataforma. Com página, o connect rate (cliques → visitas) entra como alavanca: ele vem da linha de visitas da fonte ("Visitas", "Visitas LP", "Visualizações da Página de Destino", "Sessões - Pago") ou, se a fonte não tiver a linha, de `--connect-rate` com a taxa medida no Meta/GA4. Com formulário nativo não há página: a linha não entra e o funil vai do clique direto ao lead. **Não invente connect rate para preencher a linha.**

A etapa só entra quando o connect rate é **mensurável**: a linha tem dado em todos os meses da janela e as visitas não passam dos cliques. Se a linha estiver vazia em algum mês da janela, ou se a página receber tráfego de outra origem (visitas > cliques), o piloto derruba a etapa, volta ao clique → lead e avisa — travar a taxa em 100% encolheria o funil projetado sem ninguém perceber. Quando a fonte já mede, `--connect-rate` é recusado: para sobrescrever a taxa medida use `--fixar connect=VALOR`. Com `--connect-rate` as visitas do histórico são calculadas (cliques × taxa) e aparecem assim rotuladas na aba Premissas, e a coluna Realizado dessas linhas fica em branco, porque o número não foi medido.

## 2. Regras de cálculo (declaradas no cabeçalho de toda saída)

**Dado que falta vira premissa de mercado, não buraco.** Quando o cliente não mede uma etapa (conexão, SQL → venda sem nenhuma venda, ticket sem venda), use `--premissa-mercado CHAVE=VALOR|fonte` com benchmark verificado: entra marcada como premissa de mercado na aba e na aba Premissas, e vira o primeiro item de medição do plano. Nunca use no lugar de dado medido (o piloto recusa); para levar uma taxa medida até o mercado, o caminho é `--alvo`.

**Taxas e breakeven**
- **Breakeven** = margem de contribuição cobrindo fee + mídia. A definição só muda com o usuário ciente e fica registrada (`--definicao-breakeven`). Quando o critério vira receita cobrindo fee + mídia, a margem entra como 100% no modelo, e a margem real vira linha informativa (`--margem-informativa`).
- **Taxas atuais** = média ponderada por volume do último quarter fechado (3 meses). A janela só muda com pedido explícito (`--janela N`). O mês corrente não entra na janela por conta própria: ele aparece como projeção, com o realizado ao lado. Só entra na janela com pedido explícito (`--incluir-corrente`), marcado como parcial.
- **Etapa com menos de 30 eventos na origem ou 10 no destino** recebe alerta de amostra frágil e é reportada como hipótese.
- **Nenhuma taxa de etapa passa de 100%.** Taxa acima disso significa denominador subcontado na fonte (outro canal, outra plataforma). Ela é travada com alerta e a causa é explicada ao usuário.

**Economia unitária: MC1, CAC permitido e as três camadas de breakeven**
- A margem que este documento usa é a **MC1** (margem de contribuição, ou margem pré-CAC): receita líquida menos CMV menos despesas variáveis de venda. Não é lucro líquido, não é lucro bruto. Quando houver DRE, **leia a MC1 dele em vez de aceitar uma estimativa** — e confira o que está dentro do CMV, porque overhead de fábrica mal alocado derruba a MC1 sem que nada tenha piorado de verdade.
- **CAC permitido (allowable CAC) = MC1 × ticket.** É o teto de gasto por venda antes de a transação dar prejuízo. A **folga de aquisição** é o permitido dividido pelo real.
- **Três camadas de breakeven, e elas não se substituem.** Sempre dizer qual está sendo usada:
  1. **Transação** — `ROAS = 1 / MC1`. A mídia se paga, ignorando o fee.
  2. **Contrato** — `ROAS = (fee + verba) / MC1 / verba`. O contrato inteiro se paga. **É esta que a projeção usa.**
  3. **Empresa** — `ROAS = (fee + verba + fixas) / MC1 / verba`. A mídia sozinha tira a empresa do vermelho. Quando esta dá um número absurdo, a conclusão é que **o problema da empresa não é solúvel por mídia** — e isso é um achado, não uma desculpa.
- **MC1 em porcentagem não decide viabilidade; MC1 × ticket decide.** Uma MC1 de 17,8% num ticket de R$ 3.143 dá R$ 559 de CAC permitido; uma de 40% num ticket de R$ 80 dá R$ 32. A de margem menor tem 17x mais espaço. Nunca condenar um canal pela margem percentual sozinha.
- **Nada disso é linear ao longo de um caminho, só num ponto.** Três curvaturas a declarar sempre que alguém usar esses números para decidir verba:
  - o **ROAS exigido cai** conforme a verba sobe, porque o fee dilui — isso é exato, a assíntota é `1/MC1`;
  - o **ROAS entregue cai** conforme a verba sobe, por saturação de público — isso é premissa, e a verba ótima é absurdamente sensível a ela (na indústria de plásticos, de R$ 5 mil a R$ 146 mil conforme o expoente);
  - a **MC1 muda com o ticket** (pedido grande costuma vir com desconto), então o CAC permitido cresce menos que proporcional.
- **Para medir a saturação é preciso variar a verba de propósito.** Histórico com verba estável (a indústria de plásticos variou 1,4x no ano) não permite ajustar a curva, e nenhum modelo substitui o teste. Dizer isso em vez de entregar uma verba ótima falsamente precisa.

**Trava de sanidade: a projeção contra o melhor mês real**
- O piloto calcula o **melhor mês fechado de receita** da fonte e compara com a receita projetada no mês-alvo. Quando a projeção pede **mais de 1,2x** esse mês, sai um alerta com o múltiplo e com a verba dos dois meses, e ele entra no texto do veredito na aba Premissas.
- O teto é de **receita, não de capacidade**: passar dele é legítimo quando a verba subiu, e o alerta diz isso ("com 2,4x a verba daquele mês"). O que ele impede é a promessa silenciosa — pedir o dobro do melhor mês com a mesma verba, que foi exatamente o caso da indústria de plásticos.
- Com menos de quatro meses fechados o alerta avisa que o teto é frágil. Nunca use o alerta para baixar a projeção sozinho: ele obriga a **dizer de onde vem a diferença**.

**Funil**
- **O funil corre só sobre o tráfego pago.** As taxas do piloto são do pago. Aplicá-las ao total do site (ou às visitas orgânicas da landing page) infla a receita atribuída à V4. Sessões ou visitas não pagas aparecem só como contexto.
- **Connect rate (cliques → visitas/sessões):** só entra quando existe. E-commerce: com GA4, medido na janela (sessões Google ÷ cliques do Google Ads); sem GA4, informado (`--connect-rate`, tipicamente 85% a 90%) e registrado. Inside sales: medido pela linha de visitas da fonte ou informado com `--connect-rate`; sem nenhum dos dois, a etapa não existe e o funil vai do clique ao lead.
- **Sessões não pagas** vêm do GA4 ou da linha da fonte, nunca zeradas por conveniência. A base projetada é a média dos meses fechados.

**Cenários: sempre três, cada um numa aba** (`scripts/tres_cenarios.py`)
- **Pessimista** (`--cenario pessimista`): as taxas atuais ficam constantes até o fim, sem rampa. É a linha de base, nunca o plano.
- **Desejado** (padrão): a rampa até a mediana do período comparável. É o plano e o compromisso.
- **Otimista** (`--cenario otimista`): a rampa até o **melhor mês fechado** do período, ou até o benchmark de `--alvo` quando ele é maior. É o teto do que já aconteceu no cliente ou no mercado, nunca uma combinação inventada; alavanca fixada (`--fixar`, `--premissa-mercado`) não muda em nenhum cenário.
- Os três usam o mesmo histórico e as mesmas premissas confirmadas; só o alvo da rampa muda. A planilha sai com as abas Pessimista, Desejado e Otimista, cada uma com a sua aba Premissas, e o gráfico de resultado acumulado de cada aba mostra as três linhas.
- A **rampa** leva cada alavanca, linearmente até o mês-alvo, do nível atual até a **mediana do período comparável**, nunca piorando nenhuma. A mediana é o alvo porque o melhor mês estica a projeção quando a base é pequena.
- O **mês de referência** (o mês fechado com mais vendas por real de mídia) é citado como evidência de que o nível já foi atingido. Ele nunca é um mês parcial.
- A rampa entregue no template usa alpha 1. Ir além da mediana só no cenário otimista ou num cenário pedido explicitamente (`--extra`).

**Meses vividos**
- Não recebem projeção. A linha de resultado consolidado usa o **realizado onde existe** e o projetado à frente, e alimenta KPIs, payback e gráficos. O piloto faz o mesmo no veredito: o resultado dos meses vividos (a partir do mês corrente, ou de `--inicio` quando o Mês 1 é o início do contrato) entra pelo realizado, para o status, o payback e as datas baterem com a planilha.
- Linha calculada não tem coluna Realizado: o par Projetado | Realizado (e o de totais) é mesclado numa célula só. Só tem coluna Realizado quem é campo de digitação.

## 3. Veredito de realismo

Rode o piloto com as premissas confirmadas:

`python3 scripts/breakeven_pilot.py projetar --fonte ... --aba ... --modelo ... --fee F --midia M --margem G --comissao C --mes-alvo K --horizonte H [--crescimento-midia X --midia-teto T] [--desde mês/ano] [--incluir-corrente --janela N] [--acumulado-inicial D] [--ciclo 0.5,0.3,0.2 | --ciclo-dias N | --lag L] [--cenario pessimista|desejado|otimista] [--sazonalidade-historico] [--premissa-mercado chave=valor|fonte] [--ticket T] [--fixar alavanca=valor] [--ga4 ga4.json] [--definicao-breakeven "..."] --out premissas.json`

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
- **Inside sales:** com landing page medida, o funil é clique → visita (connect rate) → lead; sem ela (formulário nativo ou fonte sem a linha de visitas), começa em clique → lead. **As linhas de Leads conectados e MQLs conectados aparecem sempre** (o usuário acompanha essa visão). Com "Conexões" na fonte, conexão MQL é 100% e Lead → MQL = (Leads → Conexões) × (Conexões → MQLs). Se a linha Conexões conta só leads conectados e o cliente não mede MQL conectado (multimídia automotiva), use `--conexao-so-lead` no gerador: a conexão lead vem da fonte e a de MQL fica em branco para preencher. Sem ela, **a conexão entra como premissa de mercado, não em branco** (regra nova da v8.1, a partir da indústria de plásticos): `--premissa-mercado conexao_lead=0.69|<fonte>` e `--premissa-mercado conexao_mql=0.80|<fonte>`, com o benchmark verificado (a mesma regra de fonte primária da seção 1.6.3). A linha ganha o rótulo "(PREMISSA DE MERCADO)", a aba Premissas lista o número e a fonte, e o funil não muda de volume: a conexão decompõe MQL → SQL em MQL → MQL conectado → SQL. Se o benchmark de conexão MQL for menor que a própria MQL → SQL do cliente, o piloto recusa (a etapa seguinte passaria de 100%). Sem benchmark verificado, aí sim a célula fica em branco. A demo (turismo do painel antigo) mantém todas as linhas.
- **E-commerce:** o template tem View Item e Pedido → Venda. View item fica em 100%, porque o GA4 conta view item em eventos. **Pedido captado → faturado é alavanca quando a fonte traz a linha "Pedidos Faturados"** (ou "Vendas Faturadas"): a taxa é medida, entra na rampa como as demais e a receita que paga a operação passa a ser a **faturada** ("Receita Faturada" da fonte, ou estimada pelo ticket do pedido captado, com aviso). Pergunte ao cliente quanto do pedido captado vira faturado (cancelamento, fraude, boleto não pago) quando a fonte não separa. Sem a linha, pedido → venda fica em 100% como antes. A verba cresce pelo percentual e pelo teto, e a comissão multiplica a margem quando é diferente de 1.
- **Com GA4** (`split` no premissas.json), a aba de e-commerce ganha os blocos "Tráfego pago · Google", "Tráfego pago · Meta" e "Sessões do site", mais a participação do Meta na verba como premissa editável.

**Como a aba se lê (v7.1).** A projeção é dividida em blocos com cor própria e tarja vertical na coluna A: **investimento** (cinza), **marketing** (vermelho V4, da verba ao lead), **vendas** (âmbar, do lead à receita), **financeiro** (verde) e **resultado** (preto). Todo rótulo começa pela unidade — `[R$]`, `[%]`, `[QNTD]` ou `[X]` — e a linha inteira de uma alavanca (rótulo, meses e total) fica pintada na cor da alavanca, para o cliente saber de relance o que pode mexer.

**Quem vira SQL é quem foi conectado.** A oportunidade nasce de alguém ter falado com a pessoa, não de ela ter sido marcada MQL. Com a linha `Conexões` na fonte, a cadeia é **lead → conexão → SQL → venda**, e a conexão é uma linha só (`CONEXÃO (LEAD OU MQL)`): todo MQL já é um lead, então separar as duas contaria a mesma pessoa duas vezes — e a conexão vale para os dois, lead e MQL. Sem a linha `Conexões` não há conexão medida e o funil volta a lead → MQL → SQL. **A conexão se mede sobre os leads, não sobre os MQLs.** Parece natural encadear lead → MQL → conexão, mas o time conecta lead que nunca virou MQL, então conexões costumam passar do número de MQLs e a taxa fica impossível: na multimídia automotiva, agosto teve 23 MQLs e 86 conexões (374%). Antes de aceitar `MQL → conexão`, divida conexões por MQLs em cada mês do histórico; se passar de 100% em algum, a conexão é sobre o lead. Checagem no sentido contrário: compare MQLs com conexões no mesmo mês — setembro teve 46 MQLs e 9 conexões, e o modelo antigo gerava SQL a partir dos 46.

**Onde termina o marketing.** O **MQL é qualificação de marketing**: o lead é qualificado por critérios do formulário, da landing page ou de onde quer que ele se inscreva — não pelo julgamento do vendedor. Então `lead → MQL` fecha o bloco de marketing ("MARKETING · DA VERBA AO MQL"), e o bloco de vendas começa no atendimento ("VENDAS · DO ATENDIMENTO À RECEITA"): conexão do lead, conexão do MQL, MQL → SQL, SQL → venda. Isso muda de quem é cada alavanca na hora de falar do caminho para o breakeven: mexer em `lead → MQL` é mexer em critério de formulário, segmentação e oferta do anúncio; mexer em `conexão` e `conexão → SQL` é mexer no time comercial. O MQL fica no marketing como qualidade do lead, fora da conta do funil.

**Um bloco financeiro só.** Nunca mostre a mesma métrica em duas versões (projetada e consolidada) na mesma aba: em mês já vivido a projetada é ficção e o cliente não tem como saber qual ler. O bloco financeiro é único, dividido em três grupos — resultado · quanto falta para zerar o mês · eficiência e retorno — e toda linha corre sobre o consolidado (realizado onde existe, projetado à frente). Linhas que só existem para alimentar fórmula ou cartão (intermediárias, flags `1 = SIM`) ficam ocultas via `hidden_rows`, não visíveis.

**Retorno em múltiplo, não em percentual.** ROI do mês, ROI da mídia e ROI do projeto saem como `[X]` (MC ÷ custo), em que **1,00x significa que o período se pagou**; abaixo de 1,00x fica vermelho, a partir de 1,00x fica verde. Percentual de retorno confunde com taxa de conversão e foi tirado da aba.

**Receita necessária para zerar o mês.** Três linhas no bloco financeiro: quanto de receita zera o custo daquele mês, quantas vendas isso significa no valor médio por venda do mês, e a sobra/falta contra o realizado-onde-existe. As três correm sobre as linhas consolidadas (`custo_cons × receita_cons ÷ mc_cons`), então valem igual para cliente de receita própria, de comissão e com CRM, e usam o realizado nos meses já vividos. A identidade que deve valer sempre: **sobra/falta × margem = resultado líquido do mês**. É o "0 a 0 do mês", sem arrastar o déficit acumulado — esse continua no bloco de meta de breakeven.

**Cenários em abas.** `--extra "premissas.json|Nome da aba|Nome do cenário|metodologia.json"` (repetível) põe cada cenário numa aba de projeção do mesmo arquivo, com a própria aba de premissas. O gráfico "Resultado acumulado mês a mês" de todas as abas mostra as linhas de todos os cenários, para comparar o payback.

**Legado completo.** Toda planilha ganha a aba **Legado completo**: todos os meses da fonte (não só os que cabem na tabela), volumes, taxas mês a mês, resultado e a lista **"O que mudou no caminho"** — fee, verba que mudou mais de 1,5x, mídia parada ou retomada, taxa que saltou 1,5x contra a mediana dos três meses anteriores, meses com mídia e sem funil medido. Leia essa lista antes de escolher a janela e o `--desde`. Para o legado sair inteiro, a fonte precisa trazer os meses desde o início do contrato, mesmo sem funil (indústria química B2B: maio/25 a abril/26 só com fee e mídia). `--sem-legado-completo` tira a aba.

**Cenário Breakeven: sempre, sem o usuário pedir.** Pessimista, desejado e otimista só usam o histórico do cliente e a verba de hoje, e quase nunca fecham. Toda projeção sai também com a aba **Breakeven**, montada sozinha pelo `scripts/cenario_breakeven.py`, que o `tres_cenarios.py` roda em cada leitura (sem e com legado). Ela responde "o que precisa ser verdade para bater", e a busca segue esta ordem:
1. **Funil no nível de mercado onde o cliente está abaixo dele.** Os níveis vêm de `referencias/mercado_alavancas.json`, só com fonte primária; o padrão é `b2b_industria`, e outro setor entra com `--mercado`/`--setor`. A etapa que já está acima do mercado fica onde está. O alvo é o maior entre o mercado e a mediana do próprio cliente, e o ticket vai à mediana do cliente.
2. **Verba em degraus** (+50% da verba atual por mês, no mínimo R$ 500, até 8x): vale o menor teto em que o mês fica no azul e o acumulado zera em até 24 meses depois do último mês vivido; se nenhum zerar, o menor teto em que o mês vira. Verba só ajuda quando a mídia se paga (margem por R$ 1 de mídia acima de 1) — é por isso que o funil vem antes.
3. **Recompra** (inside sales): do menor número de pedidos por cliente para o maior, com verba de 1x a 3x. Usa o motor da assinatura, e o gerador recebe `--vocabulario recompra` sozinho.
4. **Nada fecha:** a aba sai com a melhor tentativa e diz que a conversa é de estrutura (fee, margem, ticket).

A aba traz, no topo da Premissas: o que precisa ser verdade, a tabela "onde o cliente está × mercado × fonte × usado", a sensibilidade à verba (e à recompra, quando entra) e os **riscos sem suavizar** (lead → venda resultante contra o de hoje, trava do melhor mês, CPM constante na escala). A thread de aprovação ganha a seção **"O cenário que bate"**. Nunca entregue uma projeção só com cenários que não fecham: se o usuário precisa perguntar "qual bate?", a skill falhou. fábrica de acessórios de cortina (01/10/2026): clique → lead de 4,3% para 8,2% e MQL → SQL de 20% para 42%, verba até R$ 5 mil, acumulado sem legado zerado em fev/28. indústria química B2B: o funil de mercado não basta e entra recompra de cerca de 6,7 pedidos por cliente.

**Thread de aprovação: sempre com a restrição mapeada até agora.** O `tres_cenarios.py` roda o `scripts/aprovacao.py`, que escreve `aprovacao.md` — texto curto, pronto para colar no Slack ou no ClickUp — e põe o mesmo bloco no topo da aba Premissas de cada cenário. Ele traz o veredito, os três cenários (no azul, acumulado zera, acumulado no fim), **onde está a restrição** e o que ainda não é medido. A restrição segue esta ordem: **estrutura** (nem com fee zero a mídia se paga — nenhuma taxa resolve), **retorno da mídia** abaixo de 1 (mais verba piora), ou **funil** (a alavanca que, sozinha, fecha o mês-alvo com o menor salto, e se esse nível já aconteceu). As lacunas que o usuário conhece (recompra não medida, margem provisória) entram com `--restricao "..."`. Mande o texto da thread junto com a planilha.

**Cenário-meta e recompra B2B.** Quando nenhum dos três fecha, monte o cenário-meta, que mostra o que precisa ser verdade, como aba a mais: `--cenario-extra "Cenário-meta|<argumentos a mais do piloto>|metodologia_meta.json"`, com a explicação item por item e a tabela de sensibilidade no JSON. Em B2B que repõe estoque (químico, insumo), a recompra é a alavanca que decide e quase nunca é medida. Modele com o motor da assinatura (`--recorrencia --churn X`, em que X é a fração de clientes ativos que para de comprar por mês, e `1/X` é o número de pedidos por cliente) e `--vocabulario recompra` no gerador, que troca "assinatura/MRR/churn" por "cliente ativo/receita de recompra/% que para de comprar". Na indústria química B2B, o mês só vira com cerca de 6,7 pedidos por cliente, junto com conversão e ticket melhores. O acumulado só zera com cerca de 9 pedidos.

**Com legado e sem legado, na mesma planilha.** Quando o cliente tem déficit herdado, entregue as duas leituras: `--sem-legado "--horizonte 3 --mes-alvo 3"` no `tres_cenarios.py` monta, **na frente**, os mesmos cenários começando no mês seguinte ao último fechado, com acumulado zero e sem `--inicio` (abas "<Cenário> sem legado"), e depois os com legado ("<Cenário> com legado"), cada aba com o seu Mês 1 (o gerador aceita o 5º campo do `--extra`; o gráfico de acumulado só junta abas do mesmo calendário). O cenário-extra aceita argumentos e metodologia próprios para a leitura sem legado (campos 4 e 5). **Sem legado responde se continuar vale a pena** (o que já foi gasto não volta, qualquer que seja a decisão); **com legado responde se o contrato inteiro se paga**. Na indústria química B2B o meta sem legado zera o acumulado em dez/29; com legado, não zera em 48 meses.

Rodar tudo de uma vez:

`python3 scripts/tres_cenarios.py --cliente "<nome>" --out <Cliente>_cenarios.xlsx --piloto "<argumentos do projetar, sem --out>" --gerador "<argumentos do gerador, sem --premissas/--out>" [--restricao "..."]`

Entregue o arquivo e, no chat, o veredito com os números-chave: payback, resultado acumulado, ROAS projetado contra o realizado da janela, e vendas necessárias contra projetadas — e o texto da thread de aprovação.

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
- Não leva taxa além da mediana do período por conta própria, fora do cenário otimista. Alvo de mercado só com benchmark verificado e com o usuário ciente (`--alvo`).
- Não deixa etapa sem dado em branco quando existe benchmark verificado (`--premissa-mercado`), nem usa benchmark no lugar de dado medido.
- Não entrega sem os três cenários, sem o cenário Breakeven (o que bate) e sem o texto da thread de aprovação com a restrição mapeada.
- Não passa tráfego não pago pelo funil pago.
- Não deixa taxa acima de 100% sem explicar a causa.
- Não deixa bloco de instruções na aba do cliente, nem usa azul.
- Não entrega veredito sem o mês em que o breakeven fica realista.
- Não troca a definição de breakeven sem avisar.
- Não preenche o template antes de mostrar o veredito.
