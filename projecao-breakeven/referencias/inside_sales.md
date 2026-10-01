# Inside sales: aprendizados e armadilhas

Ler antes de projetar qualquer cliente de inside sales. Os casos de referência são consultoria B2B, revestimentos e turismo (setembro de 2026).

## 1. A planilha de indicadores (Growth Pack)

- **Rótulos variam por cliente.** MQLs, SQLs, Vendas e Faturamento aparecem como "MQLs (manual)", "SQL (manual)", "Vendas (manual)", "Valor de venda (manual)" ou "Total de Faturamento (manual)". Os sinônimos do piloto cobrem esses casos. Se aparecer um rótulo novo, acrescente-o em `SINONIMOS` e não renomeie a planilha do cliente.
- **A linha Conexões é opcional na fonte, mas a visão de conectados é obrigatória na planilha.** Sem o dado, a cadeia segue Leads → MQLs direto, e as linhas de Leads conectados e MQLs conectados ficam com a taxa em branco para o cliente preencher. O usuário recusou taxa suposta ("não coloque"), inclusive a do painel antigo (90% e 80%). **Mudou na v8.1 (indústria de plásticos):** taxa suposta continua proibida, mas benchmark verificado entra no lugar do buraco, marcado como premissa de mercado (`--premissa-mercado conexao_lead=...|fonte`). Com ela, Lead → MQL no template = (Leads → Conexões) × (Conexões → MQLs), o que reproduz os volumes do piloto.
- **Sem a linha Gross Margin, a margem vira pergunta obrigatória.** Na consultoria B2B não havia a linha, e o usuário informou 25%. Registre nas observações que a margem foi informada, não lida.
- **O ano vem da "Data Inicial".** Na consultoria B2B, janeiro e fevereiro caíam em 2025 se o ano fosse deduzido pela posição da coluna.
- **Uma linha homônima vazia de outro bloco não é etapa.** A aba principal da EZ não tem "Conexões", e o piloto achava a do bloco Meta, vazia, o que zerava lead → MQL e o funil inteiro. Hoje, etapa opcional sem nenhum valor conta como ausente. Desconfie de qualquer taxa 0% ou de um funil que zera.
- **Os blocos por plataforma (Meta, Google) não são confiáveis.** Na EZ, o bloco Meta repetia MQL e SQL de agosto em setembro, e as linhas Connect Rate (900%), "% Lead - Conexão" (#REF!) e Ticket Médio de setembro estavam erradas. O piloto usa o bloco Indicadores V4. Aponte os erros ao usuário, que é quem cuida do Growth Pack.
- **Leads de formulário nativo não passam pelo site.** Quando a fonte tem "On-Facebook Leads" e "Website Leads" zerado, o GA4 não entra no funil (na EZ ele nem tinha dados). No caminho da skill, a aba não mostra connect, visitas nem landing page: o funil começa em clique → lead.
- **Conexões pode mudar de sentido entre meses.** Na multimídia automotiva, agosto teve 86 conexões para 23 MQLs (leads conectados) e setembro 9 para 46 MQLs. O Growth Pack calcula "% MQL - Conexão" como se a conexão viesse depois do MQL, e mostrava 373,91%. O usuário quis as duas visões: leads conectados pela fonte e MQLs conectados em branco (`--conexao-so-lead`).
- **Critério de MQL que muda de um mês para o outro engana a rampa.** Na multimídia automotiva, lead → MQL foi 6% em agosto e 74% em setembro, e MQL → SQL foi 74% e 2%. A mediana por etapa juntava o melhor de cada mês e projetava 44 SQLs em março, 2,6 vezes o melhor mês real. Fixe as duas etapas na média ponderada da janela (`--fixar lead_mql=... --fixar mql_sql=...`), o que preserva lead → SQL.
- **`--ticket` só vale quando a janela não tem ticket.** Para usar o ticket informado pelo cliente no lugar do histórico, use `--fixar ticket=1500`.
- **Uma venda grande e pontual distorce o histórico.** Na revestimentos, uma venda de R$ 403 mil em janeiro de 2026 deixava o acumulado histórico positivo (R$ 61 mil), enquanto o ritmo recente perdia R$ 4,5 mil por mês. Mostre as duas leituras ao usuário e use a mediana como alvo da rampa, nunca o melhor mês.

## 2. Perguntas que mudam o resultado

- **Receita do cliente ou GMV com comissão?** No turismo, a agência recebe 15% do GMV, então o resultado é GMV × comissão × margem. Nos demais, a receita já é do cliente (comissão 1).
- **Déficit histórico entra na projeção?** Calcule e informe primeiro o acumulado dos meses fechados. Na consultoria B2B, o déficit de R$ 53.812 entrou como acumulado inicial (`--acumulado-inicial -53812`), e por isso o acumulado de dezembro fecha em −R$ 71,9 mil mesmo com os meses melhorando.
- **Desde quando o histórico é comparável?** Mudança de oferta, canal ou campanha reinicia a comparação. Na consultoria B2B foi a partir de maio de 2026 (`--desde maio/2026`).
- **Ciclo de venda.** Pergunte sempre. Com CRM, meça a curva com `scripts/ciclo_crm.py` e use `--ciclo`; sem CRM, `--ciclo-dias` com o ciclo médio informado. `--lag` ficou como atalho de dois meses.

## 3. Regras de modelagem

- **Antes de qualquer taxa, faça a conta da estrutura.** Divida o fee pela margem que cada venda deixa. Na EZ, a agência fica com 6% do valor vendido (15% de comissão × 40% de margem): uma venda de R$ 22 mil deixa R$ 1.333, e o fee de R$ 9.000 exige quase 7 vendas por mês, contra 1 a 2 no histórico. Se a margem por real de mídia fica perto de R$ 1, a mídia só se paga e mais verba não resolve. Diga isso logo, porque aí a conversa é de estrutura (fee, remuneração), não de mídia.
- **Campanha que mudou no meio da janela: fixe a etapa.** Na EZ, julho rodava outra campanha (conversas por mensagem) e convertia 19,5% de clique em lead; agosto e setembro davam 7,4% e 3,2%. A janela de julho a setembro dava 11,9%. Use `--fixar clique_lead=<taxa da campanha atual>`: o alerta fica registrado na Metodologia.
- **A rampa por alavanca pode juntar o melhor de meses diferentes.** A qualificação de agosto (MQL → SQL de 50%) com o volume de leads de julho gera mais SQLs do que qualquer mês real. Compare leads e SQLs projetados com o ritmo do mês corrente. Na EZ, setembro caminhava para cerca de 51 leads, e a projeção pedia 133: avise o usuário que a projeção é otimista no topo do funil.
- **Ciclo de venda.** Quando os SQLs de um mês viram vendas no seguinte (EZ: 49 SQLs em agosto, 2 vendas em setembro), use `--lag`. A EZ ficou com 50%.
- **Quando a meta não fecha, o piloto calcula o caminho sozinho.** É o valor de cada alavanca, uma por vez, que faz o mês-alvo fechar no zero, comparado com o melhor mês fechado. Mais o fee que fecharia, a verba que cobriria o fee e o primeiro mês positivo sem teto. O gerador leva isso para a seção "Caminho para o breakeven" da Metodologia. Use essa tabela na resposta: ela é a resposta à pergunta "o que precisa acontecer?".
- **O alvo da rampa é a mediana, não o melhor mês.** Com base pequena, o melhor mês de cada alavanca estica a projeção: consultoria B2B saltou de R$ 322 mil para R$ 1,1 milhão em 12 meses. Com a mediana, o resultado fica colado no histórico.
- **Nunca entregar só "irrealista".** Sempre diga em que mês o breakeven fica realista e qual alavanca tem mais folga. Se ele não acontece até dezembro, diga isso com todas as letras e mostre o caminho: o que teria que mudar (fee, verba ou taxa) e quanto. O usuário não apresenta ao cliente uma planilha com todos os meses negativos sem essa leitura.
- **Taxas de etapa não passam de 100%.** Isso vale para CTR, clique → lead e as demais. Se passar, é denominador subcontado na fonte.
- **Connect rate e visitas orgânicas.** A planilha padrão não mede landing page, então a aba não mostra connect nem visitas, e o funil começa em clique → lead. Se o cliente tiver GA4 na landing page, dá para medir o connect e as visitas não pagas. Nesse caso vale a mesma regra do e-commerce: o funil de lead corre só sobre as visitas pagas, e as não pagas ficam como contexto. Aplicar a taxa paga às visitas orgânicas infla os leads atribuídos à V4.
- **Horizonte até dezembro.** A projeção vai do mês corrente até dezembro, com o realizado ao lado de cada mês. Nada de meses do ano seguinte.

## 4. Casos, para calibrar a intuição

| | consultoria B2B | revestimentos |
|---|---|---|
| Fee e verba | R$ 6.500 e R$ 3.000 | R$ 5.900 e R$ 5.000 |
| Margem | 25% (informada) | 30% (Gross Margin) |
| Acumulado inicial | −R$ 53.812 | zero |
| Resultado mensal, set a dez | −R$ 7,9 mil a −R$ 2,2 mil | −R$ 8,4 mil a +R$ 7,9 mil |
| Acumulado em dezembro | −R$ 71,9 mil | +R$ 3,6 mil |
| Payback | não atinge no período | Mês 4 (dezembro) |
| Leitura | com essa margem e esse fee, nem a mediana paga a operação no ano | fecha percorrendo a rampa até a mediana |

**turismo** (setembro de 2026). A margem passou por três leituras, e cada uma trocou o veredito:

| Leitura da margem | % do valor vendido | Leitura |
|---|---|---|
| 15% de comissão × 40% (painel antigo) | 6% | nunca breaka |
| 20% sobre o valor cheio | 20% | no azul em dez/26, acumulado zera em mai/27 |
| **15% de comissão × 20% de margem (confirmada em reais: R$ 660 numa venda de R$ 22 mil)** | **3%** | **nunca, nem com fee zero** |

Com 3%, cada R$ 1 de mídia devolve R$ 0,55, então mais verba aumenta o prejuízo. Para cobrir fee e mídia, a EZ precisaria vender cerca de R$ 367 mil por mês pela V4 (17 viagens de R$ 22 mil), e o maior mês foi R$ 60 mil. SQL → venda precisaria ir de 4,5% para 55%. Planilha final: setembro a dezembro, verba de R$ 2 mil +10% até R$ 3 mil, acumulado de −R$ 61 mil em dezembro (com −R$ 21,4 mil de déficit inicial), IRREALISTA. Lições: pergunte a margem em reais antes de qualquer conta; com margem baixa, o veredito é de estrutura (modelo de remuneração, produto de margem maior, conversão comercial, recorrência do cliente), e mídia não resolve.

Depois, a pedido do usuário, entrou o SEO (incluído no fee): outubro de preparação e visitas orgânicas subindo de novembro até 10 mil por mês em maio de 2027, com conversão de 6,15% (a clique → lead atual). A planilha foi até maio de 2027. O GMV sai de R$ 10 mil em setembro para R$ 179 mil em maio, e as vendas de 0,5 para 8 por mês. Mas com 3% de margem o resultado só melhora de −R$ 10,5 mil para −R$ 6,6 mil por mês: cada visita vale cerca de R$ 0,40, e o SEO sozinho precisaria de uns 26 mil visitas por mês para fechar. O usuário quer essa visão mesmo quando não fecha, porque ela mostra ao cliente o que o SEO acrescenta em leads e faturamento.

Premissas finais da EZ (18/09/2026): fee de R$ 6.901 (o do contrato; o Growth Pack mostra R$ 9.000, substituído com `--fee-historico`), comissão de 14% sobre a viagem e margem de contribuição de 20% sobre a comissão, ou seja, 2,8% do valor vendido. Com SEO até 10 mil visitas em maio de 2027: GMV de R$ 179 mil em maio, resultado do mês de −R$ 6,4 mil (set) a −R$ 4,9 mil (mai), acumulado de −R$ 77,6 mil em maio, sem breakeven em 48 meses. Cada R$ 1 de mídia devolve R$ 0,51; para dezembro fechar, SQL → venda precisaria ir de 4,5% para 23,6%.

CRM da EZ (18/09/2026): fee de R$ 6.901 + R$ 3.000 do CRM a partir de outubro; ticket da recompra de R$ 15 mil; 2 e-mails por mês para leads, 1 reativação e 1 cross-sell. Só a base da V4 estava disponível: 665 leads sem compra em setembro e 3 clientes de junho a agosto. A base histórica da EZ ficou em branco. De setembro a maio de 2027, o CRM soma R$ 22 mil de recompra e R$ 241 mil de reativação (quase todo por e-mail para a base de leads, que chega a 4 mil), +31% sobre os R$ 846 mil de novos leads. Com 2,8% de margem, isso dá R$ 7 mil contra R$ 24 mil de custo. Para o CRM pagar os R$ 3 mil sozinho, seriam cerca de 714 clientes de 6 a 12 meses, 1.429 inativos ou 7.143 leads. A base histórica da EZ é o dado que decide essa frente.

**multimídia automotiva** (18/09/2026). Loja de multimídia automotiva, ticket de R$ 1.500 por unidade, margem de 25% (provisória, informada pelo usuário), fee de R$ 8.364,36 e verba de R$ 3.000. Só havia um mês fechado (agosto, com formulário a partir de 25/08) e setembro parcial. Cada venda deixa R$ 375, então fee mais mídia exigem 30 vendas por mês, e o funil entrega 0,7. Resultado de −R$ 11,1 mil por mês e acumulado de −R$ 76 mil em março de 2027 (meta M7, do zero em setembro), sem breakeven em 48 meses. Nenhuma alavanca fecha sozinha, nem com fee zero: cada R$ 1 de mídia devolve R$ 0,09 de margem. A conversa é de estrutura e de atribuição (as 147 conversas de WhatsApp de agosto não entram em Leads; falta confirmar se as vendas vindas delas entram em Vendas), não de mídia.

Depois, o usuário pediu dezembro ("precisa breakevar até dezembro; se não tiver dados suficientes, traga dados de mercado"). Com os benchmarks (19/09/2026), a multimídia automotiva está dentro do mercado em clique → lead (5,7% contra 4,15% a 8,54%) e CPM, e fora em contato com o lead (22% contra 47% a 79%, Foureyes) e SQL → venda (5,9% contra 22,5% a 33,2%, RD Station e First Page Sage). Margem de 25% coerente com o setor (IBGE PAC 2024: 29,9% de margem bruta em peças e acessórios). Peças e acessórios não sobem no fim do ano (IBGE PMC), então não entrou sazonalidade. Com o funil só no mercado conservador, a mídia não se paga e dezembro não fecha com verba nenhuma; no mercado médio, com ticket de R$ 1.500, a verba de dezembro teria de ir a R$ 25 mil. O usuário escolheu o kit de R$ 2.000 (aparelho + kit + instalação, dentro das amostras de preço) e verba de R$ 3.000 → 5.600 → 8.200 → 10.900: dezembro fecha em +R$ 62, com 1.045 leads e 39 vendas; o acumulado fica em −R$ 27,7 mil e zera em abril de 2027 com R$ 20 mil de verba a partir de janeiro. A pedido do usuário ("faça até o momento que eles forem breakevar"), a planilha foi até o payback: a verba segue em degraus de +R$ 2.600 até R$ 21.300 em abril de 2027 e o acumulado zera em maio de 2027 (+R$ 757), REALISTA COM RAMPA. Com a verba parada em R$ 10.900, o acumulado nunca zera: pergunte o plano de verba depois do mês-alvo antes de estender. Mas o usuário questionou o CPM e o CTR, e com razão: o plano usava o CPM médio de agosto e setembro (R$ 4,23), puxado por agosto (R$ 3,79, campanhas de catálogo e mensagem). Com o custo da campanha atual (setembro: CPM R$ 7,43, custo por lead R$ 16), aquele plano nunca fechava. O CPM da multimídia automotiva já fica abaixo de todos os meses da mediana brasileira (R$ 18,26, Superads); o CTR de link (0,68%) está um pouco abaixo do único comparativo do setor (0,80%, peças e serviços automotivos, LocaliQ). Plano final: custo de setembro, CTR até 0,80%, contato 69%, SQL → venda 33,2% (varejo, RD Station), kit de R$ 2.500 e verba em degraus até R$ 21.300; dezembro fecha em +R$ 1,7 mil e o acumulado zera em abril de 2027. Com CPM de R$ 10, o acumulado não zera em 24 meses. Depois o usuário pediu Black Friday ("90%"), a cascata ROAS → margem → fee e o acumulado zerado em dezembro contando setembro. O Google Trends de "central multimídia" (2021–2025) mostra +5% na semana da Black e 2% a 8% em dezembro; os +90% são de smart TV. Com essa sazonalidade, dezembro fecha em +R$ 3,4 mil e o payback continua em abril de 2027. Zerar o acumulado em dezembro exigiria o funil no nível do mercado já em outubro ou novembro, com R$ 12 mil a R$ 18 mil de verba desde outubro: não realista para quem contata 22% dos leads e fecha 5,9% dos SQLs. Na visão de 12 meses (set/2026–ago/2027), o usuário pediu CPM mais caro: o público local satura com a verba e o CPM base sobe até R$ 10 em abril, com eleição, datas e remarketing por cima. Com isso a multimídia automotiva não se paga em 12 meses (acumulado de −R$ 39,7 mil em agosto de 2027); o caminho é clique → lead na média do mercado, kit de R$ 3.000, margem real de 30% ou fee menor. O CPM diário do Growth Pack mostrou que a eleição não mexeu no CPM do público da multimídia automotiva. O usuário rejeitou essa versão ("eles já estavam batendo o break-even... volta o anterior e mexe só no CPM"): premissa que derruba o breakeven sem evidência não serve. Ficou o plano anterior com o CPM mais caro no nível em que o breakeven ainda acontece: multiplicadores de eleição, datas e remarketing e a base subindo até R$ 8,00 em abril. Dezembro no azul (+R$ 2,0 mil) e acumulado zerado em julho de 2027. Lição: quando o usuário pede CPM mais caro, mostre a faixa em que o plano ainda fecha e pare no maior valor que fecha; não escolha o extremo.

**Regra que saiu da multimídia automotiva (v7.0):** a aba de projeção segue o modelo padrão e mostra o valor usado no mês; premissa que varia fica na aba Premissas, em tabela mês a mês (CPM base × multiplicador × CPM usado; SQL → venda da rampa × sazonalidade × taxa usada). O usuário: "o ideal é sempre manter nas premissas os dados que a gente quer observar, para não ficar poluído na projeção". Cada conta tem frentes diferentes (mídia, SEO, CRM, social, remarketing): pergunte o que está contratado antes de montar os blocos.

**SaaS de diário de obra** (29/09/2026). SaaS de diário de obra, PLG, planos Standard R$ 209/mês (anual 169) e Plus R$ 350 (anual 309),
checkout na Hotmart, trial de 7 dias sem cartão. Fee R$ 5.941,81. **Primeiro cliente de assinatura da skill** — daí o
`--recorrencia` da v7.9. Três lições que valem para o próximo SaaS:

1. **A conta de estrutura decide antes de qualquer taxa.** Cada assinante do Standard anual deixa R$ 118 de MC por mês
   (169 × 70%). Fee mais verba de R$ 5 mil exigem **92 assinantes ativos**; só o fee exige 50. A base atribuível à V4
   no fim de setembro era 2. O caminho do piloto confirmou: o **fee que fecharia o M12 é negativo** (−R$ 2.021), ou seja,
   nem de graça o contrato fecha em 12 meses nesse nível de funil e preço.
2. **Margem: 80% é a mediana de software, mas não é a MC1.** A Hotmart leva ~10%, então a MC1 usada foi **70%**.
   Gross margin de benchmark não é margem de contribuição — desconte o meio de pagamento e o que mais for variável.
3. **Vazamento de integração não é taxa.** 57 dos 59 leads do formulário nativo do Meta nunca entravam no fluxo de
   trial, e isso piorava com a escala do Meta (3 MQLs presos em julho, 27 em setembro). Projetar a taxa observada
   (MQL → trial de 20,3%) congelaria o defeito dentro da previsão. A separação certa é medir **quem consegue chegar**:
   de quem chegava ao painel, 50,0% viravam trial, estável em 44%/50%/56%. Os dois números viraram dois cenários.

**Regra que saiu da SaaS de diário de obra:** antes de aceitar uma taxa de etapa baixa, pergunte se ela é **comportamento** ou
**encanamento quebrado**. Se for encanamento, o número certo é a taxa de quem passa pelo cano que funciona, e o
conserto vira cenário — com a diferença entre as duas linhas medindo, em reais, quanto vale a correção.

**indústria química B2B · Domissanitários** (01/10/2026). Indústria química B2B com duas linhas (domissanitários e lavanderia
branca); a projeção cobre só domissanitários. Fee R$ 2.250 (contrato; o Growth Pack mostra R$ 2.500), verba R$ 2.500 no
Meta, margem 30% provisória, ticket R$ 929 (média das 2 vendas com UTM), 1 venda a cada ~100 leads. Cada R$ 1 de mídia
devolve R$ 0,07; o fee que fecharia é negativo; acumulado de −R$ 82,8 mil em dezembro (com −R$ 48,9 mil de déficit
de mai/25 a abr/26), IRREALISTA. Três lições:

1. **Growth Pack que soma linhas de produto não serve de fonte de mídia.** A verba do GP misturava lavanderia,
   institucional e domissanitários, e não tinha nenhuma linha de lead ou venda. A mídia veio da API (Meta e Google)
   **por campanha**, filtrando pelo nome, e o funil da planilha do comercial. O Google, que parecia canal de
   domissanitários, gastava quase tudo em Lavanderia e Institucional.
2. **A data do primeiro lead não é a data do contrato.** O backup começava em maio/26, mas a projeção anterior
   tratava o contrato desde maio/25 (−R$ 63,5 mil). Pergunte o início do contrato e peça a projeção anterior **antes**
   de calcular o déficit: o déficit inicial dobrou depois que ela chegou.
3. **Sem MQL e SQL na fonte, defina pelas colunas do comercial e escreva a definição.** MQL = segmento declarado no
   formulário (fábrica ou distribuidora); SQL = status de negociação, portfólio ou pedido; conexão = "Lead respondeu?".
   Em químico B2B a recompra decide o valor do cliente e quase nunca é medida: registre como a lacuna principal.

**fábrica de acessórios de cortina · fábrica de acessórios para cortina** (01/10/2026). Vende para lojista (B2B), Google R$ 1.500 + Meta R$ 500,
fee de R$ 5.000 desde jan/26, margem de 30% provisória (a projeção anterior usava 20%), 11 vendas de jan a set (ticket
R$ 1.281 na janela, mediana R$ 1.873). Funil contra o mercado: acima em lead → MQL (64% contra 26%–40%), SQL → venda
(43% contra 13%–20%) e CTR; abaixo em clique → lead (4,3% contra 8,2%–9,8%) e MQL → SQL (20% contra 23%–42%). Três
leituras do mesmo cliente, que mostram a ordem certa das alavancas:

| Premissas | Margem por R$ 1 de mídia | Fecha? |
|---|---|---|
| Histórico do cliente, verba R$ 2 mil | R$ 0,59 | não, nem com fee zero |
| Funil de mercado nas duas etapas fracas | ~R$ 2,30 | só com verba de R$ 4 a 6 mil (sem legado zera set/27 com R$ 6 mil) |
| + recompra trimestral por 12 meses (~4,7 pedidos) | ~R$ 2,75 já no funil de hoje | otimista fecha; Breakeven fecha com R$ 2 mil (sem legado zera jun/27) |

Lições: (1) compare cada etapa com o mercado antes de dizer "não fecha"; (2) em B2B de reposição a recompra é do
modelo de negócio e entra na projeção principal; (3) a linha "Conexão" do Growth Pack era cópia dos SQLs — entrou 69%
de mercado como premissa marcada.
