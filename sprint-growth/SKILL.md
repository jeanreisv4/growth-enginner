---
name: sprint-growth
description: Sprint growth de cliente da V4 — auditoria da jornada inteira, do tráfego à venda (mídia paga Google e Meta, medição GA4/GTM/Pixel, comportamento no Clarity, página e formulário, integração com CRM ou painel, comercial, margem e breakeven, referência de mercado), com agentes especialistas por frente rodando em paralelo, plano 5W1H priorizado por impacto em receita e execução das correções pelas MCPs. Use sempre que o usuário disser "sprint growth", "preciso executar uma sprint", "auditar a conta do cliente", "sprint ads/meta/medição/clarity/comercial de um cliente", "audita só o GTM do cliente X", "diagnóstico do cliente", "onde a gente está e aonde quer chegar", ou mandar acessos, exports e planilhas de um cliente pedindo análise do funil de ponta a ponta. No fim de cada sprint a skill se atualiza com o que foi aprendido.
---

# Sprint growth

**Versão 2.0.2 (29/09/2026).** Histórico em `CHANGELOG.md`. Caminhos relativos à pasta da skill
(`.claude/skills/sprint-growth/`). Clientes em `clientes/<cliente>/` (versionado no git local, fora da cópia
pública). Configuração das MCPs em `~/.config/sprint-growth/config.json` (fora do repositório).

A sprint responde três perguntas, nesta ordem: **onde o cliente está** (medido), **onde o funil vaza** (etapa por
etapa, do clique à venda) e **o que fazer primeiro** (em R$ de receita, com confiança e esforço). Ela valida a
jornada inteira: tráfego, conversão, integração, jornada de compra, comercial e margem. O desenho do fluxo está
no `README.md` (seção Workflow).

## 0. Antes de tudo

1. Se `clientes/<cliente>/memoria.md` existe, **leia inteira** antes de perguntar qualquer coisa. Ela tem IDs,
   premissas, regra de atribuição e o que já foi executado. Não pergunte o que ela já responde.
2. Se não existe, copie `templates/cliente/` para `clientes/<cliente>/` e preencha conforme a entrevista.
3. Leia `referencias/armadilhas.md` inteiro. Cada item ali já custou um diagnóstico errado.

## 1. Entrevista (uma pergunta por vez; pare quando a memória do cliente já responde)

1. **Cliente e modelo**: segmento; inside sales (lead → venda), e-commerce ou SaaS com trial; o que o contrato
   cobre (mídia, SEO, CRM, comercial).
2. **Premissas de dinheiro**: fee, verba por canal, margem de contribuição (peça o DRE; a margem "de cabeça" já
   errou por 6 p.p.), ticket e planos, meta do cliente, projeção vigente (link).
3. **Fontes**: backup de leads, CRM ou painel (API/export), Growth Pack, contas de mídia, GA4, GTM, LP e site.
   **Qual fonte manda** quando duas dão números diferentes. **O que NÃO é fonte** (abas paradas).
4. **Como a venda é contada**: data de criação ou de fechamento; com ou sem recompra; lançamento manual ou CRM.
5. **Regra de atribuição V4**: o que conta como lead e venda da V4. Feche por escrito e grave na memória.
6. **Tempo de casa (LT)**: "LT" pode ser tempo de casa do cliente ou vida do assinante — pergunte. Na SaaS de diário de obra era
   tempo de casa; interpretar como churn mudaria todo o breakeven.

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
Para tracking do zero ou go-live, a skill é `tracking-web-and-capi`; para SEO completo, `/seo audit`.

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

`referencias/execucao.md`. Resumo: toda mudança é **validada antes** (validateOnly, draft do GTM) e só é aplicada
com ok explícito do usuário para aquela mudança; depois é **relida** pela API e registrada na aba Executado.
Publicar GTM, criar fluxo no n8n e mexer em conta de cliente passam pelo modo automático do Claude Code: se ele
negar, pare, explique e deixe a decisão com o usuário — nunca contorne.

## 6. Fechamento: atualizar a skill

Ao fim de toda sprint (ou quando o usuário pedir):
1. Atualize `clientes/<cliente>/memoria.md` (premissas, IDs, decisões, executado, pendências, link do documento).
2. Leve cada armadilha nova para `referencias/armadilhas.md` e cada verificação nova para
   `referencias/checklist_auditoria.md` (e para o script, se couber). Se a lição muda o roteiro de uma frente,
   edite `agentes/sprint-<frente>.md` e rode `python3 scripts/instalar_agentes.py`.
3. Rode `python3 tests/regressao.py`; entrada no `CHANGELOG.md`; versão no topo deste arquivo; commit e tag.
4. Publicação: `python3 scripts/publicar.py --destino <pasta>` e `--conferir <pasta>` antes do push.
   `clientes/` e a configuração nunca vão para o GitHub.
