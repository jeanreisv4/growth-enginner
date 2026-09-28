# Histórico da skill checkin-ropre

Cada versão muda o que o cliente vê no check-in. Antes de publicar uma versão nova, rode
`python3 tests/regressao.py`.

## v1.5 · 22/09/2026 · Os servidores com o nome que têm no V4OS

O painel *Ferramentas deste chat* do V4OS mostrou os servidores como eles aparecem lá dentro, e
resolveu duas dúvidas de uma vez.

- **`servidores` no JSON**: a chave usada aqui, o nome no V4OS (Dados Flow, Cockpit Colli, BigQuery ·
  Ligações, BigQuery · WhatsApp, eKyte, V4 OS, Catálogo de Produtos), o que cada um responde, o tipo
  de acesso e as etapas que o chamam. A validação confere que toda ferramenta aponta para um servidor
  da lista e que a lista bate com as etapas.
- **eKyte existe e está ligado** — cai a pendência de servidor e credencial; ficam só os nomes das
  ferramentas de entregas e horas.
- **V4 OS é um servidor** ("obrigatório para o contexto do projeto"): a etapa 01 passa a resolver o
  projeto por ele, com `localize_project` e `cockpit_list_projects` como caminho pelo nome, e vira
  etapa que chama ferramenta. A busca do projeto sai da 05.
- **Dados Flow e Catálogo de Produtos usam token pessoal do Flow e vêm desligados no chat** — nova
  pendência para quem roda. E o aviso do painel virou instrução de import: o que se liga no chat não
  altera workflows; cada etapa liga os seus.

## v1.4 · 22/09/2026 · O JSON passa a bastar para quem constrói dentro do V4OS

Revisão feita do lugar de quem recebe o repositório lá dentro e precisa montar o workflow sem
perguntar nada. O que faltava estava todo no Python, não no JSON.

- **Cada etapa que chama ferramenta diz qual.** Campo `ferramentas` por etapa, com servidor, nome,
  parâmetros e os cuidados que já custaram número errado: `account_id` sem `act_` e com aspas
  simples, `UNNEST` bloqueado, paginação de 100 sem metadado (descartar a contagem se bater no
  teto), `endLt` exclusivo, `granularity: monthly`, parâmetros de calls e WhatsApp como string.
  Antes, isso só existia dentro de `extrair/flow_mcp.py`.
- **As leis viajam com a etapa.** `leis_aplicaveis` em cada etapa e a instrução de import de
  prefixar o briefing com elas — o README já dizia que regra fora do briefing não chega ao agente,
  e o JSON fazia o contrário.
- **Entradas e saídas do workflow declaradas** (`entradas_do_workflow`, `saidas_do_workflow`): o
  que não mora em sistema nenhum da plataforma — regra de atribuição, funis, margem, fee, OKRs —
  entra como formulário, não como pergunta no meio do caminho.
- **O contrato de handoff tem um exemplo real.** `referencias/checkin.exemplo.json`, gerado da
  fixture sintética pelo `render_spec.py`, é o que a etapa 15 entrega à 16 até as skills de deck
  dizerem o formato que esperam.
- **Instruções de import e pendências no próprio JSON** (`instrucoes_de_import`): o arquivo é a
  especificação neutra, não o export do Studio; sete passos para o harness materializar, e a lista
  do que só quem está dentro da plataforma responde — cada pendência com o fallback escrito na etapa
  (ekyte sem credencial → entregas entram à mão; cockpit sem ferramenta de health → a etapa diz que
  não há sinal; calls vazias → o bloco diz que não houve).
- **`render_spec.py` valida o JSON** antes de gerar: etapa que chama ferramenta sem nomeá-la,
  conexão para etapa inexistente, lei fora do intervalo e etapa solta param a geração. A regressão
  roda a mesma validação.
- Ajustes: a etapa 03 puxa do `dados-flow` (o Nekt é quem alimenta, não quem responde); a integração
  com `account-checkin-ropre-v2` recebe da etapa 15 pela 16, não da 14; a versão no `SKILL.md`
  acompanha o changelog.

