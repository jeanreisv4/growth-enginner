# Histórico da skill projecao-breakeven

Cada versão muda o que o cliente vê. Antes de publicar uma versão nova, rode `python3 tests/regressao.py`.

## v7.7 · 24/09/2026 · Projete de onde a operação está, não da média da janela

- **O gráfico "Resultado acumulado mês a mês" também estende até o payback.** A v7.3 tinha estendido só a "Curva de payback", e a planilha ficava com dois gráficos do mesmo número em horizontes diferentes: um cruzando o zero e o outro terminando no vermelho sem explicar por quê. Agora, quando o acumulado ainda é negativo na última coluna da tabela, os dois leem a mesma série estendida. Os meses da tabela continuam por fórmula viva (acompanham quem editar a aba) e só a extensão é literal.
- **`--rampa-desde N`: a rampa passa a poder começar depois do Mês 1.** Antes ela sempre partia do M1, e numa tabela que já contém meses vividos isso distribuía a melhora pelo ano inteiro — a recuperação aparecia como se parte dela já tivesse acontecido no passado. Com a tabela de jan a dez e a rampa em `--rampa-desde 10`, os nove meses vividos ficam na taxa de hoje e só o Q4 sobe.
- **Regra que saiu de um erro meu e vale sempre: projete a partir de ONDE A OPERAÇÃO ESTÁ, não da média da janela.** Na indústria de plásticos eu tinha projetado a partir da média de 9 meses (29,1 vendas) quando os dois últimos meses entregavam 17 — ou seja, assumindo em silêncio que a quebra já estava consertada. Corrigido, o payback foi de nov/2026 para fev/2027 e o pior caixa de −R$ 2,9 mil para −R$ 7,5 mil. **Quando os últimos meses destoam da janela, a janela não é o ponto de partida: é o alvo.**
- **Achado de método: testar se o cliente é limitado por LEAD ou por CAPACIDADE antes de projetar volume.** Na indústria de plásticos a correlação entre leads e vendas no ano é **−0,29** e entre leads e conversão é **−0,73**: a operação fecha ~28,6 negócios/mês quase independentemente do volume que chega (597 leads → 33 vendas em abril; 279 leads → 37 em junho). Num cliente assim, projetar venda como função de lead é estruturalmente errado e mais verba não produz mais venda — a alavanca é ticket e capacidade. **Duas linhas de correlação evitam uma projeção inteira errada.**

## v7.6 · 24/09/2026 · Economia unitária: MC1, CAC permitido e as três camadas de breakeven

- **Vocabulário padrão adotado.** O que a skill chamava de margem de contribuição é a **MC1** (margem pré-CAC) da contabilidade gerencial; o teto de gasto por venda é o **CAC permitido** (*allowable CAC*) da literatura de unit economics. Os termos entram no SKILL.md e na aba Premissas para a conversa com o financeiro do cliente usar a mesma palavra.
- **Três camadas de breakeven, declaradas separadamente**, porque respondem perguntas diferentes e são confundidas o tempo todo: transação (`1/MC1`), contrato (`(fee+verba)/MC1/verba`) e empresa (`(fee+verba+fixas)/MC1/verba`). Na indústria de plásticos: 5,62 · 12,50 · **65,0**, contra 13,3 realizados. A mídia é muito lucrativa, o contrato empata por pouco, e a camada 3 diz que **a empresa não tem como ser consertada por mídia** — é o argumento quantitativo para levar a conversa ao custo de insumo.
- **Correção de uma regra de bolso comum.** Circula que MC1 entre 15% e 20% inviabiliza mídia. É falso como enunciado: o que decide é **MC1 × ticket**, não MC1. Uma MC1 de 17,8% num ticket de R$ 3.143 dá R$ 559 de CAC permitido; uma de 40% num ticket de R$ 80 dá R$ 32 — a de margem menor tem **17x mais espaço**.
- **Essas contas são lineares num ponto, não ao longo de um caminho** — e a skill passa a declarar as três curvaturas: o ROAS exigido cai com a verba (exato, o fee dilui, assíntota `1/MC1`); o ROAS entregue cai com a verba (premissa, saturação); e a MC1 cai com o ticket (pedido grande vem com desconto). A verba ótima é absurdamente sensível ao expoente de saturação: na indústria de plásticos vai de R$ 5 mil a R$ 146 mil.
- **Regra nova que vale mais que qualquer modelo:** com verba estável no histórico (1,4x de amplitude no ano), **não existe verba ótima calculável** — é preciso variar a verba de propósito. Dizer isso, em vez de entregar um número falsamente preciso.

## v7.5 · 24/09/2026 · O DRE do cliente entra na entrevista

