# Comercial e receita

**Leitura:** CRM pela API (`scripts/datacrazy.py` e equivalentes) e o realizado oficial. **Escrita:** o processo é
do time do cliente. A correção vira recomendação no 5W1H com dono, prazo e a métrica que prova; a V4 aplica só o
que é automação no CRM, com ok.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| V1 | Tempo até o primeiro contato (mediana e p75) | comercial | histórico do lead (`datacrazy.py historico`) | horas ou dias até falar com o lead | alta |
| V2 | Follow-up: leads sem contato e quem pediu compra sem atendimento | comercial | último contato registrado | 7 pedidos de assinatura sem ninguém falar | alta |
| V3 | Lead novo separado de cliente antigo | comercial | `datacrazy.py resumo` | recompra da base escondendo o fechamento do lead novo | alta |
| V4 | Motivos de perda, mês a mês, antes e depois do orçamento | comercial | motivos pela API | "sem retorno" dominando; motivo em branco | média |
| V5 | Tempo de cada etapa por safra e vendedor | comercial | histórico de etapas | etapa parada; vendedor muito acima dos outros | média |
| V6 | Capacidade do time × volume de leads | comercial | leads por vendedor × vendas | mais lead não vira mais venda | alta |
| V7 | Atendimento automático (IA) com segundo toque | comercial | etapa da IA e tempo parado | 77 negócios parados em "Ativado IA" | média |
| V8 | Abordagem e qualificação (roteiro, perguntas) | comercial | amostra de conversas | vendedor não pergunta o que qualifica | média |
| V9 | Disciplina de registro no CRM | comercial | negócio nascendo em orçamento; ganho em 1 min | CRM como registro, não processo | média |
| V10 | Receita por data de fechamento, novo × recorrente, piso quando parcial | comercial | CRM ou lista de assinantes | receita extrapolada de fonte incompleta | alta |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-V1 | Tempo máximo para o primeiro contato, com alerta no CRM | V1 | recomendação + automação do CRM | tempo atual mostrado ao cliente | R1 | desligar o alerta | mediana até o primeiro contato na próxima sprint |
| CX-V2 | Lista de follow-up entregue ao time, com cadência | V2 | lista do CRM (sem dado pessoal no documento) | lista revisada | R1 | — | leads da lista contatados em 7 dias |
| CX-V3 | Separar os funis (ou etiquetas) de lead novo e cliente antigo | V3 | configuração do CRM ou regra de análise | regra escrita na memória | R2 | — | taxa do lead novo medida à parte |
| CX-V4 | Motivo de perda obrigatório e com lista fechada | V4 | configuração do CRM | lista de motivos | R1 | tornar opcional | motivo em branco = 0 |
| CX-V5 | Revisão da etapa parada com o gestor | V5 | recomendação com os números | — | R1 | — | tempo da etapa na próxima sprint |
| CX-V6 | Não subir verba antes de o fechamento voltar; ajustar capacidade | V6 | recomendação (TOC: subordinar a mídia) | conta de capacidade | R1 | — | taxa de fechamento do lead novo |
| CX-V7 | Segundo toque automático e passagem para humano | V7 | automação do CRM ou da IA | mensagem aprovada | R2 | desligar | negócios parados na etapa da IA |
| CX-V8 | Roteiro de qualificação com as perguntas que separam o lead bom | V8, M3 | recomendação + material | roteiro aprovado | R1 | — | taxa de SQL por vendedor |
| CX-V9 | Regra de registro: todo negócio nasce no começo do funil | V9 | recomendação + validação no CRM | regra escrita | R1 | — | negócios nascendo em orçamento = 0 |
| CX-V10 | Fonte de receita definida (CRM ou lista) e piso declarado | V10 | memória do cliente + documento | fonte confirmada com o cliente | R1 | — | receita do mês com fonte |