## v1.3 · 22/09/2026 · A fronteira com o design system, e o grafo até o deck publicado

- **A etapa 15 deixa de desenhar slide.** Dentro da plataforma, o deck é renderizado pela skill de
  design system da companhia (`account-checkin-ropre-v2`), que já tem tokens, layouts de 1600×900,
  storytelling de performance e QA visual. A etapa passa a **entregar o check-in aprovado** para ela.
- **As integrações ficaram declaradas no JSON do workflow** (`integracoes_da_plataforma`), com papel,
  relação e o contrato de entrada de cada uma — os marcados como *a confirmar* são o que falta para o
  encaixe ser automático. `checkin-colli` sobrepõe em parte os blocos 09 a 13 e a divisão precisa ser
  fechada para não haver etapa duplicada.
- **Dois conteúdos viraram requisito de layout**, e não preferência: a regra de atribuição escrita por
  extenso no bloco de Resultados e a página final de fontes e do que não foi medido.
- **O grafo passou a ir até o deck publicado**, com quatro etapas novas que rodam em outra skill:
  16 preparar o conteúdo (`checkin-colli`), 17 compilar as páginas no design system, 18 QA visual e
  19 publicar e entregar (as três últimas em `account-checkin-ropre-v2`). São 19 etapas e 27
  conexões, e o diagrama separa em dois subgrafos quem executa o quê — o trecho do deck sai
  pontilhado, com o nome da skill dentro do nó.
- **O que o check-in cobra do trecho de deck virou briefing**, não recado: número não se recalcula na
  diagramação, "não medido" não vira travessão nem some por falta de espaço, e o QA visual confere
  também conteúdo — todo número do deck existe no check-in aprovado.
- O renderizador `.pptx` continua como **fallback para fora da plataforma**.

## v1.2 · 22/09/2026 · O workflow vira arquivo, e o arquivo vira a documentação

- **`workflow/checkin-ropre.workflow.json` é a fonte da verdade** do check-in como workflow de
  agentes: 15 etapas com briefing, entradas, saídas e a marca de quem chama ferramenta, mais as 23
  conexões e as quatro leis. É este arquivo que se importa na plataforma.
- **`workflow/render_spec.py` gera a documentação a partir dele** — a especificação completa em
  `referencias/workflow_v4os.md`, o diagrama mermaid e os blocos do README. Documentação e arquivo de
  import não podem divergir porque não são escritos duas vezes.
- **README reescrito em torno do workflow**: o desenho em diagrama, a tabela das etapas, as leis, e o
  motivo de a etapa de cobertura vir antes do cálculo. A implementação em Python passa a ser
  apresentada como referência, não como o produto.
- **Duas seções novas no README**: *De onde vêm os dados*, com os servidores MCP da plataforma, o que
  o pipeline de ingestão entrega por domínio (CRM, mídia paga, analytics, e-commerce, operações,
  social) e onde cada fonte entra no ROPRE; e *O que o ETL faz*, explicando extrair, transformar e
  carregar em prosa — normalização para o modelo canônico, cobertura antes da conta, e as duas saídas
  vindas do mesmo pacote.

## v1.1 · 22/09/2026 · Flow ligado de verdade (MCP) e cobertura de fonte por canal

- **`extrair/flow_mcp.py` substitui o adaptador REST hipotético.** Os servidores do Flow falam MCP
  sobre HTTP (JSON-RPC + SSE), então o adaptador fala MCP direto: o ETL roda em cron ou terminal,
  sem depender de estar dentro de uma sessão do Claude. Traz mídia por dia e canal, metas do
  período, atividade do grupo de WhatsApp e as calls.
- **Mídia por SQL, leads por paginação com teto.** `flow_media_query` devolve custo, impressões e
  cliques por dia numa chamada só e exata. `flow_media_conversion_summary` desempacota os leads, mas
  devolve linha por anúncio e por dia, no máximo 100 por página e sem metadado de paginação — pedir
  500 truncava em silêncio. Agora pagina de 100 em 100 com teto e, se bater no teto, **descarta a
  contagem** em vez de publicar subcontagem.
