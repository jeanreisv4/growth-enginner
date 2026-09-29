# PLG (product-led growth): aprendizados e armadilhas

Ler antes de projetar qualquer produto de assinatura self-serve (SaaS com trial, freemium, plano mensal ou anual).
O caso de referência é a SaaS de diário de obra, SaaS de diário de obra (setembro de 2026), primeiro cliente de assinatura da skill.

## 1. Como rodar

`--modelo plg` no piloto e no gerador. O motor é o do inside sales; o que muda é o vocabulário, o que é obrigatório e o
que a aba mostra.

| Etapa na fonte | Rótulos aceitos | Papel no motor |
|---|---|---|
| Cadastro | Cadastros, Signups, Contas criadas, Leads | lead |
| Trial | Trials, Trials iniciados, Testes grátis, Trial liberado | MQL |
| Ativação | Ativações, Contas ativadas, PQLs (**opcional**) | SQL |
| Assinatura | Assinaturas, Assinaturas novas, Conversões pagas, Vendas | venda |
| Receita | MRR, Receita recorrente, Faturamento V4 | receita |
| Preço | Mensalidade, Mensalidade média, ARPA, Ticket Médio | ticket |

- **Recorrência é obrigatória**: o piloto recusa rodar sem `--churn`. A receita do mês é a base de assinantes ×
  mensalidade, com `base_t = base_(t-1) × (1 − churn_t) + novas_t`.
- **A mensalidade vem da linha da fonte.** Receita ÷ assinaturas novas não é a mensalidade: o MRR é da base inteira e
  infla conforme ela cresce (numa fonte sintética de R$ 199, agosto dava R$ 1.362). A regressão trava isso.
- **Sem a linha de ativação, a etapa fica neutra** (ativações = trials) e aparece como "NÃO MEDIDA" na aba. Nenhuma
  taxa é inventada; a cadeia não muda.
- Atendimento humano, quando existir e for medido fora da planilha padrão: `--conexao-lead` e `--conexao-mql`.

## 2. Perguntas que mudam o resultado

- **Qual plano as vendas reais fecharam, mensal ou anual.** Não use o plano de cima só porque existe. Na SaaS de diário de obra a
  planilha do cliente usava R$ 350 e as duas vendas reais foram Standard Anual, R$ 169.
- **A margem em reais, numa assinatura concreta.** Gross margin de benchmark não é MC1. Na SaaS de diário de obra eu estimei 70%
  (80% de mediana de software menos a Hotmart); a real era **30%**, e o payback de caixa foi de M12 para M29.
- **O churn, e de onde ele vem.** Quase nunca é medido. Sem medição, use a faixa por ACV e escreva que é aproximação.
  Mostre a sensibilidade: na SaaS de diário de obra, a 6% o LTV/CAC dava 1,82x; a 10%, 1,09x.
- **A porta de entrada que o cadastro declarou.** Na SaaS de diário de obra 37% pediam compra direta, sem trial e sem demo, estável
  nos três meses. Cobrar trial e demo de quem já queria comprar inventa etapa no caminho de quem estava com o cartão.
- **Se o atendimento vem antes ou depois da qualificação.** Divida conexões por MQLs mês a mês: passou de 100%, vem
  antes (use a linha `Conexões`); ficou abaixo com folga, vem depois (use `--conexao-*`). Na SaaS de diário de obra vinha depois.

## 3. Regras de modelagem

- **Conta de estrutura antes de qualquer taxa: quantos assinantes ativos o fee exige.** Fee ÷ (mensalidade × MC1).
  Na SaaS de diário de obra, R$ 5.941,81 ÷ R$ 105 = 57 assinantes só para o fee, contra uma base de 2. É ela que segura o caixa.
- **Entregue as duas réguas e diga o que cada uma responde.** CAIXA conta o que entra dentro das colunas e corta cada
  safra na borda do calendário; LTV credita a assinatura pelo que vale até cancelar. As duas partem do mesmo déficit.
  Na SaaS de diário de obra, em 12 meses: caixa −R$ 91,7 mil, LTV +R$ 125,7 mil. A de LTV diz se vale adquirir; a de caixa, quanto o
  contrato consome no caminho. Nunca entregue só uma.
