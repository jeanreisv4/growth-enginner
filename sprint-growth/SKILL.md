---
name: sprint-growth
description: Sprint growth de cliente da V4 — auditoria da jornada inteira, do tráfego à venda (mídia paga Google e Meta, medição GA4/GTM, página e formulário, integração com CRM ou painel, comercial, margem e breakeven, referência de mercado), com plano 5W1H priorizado por impacto em receita e execução das correções pelas MCPs. Use sempre que o usuário disser "sprint growth", "preciso executar uma sprint", "auditar a conta do cliente", "diagnóstico do cliente", "onde a gente está e aonde quer chegar", ou mandar acessos, exports e planilhas de um cliente pedindo análise do funil de ponta a ponta. No fim de cada sprint a skill se atualiza com o que foi aprendido.
---

# Sprint growth

**Versão 1.1 (28/09/2026).** Histórico em `CHANGELOG.md`. Caminhos relativos à pasta da skill
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

## 2. Auditoria das fontes (antes de qualquer conta)

- Liste cada base com período coberto, último dia com dado e confiabilidade (alta, média, baixa). Base parada
  vira "não medido", nunca zero.
- Conte **por pessoa**, não por linha: `scripts/leads.py` (telefone BR canônico, e-mail canônico, filtro de
  teste com a lista do cliente, canal por gclid/fbclid/utm/referrer). Na SaaS de diário de obra, 152 linhas viraram 131 pessoas.
- Lead de teste é padrão em projeto novo (equipe V4 e equipe do cliente testando): liste e exclua, e mostre a lista.
- Pergunte **qual planilha é o realizado oficial** antes do primeiro gráfico (Growth Pack manual × planilha de
  projeção). A outra entra só com o projetado.
- **CRM DataCrazy**: `scripts/datacrazy.py baixar` (negócios, leads, conversas sem o token do WhatsApp, motivos,
  pipelines) e `historico` (amostra estratificada de eventos por lead, 30 req/min). Outros CRMs: mesma lógica.
- **Separe lead novo de cliente antigo** (negócio aberto no dia do cadastro × lead que já existia) antes de falar em
  conversão: `datacrazy.py resumo`. Na distribuidora de peças, "entrada estável e venda caindo" era a recompra da
  base (cliente antigo fecha ~30%, lead novo 2–4%), não o fechamento do lead novo.

## 3. Mídia

- **Google Ads**: `scripts/ads_auditoria.py` (somente leitura) gera `ads_resumo.md` com alertas A1–A10
  (conversão principal zerada, duplicada ou sem uso, invasão, lances sem teto, "presença ou interesse", nota ≤ 3,
  parcela perdida, sitelink para âncora inexistente, troca de destino, orçamento abaixo do gasto). Depois,
  `scripts/termos_negativas.py` com `referencias/negativas_base.json` + a lista do cliente.
- **Meta**: exports por anúncio (CSV) ou conector. Cruze criativo × qualidade do lead no backup (porte, CNPJ,
  campo de qualificação). Confira renomeação de campanha pelo **ID**, nunca pelo nome. Campanha com ID de outra
  conta (sufixo diferente) indica segunda conta de anúncios.
- **CPL real = verba ÷ pessoas únicas da mídia paga V4** (sem duplicado entre fontes, sem direto sem origem, sem
  orgânico, sem outra conta), mês a mês e por canal. Dividir por todos os leads subestimou o CPL em 36% (SaaS de diário de obra).
- **Lead B2B com CNPJ**: `scripts/cnpj.py` consulta a Receita (BrasilAPI) e classifica Qualificado / Parcial / Fora
  do perfil; cruze com anúncio e com a resposta de porte do formulário. Custo por lead qualificado vai no documento.
- Confirme o **canal** antes de pesquisar benchmark.

## 4. Medição e integração

- `scripts/gtm_auditoria.py`: rótulo de conversão que não existe na conta (G1), GA4 do servidor repassando evento
  do Meta (G2), tag pausada ou sem acionador (G3), rótulo repetido (G4).
- `scripts/teste_disparo.py`: prova que as tags disparam com o rótulo certo, sem lead e com GA4/Meta bloqueados.
- `scripts/teste_formulario.py`: mostra o que o formulário enviaria, sem enviar. Pega GTM preso em banner de
  cookies e formulário que não leva UTM/gclid.
