---
name: sprint-growth
description: Sprint growth de cliente da V4 — auditoria da jornada inteira, do tráfego à venda (mídia paga Google e Meta, medição GA4/GTM/Pixel, comportamento no Clarity, página e formulário, integração com CRM ou painel, comercial, margem e breakeven, referência de mercado), com agentes especialistas por frente rodando em paralelo, plano 5W1H priorizado por impacto em receita e execução das correções pelas MCPs. Use sempre que o usuário disser "sprint growth", "preciso executar uma sprint", "auditar a conta do cliente", "sprint ads/meta/medição/clarity/comercial de um cliente", "audita só o GTM do cliente X", "diagnóstico do cliente", "onde a gente está e aonde quer chegar", ou mandar acessos, exports e planilhas de um cliente pedindo análise do funil de ponta a ponta. No fim de cada sprint a skill se atualiza com o que foi aprendido.
---

# Sprint growth

**Versão 2.2.1 (30/09/2026).** Histórico em `CHANGELOG.md`. Caminhos relativos à pasta da skill
(`.claude/skills/sprint-growth/`). Clientes em `clientes/<cliente>/` (versionado no git local, fora da cópia
pública). Configuração das MCPs em `~/.config/sprint-growth/config.json` (fora do repositório).

A sprint responde três perguntas, nesta ordem: **onde o cliente está** (medido), **onde o funil vaza** (etapa por
etapa, do clique à venda) e **o que fazer primeiro** (em R$ de receita, com confiança e esforço). Ela valida a
jornada inteira: tráfego, conversão, integração, jornada de compra, comercial e margem. O desenho do fluxo está
no `README.md` (seção Workflow).

## Modos: auditoria e correção

A sprint tem dois modos, com o mesmo catálogo por plataforma em `referencias/plataformas/` (fontes, Google Ads, Meta
Ads, GA4, GTM web e servidor, Clarity, páginas, CRM e integração, comercial, mercado). Cada arquivo lista **tudo o
que se verifica** (ids `A1`, `M3`, `GA2`…) e **tudo o que se corrige** (ids `CX-…`, com risco, volta e verificação).
`python3 scripts/catalogo.py` confere que todo item de auditoria tem correção.

- **Auditoria** (etapas 0–4): somente leitura, pelos agentes; cada frente devolve o status de todos os seus itens.
- **Correção** (etapa 5): executa um `CX-…` do plano ou de uma ordem direta ("corrige o A2 do cliente X"), no ciclo
  de `referencias/modos.md`: preparar, validar antes, mostrar, ok explícito, aplicar, reler, registrar, monitorar.
- Pedido de correção sem achado recente: audite a frente primeiro. Nunca corrigir sem o número.

## 0. Antes de tudo

1. Se `clientes/<cliente>/memoria.md` existe, **leia inteira** antes de perguntar qualquer coisa. Ela tem IDs,
   premissas, regra de atribuição e o que já foi executado. Não pergunte o que ela já responde.
2. Se não existe, copie `templates/cliente/` (memória, config e briefing) para `clientes/<cliente>/`.
3. Leia `referencias/armadilhas.md` inteiro. Cada item ali já custou um diagnóstico errado.

## 1. Entrevista, briefing e pré-voo (tudo no começo; roteiro em `referencias/entrevista.md`)

Informação que chega no meio da sprint vira retrabalho. Peça tudo de uma vez, teste os acessos antes dos agentes e
pegue primeiro o que expira.

1. **Briefing**: copie `templates/cliente/briefing.md` para `clientes/<cliente>/` e mande ao usuário (ou pergunte os
   blocos em lotes de até 4 perguntas, com a opção recomendada). Cinco blocos: **dinheiro** (fee, verba por canal,
   margem pelo DRE, ticket por serviço, meta, projeção vigente), **operação e oferta** (o que vende e o que não vende,
   modalidades de atendimento e logística, regiões atendidas e evitadas, provas), **regras de contagem** (realizado
   oficial e o que não é fonte, como a venda é contada, atribuição V4, critério de MQL, siglas como "LT"),
   **comercial** (quem atende, canais, login do CRM, cadência, venda fora do CRM) e **acessos e donos**. Em branco =
   pendente: não trava a sprint, vira "não medido" e pendência com dono.
