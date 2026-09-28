# ROPRE, bloco a bloco

Referência do que entra em cada bloco do check-in. A estrutura é a do template da V4
(`[Dispara AI] Check-in Quarter`), adaptada para funcionar com qualquer modelo de negócio —
o template original é de e-commerce, e a maior parte dos clientes de inside sales não tem
taxa de conversão de site nem carrinho abandonado.

O que muda entre modelos é o conteúdo do **R**. A espinha dos cinco blocos não muda.

---

## R · Resultados

Responde "o que aconteceu no período". Sempre contra o período anterior de mesmo tamanho.

| O que entra | De onde vem | Cuidado |
| --- | --- | --- |
| Receita, vendas, ticket | CRM, por data de fechamento | não misturar com data de criação |
| Novo × recorrente | funil de recorrência do CRM | a planilha do cliente costuma lançar só o novo |
| Investimento, CPL, CTR, ROAS, CAC | plataformas de mídia | só sai com a base completa no período |
| Entrada no CRM | leads da plataforma ÷ contatos criados | mede vazamento entre mídia e comercial |
| Meta e resultado do período | fee + verba ÷ margem | proporcional aos dias em período parcial |
| Eficiência por safra | negócios criados no mês ÷ gasto do mês | é a leitura que isola o efeito da mídia |
| Por canal | canal marcado no CRM | quase sempre parcial; publicar a cobertura junto |
| Como as vendas estão marcadas | regra de atribuição | é o que sustenta o número na reunião |

**Inside sales** troca taxa de conversão de site por: leads, entrada no CRM, MQL, SQL, taxa de ganho
entre resolvidos e tempo de ciclo. **E-commerce** mantém sessão, carrinho, checkout e pedido.

## O · Objetivos

Objetivo SMART do ciclo, os key results com realizado ao lado, e o step do projeto.

- cada KR aponta para uma métrica do bloco R (`metrica` no `cliente.json`), então o realizado é
  calculado — não digitado;
- status: ✅ atingido, ⏳ dentro da tolerância, ❌ fora, — sem dado;
- o que foi **acordado com o cliente nas calls** do período entra aqui, extraído das transcrições.

## P · Premissas e Riscos

Premissa é o que o check-in assume como verdade: margem, verba, regra de atribuição, escopo. Toda
premissa carrega origem ("confirmada com o cliente em 21/09", "contrato", "a confirmar").

Risco segue o formato do template: **causa → risco → efeito**, com probabilidade × impacto.
Três fontes alimentam o bloco: os riscos cadastrados no `cliente.json`, os levantados nas calls e os
que o próprio dado denuncia (base de mídia parada, entrada no CRM abaixo de 80%).

## E · Entregas

Realizadas, previstas e pendências abertas. Entrega precisa de evidência que o cliente possa
conferir. Pendência vem de duas fontes automáticas: conversa de WhatsApp com pendência em aberto e
compromisso não fechado em call.

Horas dedicadas ao projeto entram aqui quando o time controla.

## E · Próximos Passos

O que vem, com dono e prazo. Sai de duas origens: o que a equipe planejou e o que foi acordado na
call. Passo sem dono é passo que não acontece — quando o dono não estiver claro, o campo vai como
`a_confirmar` e isso aparece no deck.

---

## Cadências

| Cadência | Para que serve | Profundidade |
| --- | --- | --- |
| Quinzenal | ritmo e desvio: dá tempo de corrigir dentro do mês | R e E completos; O e P só se mudou algo |
| Mensal | o check-in de resultado | os cinco blocos |
| Quarter | fechamento e repactuação de meta | os cinco blocos + comparativo entre quarters |

O período parcial sempre sai marcado, e a meta é proporcional aos dias corridos — quinzena não se
compara com meta mensal.