- **Pergunta nova na entrevista: peça o DRE antes de fixar a margem.** Na indústria de plásticos a margem vinha de estimativa (12%) e o DRE mostrou **17,8%** — margem de contribuição reportada de 12,9% mais os Custos Indiretos, que eram overhead de fábrica e não CMV. Sozinha, essa correção derrubou a receita mensal de breakeven de R$ 111.292 para R$ 75.028 e mudou o veredito de "nenhum mês pagou o contrato" para "quatro pagaram". **Uma premissa estimada inverteu o diagnóstico de um cliente inteiro por nove meses.**
- **O DRE também responde "quanto sobra para aquisição".** Margem de contribuição menos as despesas fixas que não são aquisição. No cliente: +R$ 7.057/mês em 2024 e **−R$ 13.215/mês** em 2025 — ou seja, o contrato estava sendo financiado por prejuízo, e isso aparece na linha "Despesas Comerciais" do DRE, que saltou 787%. É a conta que o contador do cliente vai fazer; melhor fazer antes.
- **Como ler um DRE para isto, em três passos:** (1) a margem que importa é a **de contribuição**, não o lucro líquido — e confira o que está dentro do CMV, porque overhead mal alocado a derruba sem que nada tenha piorado de verdade; (2) reclassificar conta **não muda o EBITDA** — se a conta muda e o resultado não, era classificação; (3) compare dois anos em **% da receita**, não em reais: no cliente as Compras foram de 36,7% para 45,1% (+8,3 p.p.), cresceram 2,3x mais rápido que a receita e explicam **70%** da piora do resultado.
- **`metodologia_mercado.py` aceita os dois formatos de arquivo de benchmark.** Os de v7.3 em diante usam `linhas` como dicionário (com veredito, faixa de mercado, verificação e fontes por premissa) e os antigos usam lista de seis campos. O script normaliza em vez de obrigar a reescrever arquivo.
- **Armadilha do piloto que vale como regra:** `--alvo X` sozinho não impede as OUTRAS alavancas de rampar para a mediana do período. Numa projeção que deve mover uma alavanca só, **trave todas as demais com `--fixar`** — sem isso a projeção promete melhora no funil inteiro sem dizer.

## v7.4 · 23/09/2026 · Template em outra moeda, e benchmark de home services em Meta

- **`--moeda` no gerador.** O template nascia com `R$` cravado no código — em formato numérico, em rótulo (`[R$] FEE V4`) e no eixo dos gráficos. Agora `--moeda "US$"` troca os três. Veio do cliente de climatização, cliente da V4 em Nova Inglaterra (Massachusetts), que fatura em dólar.
- **Como funciona:** os formatos numéricos nascem na importação de `projecao_builder`, antes de qualquer argparse, então `build_workbook` lê `--moeda` de `sys.argv` e planta `PROJECAO_MOEDA` no ambiente antes do import. O texto dos rótulos é trocado num passe final sobre a pasta (`aplicar_moeda`), que **pula fórmulas de propósito**: `R$` também é referência absoluta válida no Excel (coluna R, linha travada), e trocar dentro de fórmula quebraria a planilha.
- **O piloto já lia dólar:** `num()` sempre tirou `$` junto com `R$`, então `$1.200,00` na fonte nunca foi problema. O que faltava era a saída.
- **Trava do melhor mês passa a enxergar o mês corrente.** Com `--incluir-corrente`, a janela de taxas e o período de referência já incluíam o mês parcial, mas o `teto_receita` continuava só nos fechados — então o alerta disparava contra o próprio melhor mês do cliente. No cliente de climatização o melhor mês fechado era US$ 350 e o corrente US$ 12.680: a trava acusava "79,3x o melhor mês" em toda projeção. Agora o teto sai do período de referência, marcado como parcial, e o alerta diz que aquele mês ainda vai subir. Passou de 79,3x para 2,2x, com a verba comparada.
- **Regressão:** 19 casos (novo: `inside_sales_moeda_usd`), que exige os rótulos em `[US$]`, proíbe os em `[R$]` e confere que nenhuma fórmula foi tocada.
- **`scripts/publicar.py`:** a anonimização da cópia pública virou script, depois de a v7.2 ter sido publicada com remendos manuais que se perdiam. Troca cada cliente pelo segmento, generaliza caminhos de máquina, **não publica a si mesmo nem o logo da agência**, e audita o resultado — o push só sai com a auditoria limpa. Duas armadilhas travadas nele: nunca trocar `V4` sozinho (é rótulo de linha da fonte, `Fee V4`) e o mapa não levar artigo (com "usuário" → "o usuário", "O usuário" virava "O o usuário"). Anonimiza **cliente**, não a agência.
- **Logo opcional.** `build_sheet` só insere a imagem se o arquivo existir. Era um remendo aplicado à mão na cópia pública a cada publicação; virou código.
- **`referencias/home_services_hvac_meta_benchmarks.json`:** 8 premissas, 10 blocos de descarte e 14 fontes, para HVAC residencial nos EUA anunciando em **Meta**, com tickets de Massachusetts. Três pesquisas alimentaram o arquivo; ~200 URLs apareceram, 45 foram abertas, 22 retidas.
- **Lição de método que custou meia pesquisa: confirme o CANAL antes de pesquisar benchmark.** Montei o diagnóstico inteiro do cliente de climatização em cima de Google Ads porque a aba Plano de Mídia da planilha lista campanhas de Search e Local Services Ads. O cliente roda só Meta. Todo o benchmark de Google — CPC, CPL, book rate, LSA — foi descartado. Ficou no arquivo porque é bom, para o dia em que houver Google. **A pergunta "qual canal está de fato rodando" entra na entrevista antes de qualquer pesquisa de mercado.**
- **Padrão novo de diagnóstico: separar métrica quebrada de dado quebrado.** No cliente de climatização, CPM e CTR variavam 16x e 40x entre meses enquanto CPC, CPL e clique → lead variavam 3%. As que explodiram têm impressões no denominador; as estáveis não. Isso é assinatura de campo subcontado, não de mudança de leilão — e a reconciliação fechou: recalculando jul/ago com o CPM do único mês que bate, o CTR de agosto (0,33%) e o de setembro (0,31%) convergem. **Antes de explicar uma variação de dez vezes por comportamento de mídia, teste se o denominador mudou.**