- GA4: eventos principais que realmente disparam; vínculo com o Google Ads; UTMs do Meta com ID viram "Unassigned".
- Siga o lead até o destino (planilha, n8n, CRM, painel): ele chega? com origem? vira trial/oportunidade?
- Etiqueta de origem no CRM: quem coloca e com que atraso (histórico do lead). Manual e atrasada = mês corrente
  sempre parece pior.
- Clique para WhatsApp: com API oficial, a origem do anúncio só chega se o rastreio do CRM estiver ligado
  (DataCrazy: `sourceReferral` da conversa). Pop-up que redireciona para wa.me não dispara tag de clique em link.

## 5. Jornada, página e oferta

- Destino de cada anúncio (site × LP) e custo por lead de cada um.
- On-page da página que recebe o tráfego: um `<title>`, description, H1/H2 com as palavras que o anúncio compra,
  schema, og, formulário (campos obrigatórios), oferta coerente com o anúncio ("50% Off" que a página não mostra).
- SEO técnico do site: robots.txt, sitemap, canonical, dados estruturados.

## 6. Comercial e receita

- Funil real por etapa (lead → trial/oportunidade → contato → venda), com o que não é medido escrito como tal.
- Follow-up: última data de contato registrada; quem clicou em "comprar" e não foi atendido.
- Receita: lista de assinantes ou CRM por data de fechamento. Sem fonte completa, informe **piso** e o limite.
- Estratifique cada afirmação (o usuário vai perguntar "por quê?"): origem, lead novo × antigo, PF × PJ, vendedor,
  motivo de perda (todos os motivos, mês a mês, e grupos antes/depois do orçamento), tempo de cada etapa (mediana e
  p75 por safra e por vendedor) e caminhos no CRM. Tabelas longas vão numa aba "Dados do funil".
- Breakeven e projeção: use a skill `projecao-breakeven` (não refaça aqui).

## 7. Mercado

Agente de pesquisa em segundo plano (Agent, general-purpose) sobre os concorrentes que aparecem nos termos de
pesquisa: posicionamento (H1), preço com unidade, trial, CTA, provas. Confira à mão os 2 preços que mais pesam.

## 8. Priorização e plano

`referencias/priorizacao.md`: primeiro a **restrição pela Teoria das Restrições** (sistema × mídia, 5 passos),
depois impacto em R$/mês = volume da etapa × ganho esperado × taxas seguintes × ticket,
com confiança (medido ou suposto) e esforço. Medição quebrada vem antes de otimização. O plano sai em 5W1H com
Impacto, Confiança, Esforço e Status.

## 9. Documento (Claude Docs)

Formato fixo em `referencias/documento.md`: aba **Diagnóstico e plano** (resumo, contexto, fontes, projetado ×
realizado com gráfico, funil desenhado, mídia, jornada desenhada, medição, segurança, plano priorizado, SEO,
mercado, pendências, **Plano de ação 5W1H com Status**) e aba **Executado** (data, ação, onde, por quê,
verificação). **O que foi corrigido sai do diagnóstico e entra na aba Executado** — nunca some. Seção
**Restrições (TOC)** logo depois do resumo, com desenho do fluxo. Abas extras quando houver volume: **Dados do
funil** (estratificado) e **Leads por CNPJ**. Número corrigido na conversa é corrigido em todo o documento.

## 10. Execução

`referencias/execucao.md`. Resumo: toda mudança é **validada antes** (validateOnly, draft do GTM) e só é aplicada
com ok explícito do usuário para aquela mudança; depois é **relida** pela API e registrada na aba Executado.
Publicar GTM, criar fluxo no n8n e mexer em conta de cliente passam pelo modo automático do Claude Code: se ele
negar, pare, explique e deixe a decisão com o usuário — nunca contorne.

## 11. Fechamento: atualizar a skill

Ao fim de toda sprint (ou quando o usuário pedir):
1. Atualize `clientes/<cliente>/memoria.md` (premissas, IDs, decisões, executado, pendências, link do documento).
2. Leve cada armadilha nova para `referencias/armadilhas.md` e cada verificação nova para
   `referencias/checklist_auditoria.md` (e para o script, se couber).
3. Rode `python3 tests/regressao.py`; entrada no `CHANGELOG.md`; versão no topo deste arquivo; commit e tag.
4. Publicação: `python3 scripts/publicar.py --destino <pasta>` e `--conferir <pasta>` antes do push.
   `clientes/` e a configuração nunca vão para o GitHub.