2. **Config**: IDs e caminhos de chave em `clientes/<cliente>/config.json` (modelo em `templates/cliente/`).
3. **Pré-voo**: `python3 scripts/preflight.py --cliente <c> --sprint <SPRINT>` testa Google Ads (conta, veiculação,
   gasto), GTM, GA4 da LP e do site, CRM (GET com o token), n8n (API e fluxos), planilhas, páginas (GTM e GA4 no HTML),
   Clarity (só a chave) e exports do Meta, e grava `<SPRINT>/preflight.md`. Mostre ao usuário **uma lista única** do
   que falta, com como resolver.
4. **Perecíveis hoje**: leads do formulário nativo do Meta (90 dias), Clarity (24–72 h), histórico do Google Ads
   (30 dias). Exports pedidos no formato de `referencias/entrevista.md`, para não chegarem em partes.
5. **Lacunas que mudam a análise** (modalidade e logística, o que não vende, ticket e margem, atribuição, MQL): pergunte
   antes dos agentes. O resto segue como pendência.

Grave as respostas na memória e no briefing: a próxima sprint do mesmo cliente não pergunta de novo.

## 2. Auditoria pelas frentes (agentes especialistas)

Cada frente é um agente em `agentes/` (instalado em `.claude/agents/` do projeto). O agente só lê, tem o próprio
contexto e entrega `achados/<frente>.json` + `.md` no formato de `referencias/contrato_achados.md`. Ele não fala
com o usuário: o que só o usuário responde volta em `perguntas`. Entrevista, decisão, documento e execução ficam
aqui, na conversa principal.

| Frente | Agente | Cobre |
| --- | --- | --- |
| fontes | `sprint-fontes` | bases, período e confiabilidade, pessoas únicas sem teste, canal, CNPJ, `base/pessoas.json` |
| google-ads | `sprint-google-ads` | A1–A10, termos e negativas, anúncio × página, CPL real |
| meta-ads | `sprint-meta-ads` | conector do Meta ou export, criativo × qualidade do lead, segunda conta, anomalias, CPL real |
| medicao | `sprint-medicao` | GTM G1–G5, disparo real, formulário interceptado, GA4, Pixel/CAPI, lead até o CRM |
| clarity | `sprint-clarity` | robôs, raiva, clique morto, volta rápida, erro de script, rolagem (C1–C6) |
| jornada | `sprint-jornada` | destino e custo por destino, oferta × página, on-page, SEO técnico básico, velocidade |
| comercial | `sprint-comercial` | CRM, lead novo × cliente antigo, perdas, tempos, follow-up, receita (piso) |
| mercado | `sprint-mercado` | concorrentes dos termos, preço com unidade, teste, CTA, provas |

### Como conduzir
1. **Agentes instalados?** `python3 scripts/instalar_agentes.py --conferir`. Se falhar, rode sem `--conferir` e
   avise que os agentes só aparecem numa conversa nova. Enquanto isso, rode a frente com o agente
   `general-purpose` passando o conteúdo de `agentes/sprint-<frente>.md` como instrução.
2. **Pasta da sprint**: `clientes/<cliente>/sprints/<AAAA-MM-DD>/` com `achados/` e `base/`.
3. **Bloco de entrada** (igual para todos, preenchido com a memória e a entrevista):

       PASTA_SKILL: <caminho absoluto desta skill>
       CLIENTE: <cliente>   SPRINT: clientes/<cliente>/sprints/<AAAA-MM-DD>   PERÍODO: <início> a <fim>
       REALIZADO OFICIAL: ...   COMO A VENDA É CONTADA: ...   ATRIBUIÇÃO V4: ...
       IDS: Google Ads (conta, endpoint) · Meta (conta) · GA4 · GTM (conta, web, servidor) · Clarity (arquivo do token)
            · CRM (tipo, arquivo da chave ou export) · site e LPs
       JÁ SABEMOS: <o trecho da memória que importa para esta frente>

