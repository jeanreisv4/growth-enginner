# Histórico da skill projecao-breakeven

Cada versão muda o que o cliente vê. Antes de publicar uma versão nova, rode `python3 tests/regressao.py`.

## v7.0 · 21/09/2026 · Modelo padrão de dados e entrevista por frente contratada

- **Regra do modelo padrão:** a aba de projeção mostra a cadeia padrão com o valor usado no mês; premissa que varia (CPM com saturação, multiplicadores de eleição, datas e remarketing, sazonalidade de demanda) não vira linha na projeção. A decomposição vai para a aba Premissas, em tabela mês a mês. A sazonalidade da demanda passou a entrar na taxa de SQL → venda usada no mês, com a tabela "Sazonalidade da demanda mês a mês" na aba Premissas.
- **Entrevista:** novas perguntas de 1.0 (frentes contratadas e o que o fee cobre), 1.3.1 (custo de mídia da campanha atual, saturação do CPM com a escala, fatia de remarketing, eleição e datas), 1.5.1 (prazo do cliente e cenário-meta em aba extra), 1.5.2 (capacidade da operação: contatos e vendas por mês) e 1.6.3 (sazonalidade do produto pelo Google Trends e IBGE; oferta não entra sem dado).
- **Premissa mais dura que ainda fecha:** quando o usuário pede uma premissa mais conservadora, mostre a faixa com o mês de payback de cada valor e pare no mais duro que ainda fecha; os extremos ficam como sensibilidade.

## v6.5 · 19/09/2026 · Cenário extra em outra aba (loja de multimídia automotiva)

- Gerador com `--extra "premissas.json|Aba|Cenário|metodologia.json"` (repetível): cada cenário vira uma aba de projeção no mesmo arquivo, com a própria aba de premissas. loja de multimídia: "Inside Sales" (plano base, payback em jul/2027) e "Cenário Dezembro" (acumulado zerado em dez/2026).
- Com cenários extras, o gráfico "Resultado acumulado mês a mês" de cada aba de projeção mostra também as linhas das outras abas (plano base × cenários), para o payback de cada um aparecer no mesmo gráfico. O usuário queria ver o acumulado do cenário nos gráficos da aba principal, não o resultado do mês nem o faturamento.
- `metodologia_mercado.py` aceita "taxas" e "justificativas" por premissa no analise.json, para a tabela de benchmarks mostrar as taxas do cenário.
- Regressão com caso de aba extra.

## v6.4 · 19/09/2026 · Aba Premissas, CPM ao longo do ano e visão de 12 meses (loja de multimídia automotiva)

- A aba "Metodologia · <aba>" passa a se chamar "Premissas · <aba>", a pedido do usuário.
- Inside sales: "Custo total (fee V4 + mídia)" sobe para logo abaixo de fee e mídia.
- Piloto com `--cpm-crescimento`, `--cpm-teto` e `--cpm-crescimento-ate`: o CPM base cresce mês a mês (saturação do público) até um mês ou teto. Na planilha, com sazonalidade de CPM, aparecem "CPM base", "Multiplicador do CPM (eleição, datas, remarketing)" e "CPM efetivo".
- A pedido do usuário, a projeção mostra só a linha "CPM", já com o CPM usado no mês (base × multiplicador). A decomposição (base com saturação, multiplicador e CPM usado) fica numa tabela mês a mês na aba Premissas, como explicação para o cliente.
- Benchmarks: eleição de 2026 (TRE-RJ, CNN 2022), remarketing (Lebesgue, AdRoll, Metadata), CPM por data (Superads, Bïrch) e sazonalidade de demanda de 12 meses pelo Google Trends.

## v6.3 · 19/09/2026 · Sazonalidade, ROAS e retorno após a margem (loja de multimídia automotiva)

- Piloto com `--sazonalidade-demanda` e `--sazonalidade-cpm`: multiplicadores mês a mês de vendas e de CPM (Black Friday, Natal). Na planilha viram linhas editáveis ("Sazonalidade do CPM" e "Sazonalidade da demanda") que entram nas impressões e nas vendas geradas.
- Inside sales ganha a cascata de retorno: ROAS (receita ou faturamento ÷ mídia), ROAS de breakeven ((fee + mídia) ÷ mídia ÷ margem), retorno dos anúncios após a margem (MC − mídia), ROI da mídia após a margem e o resultado depois do fee V4.
- Benchmarks: sazonalidade de central multimídia pelo Google Trends (2021–2025), Neotrust, Cielo, NielsenIQ e NRF; conferência do MQL → SQL.
- Regressão com caso de sazonalidade.

## v6.2 · 19/09/2026 · Dados de mercado quando o histórico é curto (loja de multimídia automotiva)

- Piloto com `--alvo alavanca=valor`: o alvo da rampa vem de benchmark de mercado nas etapas sem histórico suficiente, nunca pior que o atual, com alerta. `--alvo conexao=0.69` (inside sales com Conexões na fonte) sobe lead → MQL na proporção da conexão e grava a conexão mês a mês.
- Planilha: a conexão lead vira linha mês a mês quando tem alvo de mercado; o envelope marca as alavancas com "alvo de mercado"; a Curva da projeção descreve a verba em degraus e os alvos de mercado.
- Novo `scripts/metodologia_mercado.py` e `referencias/multimidia_automotiva_benchmarks.json` (9 premissas, 24 fontes verificadas em 18 e 19/09/2026: Foureyes, HBR, RD Station, First Page Sage, WordStream, Superads, IBGE PAC e PMC, Damodaran, amostras de preço).
- Regressão com caso de alvo de mercado.
- Benchmarks de CPM, CTR de link e clique → lead no Brasil e no setor (Superads, LocaliQ, PTAX do BCB). A skill passa a exigir o custo de mídia da campanha atual e o estresse de CPM ao escalar a verba.