- **Fonte por canal (`midia.fonte_por_canal`).** Um canal tem um dono. No primeiro cliente, um canal
  vinha do Flow (conexão em dia) e o outro da planilha, porque a conexão daquele canal no Flow estava
  falhando havia meses. Sem essa chave, o mês contava o mesmo canal duas vezes.
- **Cobertura de leads separada da cobertura de custo.** Um canal pode trazer custo e não trazer
  lead; quando isso acontece, CPL e entrada no CRM saem sem medição e o custo e o ROAS seguem.
- **Tolerância de consolidação (`midia.tolerancia_dias`, padrão 1).** Plataforma de anúncio fecha o
  dia com atraso; exigir dado de hoje reprovava todo período corrente.
- Credenciais do Flow saem do repositório: `~/.config/v4-flow/mcp.json`, com chmod 600.

### O que a primeira operação real mostrou

- Um cliente pode ter **mais de um projeto** no Flow (contratos separados); cada um é um check-in.
- Conexão de mídia pode estar **falhando há meses** sem ninguém notar — daí a etapa de cobertura.
- Projeto pode estar **sem meta cadastrada** no período: o bloco de Objetivos precisa dizer isso.
- Pode não haver **call registrada** no período, e o grupo de WhatsApp existir com os campos de
  resumo vazios. Nos dois casos, o check-in diz que não há, em vez de inventar.

## v1.0 · 22/09/2026 · ETL do Flow ao ROPRE

- **Arquitetura em três camadas**, com contrato explícito entre elas (`transformar/canonico.py`):
  extrair (um adaptador por fonte), transformar (métricas do período) e carregar (os cinco blocos
  do ROPRE). Trocar o CRM ou a origem dos dados não encosta no check-in.
- **Adaptadores:** `flow_nect` (Flow/NECT, dirigido por configuração — endpoints e mapa de campos no
  `cliente.json`), `crm_nectarcrm` (implementação de referência para CRM fora do Flow),
  `midia_planilha` (planilha de acompanhamento, diário) e `conversas_mcp` (calls e WhatsApp lidos
  por MCP, gravados em arquivo de entrada para poderem ser conferidos antes de virar slide).
- **Cadências quinzenal, mensal e quarter.** Período parcial sai marcado e a meta é proporcional aos
  dias corridos.
- **Regra de atribuição declarada por cliente**, viajando junto com cada registro e impressa no deck.
  No primeiro cliente ela ficou assim: tag vale sozinha, e origem de mídia paga conta mesmo quando o
  texto não nomeia a agência.
- **Fonte incompleta vira "não medido".** A primeira execução em setembro devolveu ROAS de 37 e
  entrada no CRM de 720%, porque a aba do Meta está parada em 31/08. Agora `cobertura_midia` confere
  se todo canal configurado tem dado até o fim do período; sem isso, investimento, CPL, CTR, ROAS e
  CAC saem sem medição, com aviso nomeando o canal e o último dia.
- **Tabela "Planilha do cliente contra CRM"** no bloco R: responde, antes de a pergunta aparecer na
  reunião, por que o check-in mostra mais venda que o lançamento manual (a planilha não soma
  recompra).
- **Renderizadores:** `.pptx` na ordem do template da V4 (capa, índice, 01 a 05 e uma página final de
  fontes) e markdown para revisão. Os dois saem do mesmo `checkin.json`, então não existe versão com
  número diferente.
- **Regressão** com fixture sintética: leitura de data, atribuição, novo/recorrente, quinzena, mídia
  incompleta, OKRs, pendências de call e WhatsApp e os dois renderizadores. A regressão contra
  cliente real fica local, fora do repositório.

### Em aberto

- **Ekyte** (entregas e horas do projeto) veio sem token no JSON de configuração.
- **CRM no Flow:** quando o projeto não tem conexão de CRM lá, o CRM segue sendo lido direto pela
  API dele. Com CRM no Flow, usar `flow_crm_list_tables` + `flow_crm_query`.