4. **Onda 1**: `sprint-fontes` (em primeiro plano; as outras frentes cruzam a base de pessoas que ele grava).
5. **Onda 2**: numa única mensagem, as frentes que se aplicam ao cliente, em segundo plano. Frente que não se
   aplica (cliente sem Meta, sem Clarity) fica fora e não entra em `--frentes`.
6. **Consolidar**: `python3 scripts/consolidar.py --sprint <SPRINT> --frentes <lista>`. Arquivo recusado: devolva
   ao agente (SendMessage) com o problema. **Divergência** entre frentes: pergunte ao usuário qual fonte manda.
   **Perguntas** dos agentes: uma por vez, as que a memória não responde.
7. **Confira à mão** os 2 achados de maior impacto (releia o número no dado bruto) antes de levá-los ao documento.
8. Breakeven e projeção: skill `projecao-breakeven` (não refaça aqui).

### Uma frente só
"sprint ads <cliente>", "audita só o GTM do cliente X", "roda o Clarity do cliente Y": leia a memória (etapa 0), rode só o agente
da frente (com `sprint-fontes` antes quando a frente cruza pessoas: google-ads, meta-ads, comercial) e
`consolidar.py --frentes <frente>`. Entregue o `.md` da frente e as correções propostas; documento só se pedirem.
Para tracking do zero ou go-live, a skill é `tracking-e-integracoes`; para integrar (lead no CRM, Lead Ads direto no
n8n, devolução do CRM ao Meta e ao Google, revisão de automações), o modo `integrar` dela e os agentes
`integracao-*`; para SEO completo, `/seo audit`.

## 3. Priorização e plano

Entrada: `<SPRINT>/consolidado.md` (achados já ordenados, divergências e não medido).
`referencias/priorizacao.md`: primeiro a **restrição pela Teoria das Restrições** (sistema × mídia, 5 passos),
depois impacto em R$/mês = volume da etapa × ganho esperado × taxas seguintes × ticket,
com confiança (medido ou suposto) e esforço. Medição quebrada vem antes de otimização. O plano sai em 5W1H com
Impacto, Confiança, Esforço e Status.

## 4. Documento (Claude Docs)

Formato fixo em `referencias/documento.md`: aba **Diagnóstico e plano** (resumo, contexto, fontes, projetado ×
realizado com gráfico, funil desenhado, mídia, jornada desenhada, comportamento na página (Clarity), medição, segurança, plano priorizado, SEO,
mercado, pendências, **Plano de ação 5W1H com Status**) e aba **Executado** (data, ação, onde, por quê,
verificação). **O que foi corrigido sai do diagnóstico e entra na aba Executado** — nunca some. Seção
**Restrições (TOC)** logo depois do resumo, com desenho do fluxo. Abas extras quando houver volume: **Dados do
funil** (estratificado) e **Leads por CNPJ**. Número corrigido na conversa é corrigido em todo o documento.

## 5. Execução

`referencias/modos.md` (ciclo e risco R1/R2/R3) e a tabela Correção da plataforma. Resumo: toda mudança é **validada antes** (validateOnly, draft do GTM) e só é aplicada
com ok explícito do usuário para aquela mudança; depois é **relida** pela API e registrada na aba Executado.
Publicar GTM, criar fluxo no n8n e mexer em conta de cliente passam pelo modo automático do Claude Code: se ele
negar, pare, explique e deixe a decisão com o usuário — nunca contorne.

## 6. Fechamento: atualizar a skill

Ao fim de toda sprint (ou quando o usuário pedir):
1. Atualize `clientes/<cliente>/memoria.md` (premissas, IDs, decisões, executado, pendências, link do documento).
2. Leve cada armadilha nova para `referencias/armadilhas.md` e cada verificação nova para
   o catálogo em `referencias/plataformas/` (item de auditoria e a correção que o resolve; e para o script, se couber). Se a lição muda o roteiro de uma frente,
   edite `agentes/sprint-<frente>.md` e rode `python3 scripts/instalar_agentes.py`.
3. Rode `python3 tests/regressao.py`; entrada no `CHANGELOG.md`; versão no topo deste arquivo; commit e tag.
4. Publicação: `python3 scripts/publicar.py --destino <pasta>` e `--conferir <pasta>` antes do push.
   `clientes/` e a configuração nunca vão para o GitHub.