- **Com LTV/CAC abaixo de 1, mais verba aumenta o prejuízo por cliente.** Acima de 1, a verba é o acelerador. E cuidado
  com degraus de verba em assinatura: a verba sobe a régua de "assinantes necessários" mais rápido do que a base cresce.
- **Clique → cadastro mistura mecânicas.** Formulário nativo (Meta) e página (Google) não se parecem: na SaaS de diário de obra,
  10,8% contra 2,5%. Abra por canal antes de mexer na taxa, e prefira rampa até um teto ancorado no histórico do
  próprio canal a um valor chapado desde o mês 1.
- **Vazamento de integração não é taxa.** 57 de 59 cadastros do formulário do Meta não chegavam ao trial. Projetar a
  taxa observada congela o defeito na previsão; o certo é medir quem passa pelo cano que funciona e virar cenário.
- **Horizonte**: quando a pergunta é "quando o caixa vira", o template vai até 18 meses (`--horizonte`, com
  `--rampa-ate` para a rampa não esticar junto).

## 4. Benchmarks (coletados em 29/09/2026)

Resumo de busca: **abra a página antes de citar ao cliente como fonte primária**, como manda a seção 1.6.3.

| Premissa | Faixa | Fonte |
|---|---|---|
| Trial opt-in (sem cartão) → pago | 8% a 22%, mediana 14% | [ChartMogul](https://chartmogul.com/reports/saas-conversion-report/), [Shno](https://www.shno.co/marketing-statistics/free-trial-conversion-statistics) |
| PQL → pago | 25% (contra 9% sem qualificação) | [Gainsight](https://www.gainsight.com/resource/benchmark-product-qualified-lead-pql-conversion-rates/) |
| Ativação | 40%, elite 70%+ | [ProductLed](https://productled.com/blog/product-led-growth-benchmarks) |
| Churn mensal, SMB abaixo de US$ 1k de ACV | 6% a 10% | [Optifai](https://optif.ai/learn/questions/b2b-saas-churn-rate-benchmark/), [ChurnCost](https://churncost.com/b2b-saas-churn-benchmarks-2026) |
| NRR, SMB | mediana 97%, faixa 90% a 105% | [Optifai](https://optif.ai/learn/questions/b2b-saas-net-revenue-retention-benchmark/) |
| Margem bruta de software | mediana 77% a 80% | [Aleph](https://www.getaleph.com/answers/saas-gross-margin-2026), [Benchmarkit](https://www.benchmarkit.ai/2025benchmarks) |
| Landing page B2B SaaS → lead | 2% a 5%; self-serve 4% a 10%; topo 8% a 15% | [First Page Sage](https://firstpagesage.com/seo-blog/b2b-landing-page-conversion-rates/), [daydream](https://www.withdaydream.com/library/insights/average-landing-page-conversion-rate) |

## 5. Caso, para calibrar a intuição

**SaaS de diário de obra** (29/09/2026). Planos Standard R$ 209/mês (anual 169) e Plus R$ 350 (anual 309), checkout na Hotmart, trial
de 7 dias sem cartão. Fee R$ 5.941,81, margem real 30%, churn 6% (benchmark, não medido), base atribuível de 2.
Plano entregue: plano Plus, fluxo do Meta ligado (atendimento de MQL de 52,4% para 95,7%), trial → assinatura 25%,
clique → cadastro 6,88% (Google a 3,5% e 60% da verba no Meta), verba de R$ 5 mil a R$ 12 mil em degraus, 14 meses.
Resultado: caixa no azul em out/2027 (+R$ 472) e acumulado zerando em jan/2029; por LTV, no azul em out/2026 e
acumulado zerado em jan/2027. LTV R$ 1.750, CAC R$ 960, LTV/CAC 1,82x. O fee consome 75% da margem gerada no ano:
a conversa com o cliente é de estrutura (fee, remuneração atrelada à base, prazo de contrato), não de mídia.
