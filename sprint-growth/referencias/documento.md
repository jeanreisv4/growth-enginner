# Documento da sprint (Claude Docs)

Público: time da V4 e o cliente. Português, frases curtas, número com unidade, o que não é medido escrito como tal.

## Aba 1 — "Diagnóstico e plano" (nesta ordem)
1. **Resumo executivo**: a resposta em 3 frases + onde o funil vaza (lista numerada) + as ações de maior impacto.
   Linha com link para a aba Executado.
2. **Contexto e premissas** (tabela: premissa · valor · fonte).
3. **Fontes de dados** (tabela: fonte · o que traz · confiabilidade).
4. **Projetado × realizado** — gráfico (leads e trials/oportunidades projetados × reais por mês) + tabela das
   demais métricas + a régua de vendas esperadas pelas taxas da projeção.
5. **Funil real** — desenho de funil (pessoas por etapa, % que segue) + tabela por canal.
6. **Mídia** (Google, Meta) — só o que está aberto; o corrigido vai para Executado.
7. **Jornada e páginas** — desenho dos caminhos do lead (origem → página → onde cai → resultado, verde/vermelho).
   Logo abaixo, **Comportamento na página (Clarity)**: alertas C1–C6 nas páginas que recebem mídia, com o período
   coberto (a API só dá 24–72 h por coleta) escrito ao lado.
8. **Medição e rastreamento** (tabela: ponto · situação · efeito).
9. **Segurança**.
10. **Plano priorizado** (ranking em R$ com status).
11. **Google Ads e SEO: ação para cada achado** + **SEO on-page da página que recebe tráfego**.
12. **Referência de mercado**.
13. **Google Ads: o que falta decidir**.
14. **Pendências** (dados a receber, perguntas, próximos passos).
15. **Plano de ação 5W1H** com Status e a coluna Correção (o id `CX-…` do catálogo, com o risco R1/R2/R3).
16. **Fontes** (última linha).

### Seção obrigatória logo depois do resumo
**Restrições (Teoria das Restrições)**: restrição do sistema × restrição da mídia, desenho do fluxo (etapas com a
restrição em vermelho), "por que" com dado para cada afirmação, os 5 passos aplicados e a ordem de ataque.

## Abas opcionais (quando o volume pede)
- **Dados do funil (estratificado)**: por origem, lead novo × cliente antigo, PF × PJ, motivos de perda completos,
  time por mês, V4 × lead novo, tempo de cada etapa, WhatsApp e método.
- **Leads por CNPJ**: lista com empresa, CNAE, porte, UF, anúncio e classe (sem CPF de MEI).

## Aba 2 — "Executado"
Tabela única, mais recente primeiro: Data · Ação · Onde · Por quê (achado, com o número) · Verificação.

## Regras
- Corrigido sai do diagnóstico e **entra na aba Executado** (nunca some).
- Número corrigido durante a sprint é trocado no texto e avisado no chat (ex.: 152 → 131 pessoas).
- Gráfico e desenho: conferir por captura de tela e corrigir título que não bate com o número.
- Datas de ação como chip; status como menu.