## v7.3 · 22/09/2026 · Curva de payback além da tabela e benchmarks de indústria B2B

- **Curva de payback estendida.** A tabela tem 12 colunas e o payback muitas vezes cai depois delas — o gráfico terminava sem cruzar o zero e o payback virava nota de rodapé. Agora o gerador monta `payback_estendido` a partir dos 48 meses do piloto (seguindo no run-rate quando a série acaba antes) e o gráfico "Curva de payback" vai até o mês em que o acumulado zera. Na indústria de plásticos a curva passou de 12 para 44 colunas, de jan/2026 a ago/2029.
- **`referencias/industria_plasticos_b2b_benchmarks.json`:** 7 premissas, 44 fontes abertas e 77 descartadas, para indústria de plásticos e utensílios vendendo B2B a varejo e atacado no Brasil. Cada linha passou por verificação adversarial que abriu as URLs; duas conclusões do pesquisador foram corrigidas na verificação (SQL → venda e MQL → SQL).
- **Lição de método que motivou a pesquisa:** usar só o envelope histórico do cliente mede o teto errado quando a operação está quebrada — o melhor mês de quem está mal pode estar abaixo do normal do setor. A regra já estava no SKILL.md; o que faltava era aplicá-la antes de declarar "esta alavanca não chega".

## v7.2 · 22/09/2026 · Legado na projeção, projetado × realizado e a trava do melhor mês

- **Legado dentro da tabela.** A entrevista passa a perguntar se o cliente quer o histórico na própria tabela de projeção (1.4.2). Com `--inicio-contrato`, os meses vividos entram pela coluna Realizado e os seguintes são projeção, numa linha só — sem aba separada de histórico. O aviso que a pergunta precisa dar: a tabela tem 12 colunas, então legado longo come o horizonte.
- **Projetado × realizado.** Nova pergunta (1.4.3) sobre a projeção anterior, e `--legado arquivo.json` no gerador: a aba Premissas ganha um bloco com prometido, realizado e **atingimento** por métrica e por mês, vermelho abaixo de 100%. Na indústria de plásticos, o atingimento de faturamento da projeção antiga foi 38%, 50%, 57%, 128%, 40%, 56%, 15%, 5% e 5% — é a resposta quantificada ao "a gente nunca executou o que projetou".
- **Trava de sanidade do melhor mês.** O piloto calcula o melhor mês fechado de receita da fonte (`teto_receita`) e alerta quando a projeção pede mais de 1,2x isso no mês-alvo, dizendo o múltiplo e comparando a verba dos dois meses. O teto é de receita, não de capacidade: passar dele é legítimo com mais verba, e o alerta diz isso. Com menos de quatro meses fechados ele avisa que o teto é frágil. Teria pego a projeção antiga da indústria de plásticos, que pedia 2,4x o melhor mês com a mesma verba.
- **Qual fonte manda (1.1.0).** Com mais de uma planilha ou aba trazendo o mesmo mês, a skill pergunta qual vale antes de ler qualquer número, e registra a resposta. Veio da indústria de plásticos, onde janeiro aparecia com R$ 13.074 numa aba e R$ 45.759 na outra.
- **Como as vendas são contadas (1.1.0.1).** Três perguntas novas sobre a linha de vendas: lançamento manual ou CRM, data de criação ou de fechamento, com ou sem recompra da base. As três mudam o número em dezenas de por cento.
- **Refatoração:** o renderizador de tabela mês a mês da aba Premissas virou uma função só (`tabela_meses`), usada pelo histórico e pelo legado; a linha "Status na fonte" só aparece quando há status; e a área de impressão da aba passou a acompanhar o bloco mais largo em vez de ficar fixa em 14 colunas.
- **Numeração:** havia duas seções 1.6.3 no SKILL.md; a de datas comemorativas virou 1.6.4.
- **Regressão:** 18 casos (novo: `--legado`), mais a checagem de que `teto_receita` chega ao gerador em todos eles.

## v7.1 · 22/09/2026 · Leitura da aba: blocos, unidades, retorno em múltiplo e connect rate

