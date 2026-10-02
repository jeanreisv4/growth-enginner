# Armadilhas: o que já deu errado e como a skill evita

Leia antes de qualquer projeção. Cada item tem o caso que o originou e a regra que ficou. Os casos de calibragem por
modelo estão em `inside_sales.md`, `ecommerce.md` e `plg.md`.

## Entrega

1. **Entregar só cenários que não fecham.** Na fábrica de acessórios de cortina saíram pessimista, desejado, otimista e meta, todos sem
   breakeven, e o usuário teve de perguntar "qual bate?". Regra (v8.3): toda projeção sai com a aba **Breakeven**,
   montada sozinha pelo `cenario_breakeven.py` — funil de mercado onde o cliente está abaixo, verba em degraus,
   recompra e, se nada fechar, a conversa de estrutura. Se o usuário precisa perguntar o que bate, a skill falhou.
2. **Usar só o histórico do próprio cliente para dizer que não fecha.** Pessimista, desejado e otimista andam dentro do
   envelope do cliente; com a verba de hoje e a mídia devolvendo menos de R$ 1 por R$ 1, nenhum deles fecha por
   construção. Antes de dizer "irrealista", compare etapa por etapa com o mercado (`mercado_alavancas.json`): na fábrica de acessórios de cortina
   três etapas estavam acima do mercado e duas abaixo (clique → lead 4,3% contra 8,2%; MQL → SQL 20% contra 42%). O
   breakeven mora nas etapas abaixo.
3. **Verba só ajuda quando a mídia se paga.** Com margem por R$ 1 de mídia abaixo de 1, mais verba aumenta o prejuízo
   (indústria química B2B: R$ 0,07). A ordem é: funil primeiro, verba depois. A fábrica de acessórios de cortina no nível conservador de mercado só fechava com
   R$ 14 mil de verba; no nível de mercado, com R$ 4 a 6 mil; com recompra, com os R$ 2 mil de hoje.
4. **Recompra fora da projeção principal.** Cliente que vende para quem repõe estoque (lojista, distribuidor, insumo,
   químico) tem recompra pelo modelo de negócio. Ela não é "cenário otimista": entra na projeção principal com
   `--recompra INTERVALO,VIDA[,FATOR]`, como premissa escrita e editável, e vira a primeira coisa a medir. Na fábrica de acessórios de cortina,
   reposição trimestral por 12 meses tirou a restrição de "estrutura" para "funil" e fez o otimista fechar.
5. **Uma leitura só do déficit.** Com legado (o contrato inteiro) e sem legado (daqui para frente) respondem perguntas
   diferentes: a primeira diz se o contrato se paga, a segunda se continuar vale a pena — o que já foi gasto não volta.
   Entregue as duas (`--sem-legado`), sem legado na frente, e cada uma procura a própria verba no Breakeven: a mesma
   verba nas duas deixava a leitura com legado sem zerar.
20. **Repetir o desejado na aba Breakeven quando o plano já bate.** Na brindes corporativos B2B setembro (7 vendas, R$ 26 mil)
    bastava para o desejado fechar, e a aba Breakeven saiu igual ao desejado com 18 meses, R$ 224 mil de acumulado e
    "3,5x o melhor mês". Regra (v8.5): quando o plano já bate, a aba mostra o **piso** — até onde SQL → venda e ticket
    podem cair e a conta ainda zera no prazo, com e sem a recompra. Projeção apoiada num mês só pede piso, não teto.
21. **Sazonalidade crua sobre base de pico.** O índice do Google Trends é relativo à média do ano; se o funil vem de
    setembro (índice 1,22 em brindes corporativos), aplicar outubro 1,57 conta o pico duas vezes. Divida pelo índice do
    mês-base.

## Fonte

6. **Linha copiada de outra.** Na fábrica de acessórios de cortina, "Conexão (manual)" repetia a linha de SQLs mês a mês. Compare as linhas do
   funil entre si antes de aceitar: linha idêntica a outra não é medida — vira premissa de mercado (`--premissa-mercado`)
   ou sai da cadeia.
7. **Bloco por plataforma com fórmula quebrada.** O bloco do Meta da fábrica de acessórios de cortina dava MQL → SQL de 600% e 1.900% e o CTR
   repetia a taxa de conversão. Use o consolidado (Indicadores V4) e confira que a soma dos blocos bate com ele.
8. **Growth Pack que soma linhas de produto.** Na indústria química B2B a verba misturava lavanderia, institucional e domissanitários:
   a mídia veio da API por campanha.
9. **Venda sem valor.** Maio da fábrica de acessórios de cortina teve 1 venda e R$ 0. Pergunte; quando a venda é real, o usuário pediu o ticket
   médio das demais (R$ 1.876,62), registrado nas observações.
10. **Data do primeiro lead não é o início do contrato.** A planilha de leads da indústria química B2B começava em mai/26; o contrato,
    em mai/25. Pergunte o início e peça a projeção anterior antes de calcular o déficit.
11. **Projeção anterior lida pelo que diz, não pelo que lembram dela.** O usuário achava que a projeção antiga da
    fábrica de acessórios de cortina "estava num breakeven"; ela dizia NÃO BREAKEVA, com margem de 20% e verba de R$ 400 (o realizado foi
    R$ 1,9 mil). Mostre as premissas dela ao lado das atuais no bloco projetado × realizado.

## Custo de mídia

19. **Canal que sai do plano sai também do histórico.** No escritório de arquitetura o Q4 é só Meta: a fonte passou a
    ser o bloco do Meta (investimento, impressões, cliques e leads do Meta), o Google saiu do legado (R$ 1.200) e os
    leads de setembro que não eram do Meta também — o clique → lead da campanha atual caiu de 12,0% para 9,5%. Funil
    abaixo do lead (MQL, SQL, venda) segue o consolidado quando o canal que saiu não teve gasto no período.

12. **Mudança de mix entre canais muda o CPM inteiro.** A fábrica de acessórios de cortina saiu de quase todo Meta (CPM R$ 8 a R$ 18) para 75%
    Google (CPM combinado R$ 63). Mediana do período nesse caso puxa o CPM para um patamar que não volta com a divisão
    atual: fixe CPM, CTR e clique → lead na campanha atual (`--fixar`) e deixe o resto do funil usar o período longo.

## Mecânica (bugs que já aconteceram)

13. **Dia 1 do mês.** O mês corrente sem nenhum investimento era tratado como realizado zerado e zerava a "receita
    necessária para zerar o mês". Mês corrente sem investimento é futuro.
14. **Nome de aba com mais de 31 caracteres.** O Excel corta; "Premissas · Pessimista sem legado" perdia o fim que
    distingue as abas. Nome longo vira "Prem. · <aba>".
15. **Gráfico que mistura calendários.** Abas com Mês 1 em mai/26 e em out/26 no mesmo gráfico de acumulado põem meses
    diferentes no mesmo ponto: o gráfico só junta abas do mesmo calendário.
16. **Restrição que ignora a recompra.** A margem por R$ 1 de mídia contava só o primeiro pedido e dizia "retorno da
    mídia abaixo de 1" com recompra na projeção. Com recompra, conta a vida do cliente.
17. **Trava do melhor mês com recompra.** O melhor mês realizado só tem clientes novos; com recompra a projeção passa
    dele por construção. O alerta continua, mas diz de onde vem a diferença (funil, verba, recompra).
18. **Vocabulário de assinatura em cliente B2B.** O motor da assinatura escreve "MRR", "assinante", "churn"; em recompra
    use `--vocabulario recompra` (o `tres_cenarios.py` põe sozinho quando alguma aba usa recorrência).
