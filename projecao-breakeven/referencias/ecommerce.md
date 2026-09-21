# E-commerce: aprendizados e armadilhas

Ler antes de projetar qualquer cliente de e-commerce. Cada item veio de um erro real ou de uma correção do usuário. O caso de referência é o e-commerce de tecidos (setembro de 2026).

## 1. A planilha de indicadores (Growth Pack)

- **O funil fica no bloco GA4, e é do site inteiro.** Sessões, view item, carrinho, checkout e compra aparecem só no bloco "GA4". O bloco Meta tem linhas com os mesmos nomes, zeradas, então o piloto ancora a leitura no rótulo "GA4".
- **A receita atribuída fica em "Receita Captada V4" e "Vendas Captados V4".** Esses rótulos estão nos sinônimos do piloto.
- **Meses antigos podem não servir de histórico.** No e-commerce, de janeiro a julho as conversões do Ads não tinham valor: dezenas de "vendas" com receita de centavos. Aponte isso ao usuário e proponha `--desde`.
- **A verba soma Google e Meta, mas cliques e impressões são só do Google.** É o erro mais caro da fonte. No e-commerce, em agosto, a verba foi R$ 4.353 (R$ 3.534 no Google e R$ 819 no Meta), e os cliques foram 9.241, exatamente os do Google Ads. Consequências:
  - o CPM sai inflado: R$ 41,58 pela fonte contra R$ 33,76 do Google;
  - "Sessões Tráfego V4", que soma as duas plataformas, dividido pelos cliques do Google deu 131% de connect rate.
- **A linha "Sessões Orgânicas" da fonte não é confiável.** Antes da V4 ela vinha negativa (sessões gerais zeradas menos pagas). Com GA4, use as sessões não pagas do GA4.

## 2. GA4: como extrair sem se enganar

Use `scripts/ga4_resumo.py`. Ele já trata as armadilhas abaixo.

- **Corte do mês corrente.** O GA4 tem que ir até o mesmo dia da planilha. Para conferir, compare os cliques do Google Ads no GA4 com a linha de cliques da fonte. No e-commerce, até 17/09 foram 8.933 no GA4 e 8.932 na fonte.
- **O Meta aparece como "Paid Other".** A V4 marca os anúncios como `utm_source=meta_ads / utm_medium=paid`, e o GA4 não reconhece `meta_ads` como rede social. O script classifica como Meta qualquer canal pago com origem meta, facebook, instagram, fb ou ig. Vale sugerir ao time trocar a UTM para `facebook` ou `instagram`, para cair em Paid Social.
- **O Google se espalha em vários canais:** Paid Search, Cross-network (PMax, às vezes sem origem), Display e Paid Shopping.
- **Custo do Google Ads cruzado com mês duplica valores.** Cruzar `yearMonth` com `sessionCampaignName` e `advertiserAdCost` deu R$ 73 mil em agosto, contra R$ 3,5 mil reais. Consulte mês a mês, só com a campanha como dimensão.
- **View item é contado em eventos, não em sessões.** Uma sessão vê vários produtos, então a razão view item ÷ sessões deu 132%. Por isso sessão paga → view item fica em 100% no template.
- **O último clique do GA4 atribui bem menos que as plataformas.** Em agosto, o GA4 deu ao tráfego pago 184 compras e R$ 43 mil. A fonte, com a atribuição das plataformas, deu 310 pedidos e R$ 60 mil. Pedidos e receita ficam sempre da fonte: é o número que a V4 reporta ao cliente.
- **Carrinho e checkout pagos vêm medidos do GA4** (soma dos canais pagos). Sem GA4, o piloto estima esses dois aplicando a proporção do site inteiro às sessões pagas. O produto das taxas entre sessão e pedido é o mesmo nos dois casos, então os pedidos projetados praticamente não mudam. O que muda é que cada etapa passa a mostrar um número real.

## 3. Regras de modelagem

- **O funil corre só sobre as sessões pagas.** As taxas do piloto (carrinho, checkout, pedido) são do tráfego pago. Aplicadas ao total do site, elas transformam orgânico e direto em pedido atribuído à V4. No e-commerce isso deu R$ 91 mil de receita projetada em outubro, contra R$ 50 mil do piloto. As sessões não pagas aparecem como contexto (total do site) e não geram receita. O teste de regressão pega esse erro.
- **Google e Meta ficam separados quando o GA4 permite:**
  - Google: verba → CPM → impressões → CTR → cliques → connect → sessões.
  - Meta: verba ÷ custo por sessão → sessões.
  - Verba Meta = verba da fonte − custo do Google Ads no GA4.
  - A participação do Meta na verba (20% no e-commerce) fica constante na projeção e é premissa amarela.
  - Os blocos só aparecem em cliente que roda Meta com dados separáveis.
- **O connect rate é medido na janela, não num mês.** No e-commerce: 80% em agosto, 98% em setembro (entrada do PMax) e 89% na janela ponderada. Sem GA4, ele é informado com `--connect-rate` (tipicamente 85% a 90%) e registrado como premissa.
- **Nenhuma taxa passa de 100%.** Se passar, o denominador está subcontado: outro canal ou outra fonte. Explique a causa ao usuário, nunca só trave o número.
- **Sessões não pagas = tudo que não é pago:** orgânico, direto, referência, não atribuído e assistentes de IA. A soma com as pagas fecha o total do site. A base projetada é a média dos meses fechados, porque o mês parcial subestima.
- **Checkout → pedido oscila no realizado.** Ele mistura checkout do GA4 com pedido das plataformas (e-commerce: 67% em agosto, 35% em setembro). A projeção usa a média ponderada da janela. Avise o usuário.
- **Critério de breakeven.** Quando o cliente recebe 100% da receita e a margem é baixa (e-commerce, 5%), o usuário usa receita atribuída cobrindo fee + mídia. A margem entra como linha informativa (`--margem-informativa`), fora do resultado.
- **Participação da mídia no faturamento da loja.** O faturamento total vem do Power BI do cliente (`--faturamento-total`). Confira se o valor do mês parcial está atualizado, porque ele envelhece rápido.
- **Crescimento contra mês parcial sai inflado** (e-commerce: +71% de setembro para outubro). Isso fica anotado na Metodologia.

## 4. Caso e-commerce de tecidos, para calibrar a intuição

Os números abaixo são da janela de agosto (fechado) e setembro (parcial até 17/09), com fee de R$ 8 mil e verba de R$ 4.000 crescendo 5% ao mês até R$ 6.000.

| Alavanca | Valor |
|---|---|
| CPM do Google | R$ 19,39 |
| CTR do Google | 6,8% |
| Connect | 89% |
| Meta | 20% da verba, R$ 0,26 por sessão |
| Sessão paga → carrinho | 36% |
| Carrinho → checkout | 14% |
| Checkout → pedido | 49% |
| Ticket | R$ 196 |
| ROAS realizado na janela | 15,9x |
| ROAS projetado, outubro a dezembro | 16,8x a 17,4x |
| Receita da mídia, outubro a dezembro | R$ 74 mil a R$ 85 mil |
| Payback | Mês 1 |
| Acumulado em dezembro | R$ 281 mil |

Se uma projeção nova sair muito longe do ROAS realizado da janela, algo está misturado. Suspeite primeiro de verba e cliques de plataformas diferentes, e de sessões não pagas entrando no funil.