- **Blocos com cor.** Cada seção da projeção tem cor própria e uma tarja vertical na coluna A com o nome do bloco: investimento (cinza), marketing (vermelho V4), vendas (âmbar), financeiro (verde) e resultado (preto). O investimento saiu de dentro do bloco de marketing e virou bloco próprio, e a fronteira entre mídia e comercial passou a ser o lead (lead → MQL é vendas, como na planilha de referência da V4).
- **Alavanca pintada na linha inteira.** Rótulo, meses projetados e coluna de total das linhas editáveis ficam na cor da alavanca (amarelo para editável, amarelo-claro para o que puxa a premissa geral), com barra lateral na cor do bloco. Antes só as células dos meses eram pintadas.
- **Unidade no rótulo.** Todo rótulo do inside sales começa por `[R$]`, `[%]`, `[QNTD]` ou `[X]`, convenção que o modelo e-commerce já usava. Fica explícito o que é investimento, o que é custo, o que é taxa e o que é múltiplo.
- **Retorno em múltiplo.** ROI do mês, da mídia e do projeto saem como `[X]` (MC ÷ custo): 1,00x = o período se pagou. O vermelho/verde desses múltiplos corta em 1,00x, não em zero (`x_rows` no builder). O cartão "ROI do projeto" virou "Retorno por R$ 1 investido".
- **Receita necessária para zerar o mês.** Novas linhas `[R$] receita/faturamento/GMV necessário para zerar o custo do mês` (custo ÷ margem, e ÷ comissão quando existe), `[QNTD] vendas necessárias` e `[R$] sobra/falta contra o necessário`, nos dois modelos. Diferente do bloco de meta, que arrasta o acumulado.
- **Connect rate de volta no inside sales.** O gerador forçava `sem_lp=True` em todo inside sales, o que apagava connect rate e visitas. Agora a etapa "Visitas" é opcional no piloto: entra quando a fonte tem a linha (`Visitas`, `Visitas LP`, `Visualizações da Página de Destino`, `Sessões - Pago`) ou quando `--connect-rate` é informado, e aí o funil vira clique → visita → lead. Sem nenhum dos dois, segue clique → lead — nenhuma taxa é inventada. `--connect-rate` deixou de sobrescrever a taxa clique → lead do inside sales, que era o comportamento errado.
- **"Antes do lag" virou ciclo de venda.** `VENDAS GERADAS NO MÊS (ANTES DO LAG)` → `[QNTD] VENDAS ORIGINADAS PELOS SQLS DO MÊS`, `VENDAS` → `[QNTD] VENDAS FECHADAS NO MÊS`, e a premissa `lag` virou "Ciclo de venda: % das vendas que fecha ainda no mês do lead". Com ciclo em 100% a primeira linha some, porque seria cópia da segunda (idem pedidos no e-commerce).
- **Guardas do connect rate (revisão adversarial da própria v7.1):** a etapa Visitas só entra quando é mensurável — linha preenchida em toda a janela e visitas ≤ cliques; fora disso o piloto derruba a etapa, volta ao clique → lead e avisa, em vez de travar a taxa em 100% (ou em zero) e encolher o funil sem ninguém ver. Os sinônimos de "Visitas" foram restritos a rótulos de landing page: "Sessões - Pago"/"Sessões Tráfego V4" pertencem ao bloco GA4 do site inteiro e capturavam a linha errada. `--connect-rate` é recusado quando a fonte já mede (use `--fixar connect=`), as visitas sintetizadas aparecem rotuladas como calculadas no histórico e não viram Realizado, e o prefill do realizado nunca passa dos cliques.
- **Trio de breakeven sobre o consolidado.** `receita necessária`, `vendas necessárias` e `sobra/falta` passaram a correr sobre `custo_cons × receita_cons ÷ mc_cons` (margem implícita do consolidado), o que vale igual para receita própria, comissão, CRM e e-commerce, usa o realizado nos meses vividos e elimina as três variantes de fórmula. A identidade conferida em todos os casos: sobra/falta × margem = resultado líquido do mês.
- **Retorno acumulado com déficit herdado.** `cum_cons/custo_acum + 1` dava múltiplo negativo quando havia "acumulado inicial" (o numerador carregava o déficit, o denominador não). Agora é MC acumulada ÷ custo acumulado, que bate com o cartão de KPI.
- **Acertos de leitura.** Coluna do rótulo de 40 para 52 (os nomes com prefixo eram cortados pela célula do Mês 1); o total continua cinza, porque amarelo é o código de "editável" e total é sempre fórmula; seções vizinhas do mesmo bloco compartilham uma tarja só, em vez de repetir a palavra; linhas `mixed` (sessões orgânicas, faturamento da loja, base do CRM) entraram na pintura de alavanca; e a explicação das cores e dos prefixos virou a seção "COMO LER A ABA DE PROJEÇÃO" na aba Premissas do cliente, que antes só existia na planilha demo.
- **O SQL sai de quem foi conectado, não do MQL.** A cadeia do inside sales virou lead → conexão → SQL → venda quando a fonte tem a linha `Conexões`; sem ela, volta a lead → MQL → SQL. O MQL sai da multiplicação e fica como qualidade do lead no bloco de marketing (`informativas()` no piloto). Motivo: a oportunidade depende de alguém ter falado com a pessoa — na multimídia automotiva, setembro teve 46 MQLs e 9 conexões, e o modelo antigo gerava SQL a partir dos 46. As duas linhas de conexão viraram uma só, `CONEXÃO SOBRE OS LEADS (MQL OU NÃO)`, porque todo MQL já é um lead e a conexão vale para os dois. O rótulo diz o denominador de propósito: encadear `MQL → conexão` parece natural mas não fecha — o time conecta lead que nunca virou MQL, e na multimídia automotiva agosto teve 23 MQLs para 86 conexões (374%). `--alvo conexao` deixou de ser gambiarra (subia o lead → MQL na proporção) e virou alvo direto da etapa; a versão antiga sobrevive só para fonte sem `Conexões`. Na multimídia automotiva a projeção ficou idêntica mês a mês — mesmo payback em jul/2027 — porque `lead → MQL × MQL → SQL` e `conexão × conexão → SQL` dão o mesmo lead → SQL (4,18%).
- **O marketing vai até o MQL.** `lead → MQL`, `MQLs` e `custo por MQL` voltaram para o bloco de marketing: o MQL é qualificado por critérios do formulário ou da landing page, não pelo vendedor (regra do usuário, 22/09). As seções viraram "MARKETING · DA VERBA AO MQL" e "VENDAS · DO ATENDIMENTO À RECEITA", que começa na conexão do lead. A planilha de referência da V4 põe lead → MQL no bloco comercial; a operação do usuário não funciona assim.
- **Cartões do resultado executivo.** Passaram a começar na coluna G, com respiro entre o bloco de premissas e os cartões, e a se organizar pela quantidade (até 8 cartões ficam 4 + 3, não 5 + 2). A ordem começa pelo resultado líquido, depois faturamento, custo e retorno. Saíram "maior exposição de caixa" e "excedente pós-payback" — o número da exposição segue no veredito, na aba Premissas.
- **Um bloco financeiro só, todo consolidado.** A aba trazia os blocos FINANCEIRO (só projetado) e RESULTADO (realizado onde existe) lado a lado, com **cinco métricas repetidas e com valores diferentes** — resultado MC, custo acumulado, resultado do mês, resultado acumulado e retorno por R$ 1. Em mês já vivido a versão projetada é ficção (na multimídia automotiva, setembro: R$ 658 de MC projetado contra R$ 0 real, R$ 11.364 de custo contra R$ 9.396), e nada indicava qual das duas ler. Agora existe um bloco financeiro só, em três grupos (resultado · quanto falta para zerar o mês · eficiência e retorno), com toda linha no consolidado. ROAS, ROAS de breakeven, retorno da mídia e retorno por R$ 1 passaram a rodar sobre as linhas consolidadas, o que exigiu uma `midia_cons`. O ROAS de breakeven virou `receita necessária ÷ mídia`, fórmula única que dispensa a variante da agência com margem 100%. `hidden_rows` no builder esconde as intermediárias de fórmula e as três flags `(1 = SIM)`, que alimentam os cartões e não são para o cliente: de 24 linhas visíveis para 16 métricas em 3 grupos.
- **Bloco orgânico parametrizável.** As linhas de tráfego orgânico deixaram de ser fixas em SEO: `--organico-origem` e `--organico-metrica` definem a origem (SEO, social orgânico, indicação) e o que é contado na entrada, porque em cliente sem site a entrada não é "visita" e sim clique no link da bio ou conversa iniciada. Os rótulos das três linhas e da premissa seguem esses dois valores; o padrão continua SEO/visitas orgânicas. Veio da multimídia automotiva, que não tem página nenhuma e cujo Growth Pack não mede orgânico de social.
- **Mês vivido sem receita.** A margem implícita do consolidado é 0/0 nesses meses e zerava a linha de breakeven (apareceu ao regerar a multimídia automotiva: setembro mostrava R$ 0 de receita necessária em vez de R$ 37.585). A fórmula agora cai para a razão planejada do mês, e a regressão passou a exigir que a linha seja sempre positiva.
- **Regressão:** 17 casos (novos: fonte com linha de visitas, connect rate informado na mão, ciclo de venda em 50% e o formato do EZ — margem 100% com comissão). A checagem de taxa acima de 100% passou a valer para todo rótulo `[%]`, exceto crescimento, conexão e participação, que podem passar por definição. Duas travas numéricas novas, porque a checagem de existência de linha não pegava troca de valor entre alavancas: `valores=` prende o número da alavanca no Mês 1 (connect rate e visita → lead), e a identidade **sobra/falta × margem = resultado líquido do mês** é conferida em todos os meses de todos os casos. Conferido por mutação: tirar a margem do denominador da linha de breakeven faz o teste falhar.

