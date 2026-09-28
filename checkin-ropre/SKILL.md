---
name: checkin-ropre
description: Monta o check-in de cliente no modelo ROPRE (Resultados, Objetivos, Premissas e Riscos, Entregas, Próximos Passos) a partir dos dados brutos do Flow/NECT — CRM, mídia paga, chat conversacional, transcrição de call e WhatsApp. Use sempre que o usuário pedir check-in quinzenal, mensal ou de quarter de um cliente, pedir para montar a apresentação de reunião de resultado, ou perguntar "como fechou o mês do cliente X". Roda o ETL (extrair, transformar, carregar), calcula os cinco blocos e entrega deck .pptx e documento, com a regra de atribuição declarada e o que não foi medido escrito na cara.
---

# Check-in ROPRE

**Versão 1.5 (22/09/2026).** Histórico em `CHANGELOG.md`. Caminhos relativos à pasta da skill
(`.claude/skills/checkin-ropre/`).

O check-in é um ETL, não um relatório escrito à mão:

```
E  extrair/      um adaptador por fonte  →  modelo canônico
T  transformar/  métricas do período, sempre com a mesma definição
L  carregar/     os cinco blocos do ROPRE  →  deck .pptx + documento
```

O contrato entre as três camadas é `transformar/canonico.py`. Enquanto o adaptador devolver o
canônico, trocar RD Station por HubSpot, ou uma planilha pelo Flow, não encosta no check-in.

## Regras que não se negociam

1. **Faturamento lê data de fechamento.** É o que o cliente reconhece como resultado do mês.
   Safra por data de criação responde outra pergunta — "o lead daquele mês virou o quê" — e é a
   leitura certa para eficiência de mídia. As duas aparecem no check-in, nomeadas.
2. **Novo e recorrente andam separados e somados.** A planilha do cliente costuma lançar só a venda
   nova; a recompra fica numa linha à parte e some do total. É a causa número um de "por que tem mais
   venda na apresentação do que na planilha" — e o bloco R já responde isso numa tabela.
3. **A regra de atribuição é declarada, não implícita.** Ela mora no `cliente.json`, viaja junto com
   cada registro e é impressa no deck. Sem regra escrita, o número não é defensável.
4. **O que não foi medido é dito.** Base de mídia parada, evento quebrado, canal sem marcação: vira
   aviso no bloco de fontes, nunca zero e nunca estimativa disfarçada. Métrica que depende de uma
   fonte incompleta sai como "não medido" — foi assim que a skill pegou um ROAS de 37 que vinha de
   aba parada.
5. **Período parcial é marcado como parcial**, e a meta é proporcional aos dias corridos.

## 1. Entrevista (antes de rodar, uma pergunta por vez)

**1.1 Cliente e cadência.** Qual cliente e qual cadência: `quinzenal`, `mensal` ou `quarter`.
Se não existir `clientes/<cliente>/cliente.json`, crie a partir de `clientes/exemplo/cliente.json`
e confirme cada campo com o usuário — fee, verba, margem, funis de venda e de recorrência.

**1.2 Fonte.** Pergunte de onde vêm os dados deste cliente:
- **Flow (padrão)** — `extrair/flow_mcp.py` fala MCP direto com os servidores da V4 (`dados-flow`,
  `bigquery-whatsapp`, `bigquery-calls`, `cockpit` — no V4OS aparecem como Dados Flow, BigQuery ·
  WhatsApp, BigQuery · Ligações e Cockpit Colli). Precisa de `flow.project_document_id` no
  `cliente.json` e das credenciais em `~/.config/v4-flow/mcp.json` (chmod 600).
  Para achar o projeto: `localize_project(search_text="<cliente>")` no `bigquery-calls`.
  **Um cliente pode ter mais de um projeto** — é comum a assessoria e um produto adicional serem
  contratos separados. Pergunte qual entra no check-in; cada projeto tem meta e período próprios.
- **CRM direto** — `extrair/crm_nectarcrm.py`, para o CRM que não está ligado ao Flow.
- **Planilha de mídia** — `extrair/midia_planilha.py`, quando a conexão de mídia do Flow estiver
  quebrada. Vale conferir as duas: já aconteceu de o Flow ter um canal em dia e o outro parado, com a
  planilha no inverso exato — daí `midia.fonte_por_canal`, que dá um dono a cada canal.

**1.3 Margem, fee e verba.** Confirme os três, mesmo que estejam no `cliente.json`. Margem de
contribuição é a pergunta que mais muda veredito: confirme em reais, com uma venda concreta
("numa venda de R$ 10 mil, quanto sobra depois do custo variável?").

**1.4 OKRs do ciclo.** Confirme os key results e a meta de cada um. Cada OKR aponta para uma métrica
do bloco R pelo campo `metrica` (ex.: `receita`, `roas`, `participacao_recorrente`, `entrada_no_crm`),
então o realizado é calculado, não digitado.