## v6.1 · 18/09/2026 · Conexão só de lead e receita própria (loja de multimídia automotiva)

- Gerador com `--conexao-so-lead`: quando a linha Conexões conta só leads conectados, a conexão lead vem da fonte e a de MQL fica em branco para preencher, sem taxa suposta. O funil segue MQL → SQL e o realizado de MQL conectado fica aberto.
- Cliente com receita própria (comissão 1, sem CRM): saem as linhas de comissão e "receita da agência". A linha de faturamento vira "Faturamento (vendas × ticket)", o cartão de GMV sai e a meta pede faturamento, não GMV. consultoria e varejo de revestimentos também mostravam "comissão 100%".
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

- A entrevista pede a margem com uma venda concreta ("numa venda de R$ X, quanto sobra?"). A agência de viagens passou por três leituras de margem (6%, 20%, 3%) antes da confirmação em reais.

## v5.3 · 18/09/2026 · Planilha até o payback (agência de viagens)

- O piloto usa o realizado dos meses já vividos no veredito, como a linha consolidada da planilha. Antes, a agência de viagens tinha setembro projetado em −R$ 8,9 mil e realizado em +R$ 1,8 mil, e o piloto dizia payback em ago/27 enquanto a planilha dizia mai/27. `--inicio` alinha o Mês 1 quando ele é o início do contrato.
- `--rampa-ate` separa o fim da rampa do mês-alvo. A planilha pode ir até o mês do payback sem que a rampa fique mais lenta e mude os números.
- Regra de horizonte: até dezembro por padrão. Quando o acumulado só zera depois, a planilha é estendida até esse mês, a pedido do usuário.

## v5.2 · 18/09/2026 · Duas datas no veredito e verba em degraus (agência de viagens)

- O veredito sempre responde "em que mês fica realista", mesmo depois do horizonte: **no azul a partir de** (todo mês seguinte com resultado ≥ 0) e **acumulado zera em** (payback). As duas datas consideram o realizado dos meses vividos e a projeção por 48 meses. Aparecem no subtítulo, na Metodologia e num cartão novo, e a tabela ganha as linhas "Mês no azul?" e "No azul daqui até o fim?".
- `--verba-plano` define a verba mês a mês, em degraus. Na planilha, cada mês fica editável, e crescimento e teto saem das premissas.
- Inside sales: quando a comissão já é a margem da agência (margem 100%), a linha de margem sai e a comissão vira "margem da agência".
- O subtítulo mostra o período real (ex.: set/2026 a dez/2026) em vez de "12 meses".

## v5.1 · 18/09/2026 · Caminho para o breakeven (agência de viagens)

- **Correção:** uma etapa opcional sem nenhum valor passa a contar como ausente. Na agência de viagens, o piloto achava a linha "Conexões" vazia do bloco Meta e zerava o funil inteiro.
- O piloto calcula o **caminho** quando a meta não fecha: quanto cada alavanca precisaria, sozinha, para o mês-alvo fechar no zero, e se isso já aconteceu num mês fechado. Mais o fee que fecharia, a margem por real de mídia, a verba que cobriria o fee e o primeiro mês positivo sem teto. O gerador leva isso para a seção "Caminho para o breakeven" da Metodologia.
- `--fixar alavanca=valor` fixa uma etapa quando a campanha mudou no meio da janela. O alerta fica registrado.
- O template de inside sales deixa de mostrar linhas que o cliente não tem: connect, visitas e landing page (a planilha padrão não mede) e as linhas de conexão, quando a fonte não tem "Conexões". A demo mantém todas.
- O teste de regressão ganha um caso irrealista, que exige a seção do caminho e confere que as linhas de landing page não aparecem.

## v5 · 18/09/2026 · GA4, funil pago e versionamento

- **Correção:** o funil de e-commerce passa a correr só sobre as sessões pagas. Antes, as sessões orgânicas passavam pelas taxas do tráfego pago e inflavam a receita atribuída. No e-commerce, outubro aparecia com R$ 91 mil, contra R$ 50 mil do piloto.
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

## v4 · 17/09/2026 · Revisão do template (e-commerce)

- Nenhuma taxa de etapa passa de 100%: ela é travada com alerta e a causa é explicada. No e-commerce, os cliques eram só do Google e as sessões somavam Google e Meta.
- `--connect-rate` para informar o connect quando a fonte não permite medir.
- O horizonte vai só até dezembro do ano corrente (`--horizonte`), sem meses do ano seguinte.
- Sai o bloco de quarter. Histórico e envelope vão para a aba Metodologia.
- Ordem da aba: premissas, indicadores, meta, projeção e, por último, os gráficos.
- Gráficos: receita da mídia com crescimento mês a mês, resultado acumulado, payback, participação da mídia e funil.

## v3 · 17/09/2026 · Revisão do template (consultoria, varejo de revestimentos, e-commerce)

- O alvo da rampa passa a ser a mediana do período comparável, nunca pior que o atual. O melhor mês inflava a consultoria de R$ 322 mil para R$ 1,1 milhão.
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
- Primeiros clientes: varejo de revestimentos, consultoria B2B e e-commerce de tecidos.

## v0 · Piloto original

- `breakeven_pilot.py` e `SKILL_breakeven_pilot.md` na raiz: taxas efetivas e veredito, sem template.