## v7.0 · 21/09/2026 · Modelo padrão de dados e entrevista por frente contratada

- **Regra do modelo padrão:** a aba de projeção mostra a cadeia padrão com o valor usado no mês; premissa que varia (CPM com saturação, multiplicadores de eleição, datas e remarketing, sazonalidade de demanda) não vira linha na projeção. A decomposição vai para a aba Premissas, em tabela mês a mês. A sazonalidade da demanda passou a entrar na taxa de SQL → venda usada no mês, com a tabela "Sazonalidade da demanda mês a mês" na aba Premissas.
- **Entrevista:** novas perguntas de 1.0 (frentes contratadas e o que o fee cobre), 1.3.1 (custo de mídia da campanha atual, saturação do CPM com a escala, fatia de remarketing, eleição e datas), 1.5.1 (prazo do cliente e cenário-meta em aba extra), 1.5.2 (capacidade da operação: contatos e vendas por mês) e 1.6.3 (sazonalidade do produto pelo Google Trends e IBGE; oferta não entra sem dado).
- **Premissa mais dura que ainda fecha:** quando o usuário pede uma premissa mais conservadora, mostre a faixa com o mês de payback de cada valor e pare no mais duro que ainda fecha; os extremos ficam como sensibilidade.

## v6.5 · 19/09/2026 · Cenário extra em outra aba (multimídia automotiva)