**1.5 Calls e conversas.** O `flow_mcp` já traz as calls do período e a atividade do grupo de
WhatsApp. O que ele **não** faz é inferir acordo: veja a seção 3.

**1.6 Entregas.** Pergunte o que a equipe entregou no período e o que está previsto, ou confirme o
que já está em `clientes/<cliente>/entradas/entregas.json`. Entrega sem evidência não entra: cada
item precisa de algo que o cliente possa conferir.

## 2. Rodar

```bash
./gerar.sh exemplo mensal 2026-08-15       # mês fechado
./gerar.sh exemplo quinzenal 2026-09-21    # quinzena corrente (sai marcado como parcial)
```

Saída em `saida/<cliente>/`: `checkin.json` (os números, para conferir), `checkin.md` (documento de
revisão) e `checkin.pptx` (deck; o Google Slides abre e converte).

Passo a passo, quando quiser rodar só uma parte:

```bash
python3 extrair/crm_nectarcrm.py  --cliente clientes/exemplo/cliente.json --saida saida/crm.json
python3 extrair/midia_planilha.py --cliente clientes/exemplo/cliente.json --saida saida/midia.json
python3 carregar/blocos.py --cliente clientes/exemplo/cliente.json \
    --dados saida/crm.json saida/midia.json --cadencia mensal --referencia 2026-08-15 \
    --entradas clientes/exemplo/entradas/entregas.json --saida saida/checkin.json
python3 carregar/documento.py --checkin saida/checkin.json --saida saida/checkin.md
python3 carregar/deck.py      --checkin saida/checkin.json --saida saida/checkin.pptx
```

## 3. Calls e WhatsApp (a parte que é sua)

O `flow_mcp` traz a call e a transcrição; **extrair o acordo é leitura, e isso é com você.** O
circuito:

1. rode `extrair/flow_mcp.py` — cada call vem com `_transcricao`;
2. leia a transcrição e escreva `clientes/<cliente>/entradas/calls.json` com acordos, pendências e
   riscos, no formato de `extrair/conversas_mcp.py`;
3. rode `extrair/conversas_mcp.py` — os acordos viram Próximos Passos, as pendências viram Entregas
   e os riscos entram no bloco P.

**Só entra o que foi dito.** Acordo que você não encontrou na transcrição não vira linha de check-in;
se a call não existe no período, o bloco sai dizendo isso. Nunca infira compromisso do cliente.

## 4. Conferir antes de apresentar

Antes de mandar o deck, leia o `checkin.md` e confira três coisas:

- **a seção "Fontes e o que não foi medido"** — se houver aviso de base incompleta, ou você atualiza
  a base, ou fala do buraco na reunião. Não apresente indicador com lacuna silenciosa;
- **a tabela "Planilha do cliente contra CRM"** — é ela que responde a pergunta do cliente sobre
  divergência de número, antes de ele perguntar;
- **a tabela "Como as vendas do período estão marcadas"** — se a fatia "sem marca" for grande, o
  próximo passo do projeto é corrigir a marcação, e isso é conversa de reunião.

## 5. Publicar

**Dentro da plataforma, o deck não é seu.** Quem renderiza é a skill de design system
(`account-checkin-ropre-v2`): ela tem os tokens, os layouts de 1600×900, o storytelling de
performance e o QA visual. Entregue a ela o check-in aprovado e pare aí. `checkin-colli` prepara
conteúdo para o deck e sobrepõe em parte os blocos 09 a 13 — confirme a divisão antes de duplicar
trabalho. `design-system-pro` só entra se o design system for criado ou refeito.

Dois conteúdos são requisito de layout e não podem ser podados pela diagramação: a **regra de
atribuição escrita por extenso** no bloco de Resultados e a página final de **fontes e o que não foi
medido**.

O que se entrega é o `checkin.json` — um exemplo sem dado de cliente está em
`referencias/checkin.exemplo.json`, e é esse o contrato até as skills de deck dizerem o formato que
esperam. Dentro do V4OS, o workflow inteiro está em `workflow/checkin-ropre.workflow.json`, com as
ferramentas MCP de cada etapa e as instruções de import; a spec legível é `referencias/workflow_v4os.md`.

- **Deck fora da plataforma:** o `.pptx` daqui é fallback. Suba no Drive do cliente e o Google Slides
  converte; o tema da marca se aplica depois.
- **Documento:** o `checkin.md` vira documento vivo quando o usuário quiser comentar e revisar antes
  da reunião.

## 6. Testes

```bash
python3 tests/regressao.py
```

Cobre as regras de leitura de data, atribuição, novo/recorrente, quinzena, mídia incompleta, OKRs,
blocos qualitativos e os dois renderizadores.

Quem opera um cliente real deve manter uma regressão própria, com um mês já fechado e os números
conferidos à mão, em `tests/regressao_cliente.py` — o arquivo fica fora do repositório de propósito.
