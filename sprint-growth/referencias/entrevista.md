# Entrevista: tudo no começo, uma vez

Informação que chega no meio da sprint custa retrabalho: numa sprint de 2026, o token do CRM, os exports do Meta
em partes, o link da projeção, a operação do cliente (atendimento no local × na sede), o escopo e a divisão da
verba chegaram depois dos agentes e obrigaram a refazer resumo, restrições, mídia, plano e régua de MQL. A
entrevista existe para isso não acontecer: pede tudo de uma vez, testa os acessos sozinha e pega primeiro o que
expira.

## Ordem

1. **Memória** (`clientes/<c>/memoria.md`): o que ela responde não se pergunta.
2. **Briefing** (`clientes/<c>/briefing.md`, do modelo em `templates/cliente/`): mande o arquivo ao usuário (ou os
   blocos em lotes de até 4 perguntas na conversa) e grave as respostas. Em branco = pendente, não trava.
3. **Config** (`clientes/<c>/config.json`): IDs e caminhos de chave do bloco 5 do briefing.
4. **Pré-voo**: `python3 scripts/preflight.py --cliente <c> --sprint <SPRINT>`. Testa cada acesso e escreve
   `<SPRINT>/preflight.md` (ok · falta · atenção · manual, com como resolver). Mostre ao usuário só o que falta, numa
   lista única.
5. **Perecíveis primeiro** (tabela abaixo): peça hoje o que expira.
6. **Lacunas**: o que ficou em branco e muda a análise vira pergunta em lote (até 4 por vez, com opção recomendada).
7. Só então o bloco de entrada dos agentes. Frente sem acesso roda com o que houver e escreve "não medido".

## O que expira

| Dado | Janela | Como pedir |
| --- | --- | --- |
| Leads do formulário nativo do Meta | 90 dias na Central de Leads | CSV por formulário, período inteiro da sprint |
| Clarity (Data Export API) | últimas 24–72 h, 10 chamadas por projeto por dia | coletar no dia 1 e todo dia depois |
| Histórico de alterações do Google Ads | 30 dias (`change_event`) | ler no dia 1, antes de qualquer mudança |
| Execuções do n8n | conforme a retenção da instância | ler no dia 1 |

## Formato dos exports (para não chegar em partes)

| Fonte | Formato |
| --- | --- |
| Meta Ads | Gerenciador → Anúncios → colunas: ID da campanha, do conjunto e do anúncio, nomes, gasto, resultados, impressões, cliques no link, CPM, CTR, frequência, classificações de qualidade; **detalhamento por dia**; período inteiro (um arquivo, sem mês repetido) |
| Meta leads | Central de Leads (ou Formulários instantâneos) → baixar CSV de cada formulário do período |
| CRM sem API | todos os negócios do período com etapa, data de criação, data de ganho ou perda, motivo de perda, valor, origem, etiquetas e responsável |
| Construtor de página | leads do período (o construtor guarda mesmo quando a integração falha) |
| Projeção | link da planilha com as abas de premissas e de cenário |

## Perguntas que mudam a análise (não deixe para depois)

- Modalidades de atendimento e logística: definem a qualificação por região (lead longe só serve em uma delas).
- O que o cliente não vende: vira negativa e sai do MQL.
- Ticket por serviço e margem do DRE: sem eles a projeção fica circular (ticket = custo ÷ margem).
- Regra de atribuição e contagem da venda: sem elas o "realizado V4" não existe.
- Critério de MQL vigente: régua que aprova mais de 60% não separa nada.