- Gerador com `--extra "premissas.json|Aba|Cenário|metodologia.json"` (repetível): cada cenário vira uma aba de projeção no mesmo arquivo, com a própria aba de premissas. multimídia automotiva: "Inside Sales" (plano base, payback em jul/2027) e "Cenário Dezembro" (acumulado zerado em dez/2026).
- Com cenários extras, o gráfico "Resultado acumulado mês a mês" de cada aba de projeção mostra também as linhas das outras abas (plano base × cenários), para o payback de cada um aparecer no mesmo gráfico. O usuário queria ver o acumulado do cenário nos gráficos da aba principal, não o resultado do mês nem o faturamento.
- `metodologia_mercado.py` aceita "taxas" e "justificativas" por premissa no analise.json, para a tabela de benchmarks mostrar as taxas do cenário.
- Regressão com caso de aba extra.

## v6.4 · 19/09/2026 · Aba Premissas, CPM ao longo do ano e visão de 12 meses (multimídia automotiva)

- A aba "Metodologia · <aba>" passa a se chamar "Premissas · <aba>", a pedido do usuário.
- Inside sales: "Custo total (fee V4 + mídia)" sobe para logo abaixo de fee e mídia.
- Piloto com `--cpm-crescimento`, `--cpm-teto` e `--cpm-crescimento-ate`: o CPM base cresce mês a mês (saturação do público) até um mês ou teto. Na planilha, com sazonalidade de CPM, aparecem "CPM base", "Multiplicador do CPM (eleição, datas, remarketing)" e "CPM efetivo".
- A pedido do usuário, a projeção mostra só a linha "CPM", já com o CPM usado no mês (base × multiplicador). A decomposição (base com saturação, multiplicador e CPM usado) fica numa tabela mês a mês na aba Premissas, como explicação para o cliente.
- Benchmarks: eleição de 2026 (TRE-RJ, CNN 2022), remarketing (Lebesgue, AdRoll, Metadata), CPM por data (Superads, Bïrch) e sazonalidade de demanda de 12 meses pelo Google Trends.

## v6.3 · 19/09/2026 · Sazonalidade, ROAS e retorno após a margem (multimídia automotiva)

- Piloto com `--sazonalidade-demanda` e `--sazonalidade-cpm`: multiplicadores mês a mês de vendas e de CPM (Black Friday, Natal). Na planilha viram linhas editáveis ("Sazonalidade do CPM" e "Sazonalidade da demanda") que entram nas impressões e nas vendas geradas.
- Inside sales ganha a cascata de retorno: ROAS (receita ou faturamento ÷ mídia), ROAS de breakeven ((fee + mídia) ÷ mídia ÷ margem), retorno dos anúncios após a margem (MC − mídia), ROI da mídia após a margem e o resultado depois do fee V4.
- Benchmarks: sazonalidade de central multimídia pelo Google Trends (2021–2025), Neotrust, Cielo, NielsenIQ e NRF; conferência do MQL → SQL.
- Regressão com caso de sazonalidade.

## v6.2 · 19/09/2026 · Dados de mercado quando o histórico é curto (multimídia automotiva)

- Piloto com `--alvo alavanca=valor`: o alvo da rampa vem de benchmark de mercado nas etapas sem histórico suficiente, nunca pior que o atual, com alerta. `--alvo conexao=0.69` (inside sales com Conexões na fonte) sobe lead → MQL na proporção da conexão e grava a conexão mês a mês.
- Planilha: a conexão lead vira linha mês a mês quando tem alvo de mercado; o envelope marca as alavancas com "alvo de mercado"; a Curva da projeção descreve a verba em degraus e os alvos de mercado.
- Novo `scripts/metodologia_mercado.py` e `referencias/multimidia_automotiva_benchmarks.json` (9 premissas, 24 fontes verificadas em 18 e 19/09/2026: Foureyes, HBR, RD Station, First Page Sage, WordStream, Superads, IBGE PAC e PMC, Damodaran, amostras de preço).
- Regressão com caso de alvo de mercado.
- Benchmarks de CPM, CTR de link e clique → lead no Brasil e no setor (Superads, LocaliQ, PTAX do BCB). A skill passa a exigir o custo de mídia da campanha atual e o estresse de CPM ao escalar a verba.

## v6.1 · 18/09/2026 · Conexão só de lead e receita própria (multimídia automotiva)

- Gerador com `--conexao-so-lead`: quando a linha Conexões conta só leads conectados, a conexão lead vem da fonte e a de MQL fica em branco para preencher, sem taxa suposta. O funil segue MQL → SQL e o realizado de MQL conectado fica aberto.
- Cliente com receita própria (comissão 1, sem CRM): saem as linhas de comissão e "receita da agência". A linha de faturamento vira "Faturamento (vendas × ticket)", o cartão de GMV sai e a meta pede faturamento, não GMV. Destra e RPS também mostravam "comissão 100%".
- Metodologia: as fórmulas do inside sales descrevem o funil real (leads = cliques × clique → lead) e o faturamento quando não há comissão; o cenário de referência cita o número real de meses.
- Regressão com o caso de conexão só de lead, que também confere que as linhas de comissão não aparecem.

## v6.0 · 18/09/2026 · CRM Marketing: recompra e reativação da base

- Piloto com `--crm crm.json`: a base de leads sem compra cresce com os leads novos e perde contatos pelo descadastro; os clientes envelhecem por coorte. WhatsApp (recompra de 6 a 12 meses), cross-sell (menos de 6 meses), e-mail (leads sem compra) e reativação (inativos com mais de 12 meses) atuam em grupos sem sobreposição. O faturamento sai separado em [1] novos leads, [2] recompra e [3] reativação. Os meses vividos usam os volumes realizados.
- `--fee-plano`: fee mês a mês (ex.: +R$ 3.000 quando o CRM entra).
- Planilha: bloco "CRM · recompra e reativação da base" com fórmulas vivas (base, coortes, vendas por canal, GMV por origem, GMV total), premissas editáveis, cartão de GMV total e gráfico de faturamento por origem.
- Metodologia: seções em tabela e com links. Novo `scripts/metodologia_crm.py`, que monta a análise, a tabela Premissa | Fonte | Benchmark | Período | Taxa | Justificativa, os benchmarks descartados e as fontes no fim da aba, a partir de `referencias/crm_turismo_benchmarks.json` (15 fontes verificadas em 18/09/2026).
- Regressão com caso de CRM, conferindo cada origem de faturamento contra o piloto.

## v5.6 · 18/09/2026 · Fee do contrato no histórico

- `--fee-historico`: quando a linha Fee V4 da fonte diverge do contrato, o fee informado vale em todo o histórico (déficit inicial, realizado dos meses vividos e prefill da planilha). O valor da fonte fica guardado e um alerta registra a troca.

## v5.5 · 18/09/2026 · SEO no inside sales

- `--organico-visitas` e `--organico-conversao`: visitas orgânicas mês a mês viram leads, somados aos pagos antes de lead → MQL, no piloto e na planilha. A planilha ganha as linhas de visitas orgânicas (editáveis), conversão, leads orgânicos e leads totais. Leads conectados e a conversão do funil passam a usar os leads totais.
- **Correção no gerador:** renomear a linha de leads apagava a fórmula ajustada para cliques; os ajustes de linha agora se mesclam.
- A regressão ganhou um caso com SEO.

## v5.4 · 18/09/2026 · Conectados sempre visíveis

- O inside sales volta a mostrar Leads conectados e MQLs conectados em todo cliente. Sem o dado na fonte, a conexão fica em branco para preencher (nenhuma taxa suposta), as linhas de conectados são informativas e a projeção não muda. O realizado de MQL conectado não é mais preenchido com o total de MQLs quando a fonte não mede conexão.

## v5.3.1 · 18/09/2026 · Margem confirmada em reais

- A entrevista pede a margem com uma venda concreta ("numa venda de R$ X, quanto sobra?"). A EZ passou por três leituras de margem (6%, 20%, 3%) antes da confirmação em reais.

## v5.3 · 18/09/2026 · Planilha até o payback (turismo)

- O piloto usa o realizado dos meses já vividos no veredito, como a linha consolidada da planilha. Antes, a EZ tinha setembro projetado em −R$ 8,9 mil e realizado em +R$ 1,8 mil, e o piloto dizia payback em ago/27 enquanto a planilha dizia mai/27. `--inicio` alinha o Mês 1 quando ele é o início do contrato.
- `--rampa-ate` separa o fim da rampa do mês-alvo. A planilha pode ir até o mês do payback sem que a rampa fique mais lenta e mude os números.
- Regra de horizonte: até dezembro por padrão. Quando o acumulado só zera depois, a planilha é estendida até esse mês, a pedido do usuário.

## v5.2 · 18/09/2026 · Duas datas no veredito e verba em degraus (turismo)

- O veredito sempre responde "em que mês fica realista", mesmo depois do horizonte: **no azul a partir de** (todo mês seguinte com resultado ≥ 0) e **acumulado zera em** (payback). As duas datas consideram o realizado dos meses vividos e a projeção por 48 meses. Aparecem no subtítulo, na Metodologia e num cartão novo, e a tabela ganha as linhas "Mês no azul?" e "No azul daqui até o fim?".
- `--verba-plano` define a verba mês a mês, em degraus. Na planilha, cada mês fica editável, e crescimento e teto saem das premissas.
- Inside sales: quando a comissão já é a margem da agência (margem 100%), a linha de margem sai e a comissão vira "margem da agência".
- O subtítulo mostra o período real (ex.: set/2026 a dez/2026) em vez de "12 meses".

## v5.1 · 18/09/2026 · Caminho para o breakeven (turismo)

- **Correção:** uma etapa opcional sem nenhum valor passa a contar como ausente. Na EZ, o piloto achava a linha "Conexões" vazia do bloco Meta e zerava o funil inteiro.
- O piloto calcula o **caminho** quando a meta não fecha: quanto cada alavanca precisaria, sozinha, para o mês-alvo fechar no zero, e se isso já aconteceu num mês fechado. Mais o fee que fecharia, a margem por real de mídia, a verba que cobriria o fee e o primeiro mês positivo sem teto. O gerador leva isso para a seção "Caminho para o breakeven" da Metodologia.
- `--fixar alavanca=valor` fixa uma etapa quando a campanha mudou no meio da janela. O alerta fica registrado.
- O template de inside sales deixa de mostrar linhas que o cliente não tem: connect, visitas e landing page (a planilha padrão não mede) e as linhas de conexão, quando a fonte não tem "Conexões". A demo mantém todas.
- O teste de regressão ganha um caso irrealista, que exige a seção do caminho e confere que as linhas de landing page não aparecem.

## v5 · 18/09/2026 · GA4, funil pago e versionamento

- **Correção:** o funil de e-commerce passa a correr só sobre as sessões pagas. Antes, as sessões orgânicas passavam pelas taxas do tráfego pago e inflavam a receita atribuída. Na varejo de tecidos, outubro aparecia com R$ 91 mil, contra R$ 50 mil do piloto.
- **GA4:**
  - `scripts/ga4_resumo.py` consulta o servidor MCP oficial e gera o `ga4.json` do mês.
  - O piloto aceita `--ga4` e separa Google (CPM, CTR, connect) de Meta (verba ÷ custo por sessão).
  - Carrinho e checkout do pago passam a ser medidos, e as sessões não pagas vêm do GA4.
  - A verba Meta é a verba da fonte menos o custo do Google Ads.
- O template ganha os blocos "Tráfego pago · Google", "Tráfego pago · Meta" e "Sessões do site", só para quem roda Meta. A linha de orgânico vira "Sessões - não pagas".
- Nas linhas calculadas (bloco de resultado, participação, totais), o par Projetado | Realizado vira uma célula só, porque o número já é o realizado onde existe.
- O connect rate passa a ser medido na janela quando há GA4. `--connect-rate` fica só para quando não há como medir.
- Sessões não pagas projetadas usam a média dos meses fechados, porque o mês parcial subestima.
- O gerador sai de `projecao-template/` e entra na skill (`gerador/`), e a skill fica autocontida. Os dados dos clientes continuam fora, em `projecao-template/clientes/`.
- Entram o teste de regressão (`tests/regressao.py`) com dados sintéticos, inclusive um GA4 sintético, e os aprendizados em `referencias/`.
- Começa o versionamento com Git.

## v4 · 17/09/2026 · Revisão do template (varejo de tecidos)

- Nenhuma taxa de etapa passa de 100%: ela é travada com alerta e a causa é explicada. Na varejo de tecidos, os cliques eram só do Google e as sessões somavam Google e Meta.
- `--connect-rate` para informar o connect quando a fonte não permite medir.
- O horizonte vai só até dezembro do ano corrente (`--horizonte`), sem meses do ano seguinte.
- Sai o bloco de quarter. Histórico e envelope vão para a aba Metodologia.
- Ordem da aba: premissas, indicadores, meta, projeção e, por último, os gráficos.
- Gráficos: receita da mídia com crescimento mês a mês, resultado acumulado, payback, participação da mídia e funil.

## v3 · 17/09/2026 · Revisão do template (Destra, RPS, varejo de tecidos)

- O alvo da rampa passa a ser a mediana do período comparável, nunca pior que o atual. O melhor mês inflava a Destra de R$ 322 mil para R$ 1,1 milhão.
- A verba de mídia cresce por percentual mensal com teto (`--crescimento-midia`, `--midia-teto`), o que faz o ROAS variar.
- Resultado consolidado: realizado onde existe, projetado à frente. `--inicio-contrato` define o Mês 1.
- Aba "Metodologia" com fonte, janela, alertas, premissas assumidas e cenário base. Nenhum bloco de instruções na aba do cliente.
- Nenhum azul nas células: amarelo é editável, vermelho-claro é realizado.
- Comissão, GMV e margem só aparecem para quem tem esses elementos. `--margem-informativa` cria uma linha fora do resultado.
- Participação da mídia no faturamento da loja (`--faturamento-total`), com crescimento mês a mês.

## v2 · 17/09/2026 · Nunca só "irrealista"

- Dois cenários: base (taxas atuais constantes) e rampa até o mês de referência, com `alpha` como fração do caminho.
- Status REALISTA, REALISTA COM RAMPA ou IRREALISTA, sempre acompanhado do mês em que o breakeven fica realista.
- `--desde` delimita o período comparável. O mês de referência é o fechado com mais vendas por real de mídia.
- Aba de apoio oculta (`_apoio_<aba>`) para gráficos e KPIs.

## v1 · 17/09/2026 · Integração com o template

- O piloto grava o `premissas.json`, e o gerador preenche o template V4 (inside sales ou e-commerce) com fórmulas vivas.
- Entrevista em ordem: fonte, modelo, fee e mídia confirmados, margem, mês-alvo.
- Cada mês tem colunas Projetado e Realizado. Bloco histórico.
- Janela das taxas: o último quarter fechado, ponderado por volume.
- Primeiros clientes: RPS Revestimentos, Destra Consultoria e varejo de tecidos.

## v0 · Piloto original

- `breakeven_pilot.py` e `SKILL_breakeven_pilot.md` na raiz: taxas efetivas e veredito, sem template.
