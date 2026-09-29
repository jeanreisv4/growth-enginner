# Changelog

## v2.0.2 (29/09/2026)

- Desenhos do README com o logo da ferramenta de cada agente: Google Ads e Google Analytics desenhados com a
  geometria e as cores oficiais, Meta, Tag Manager, Sheets e PageSpeed do Simple Icons (CC0) e Clarity do
  repositório oficial da Microsoft (MIT). Origem e licença em `assets/logos/FONTES.md`.

## v2.0.1 (29/09/2026)

- README com desenhos animados no estilo do claude-seo (SVG com animação nativa, roda no GitHub): capa com os
  comandos sendo digitados e o funil vazando na restrição, fluxo do sinal pelas duas ondas de agentes com o loop
  de volta à memória, e o mapa radial dos 8 agentes. O Mermaid detalhado continua, recolhido.
- `scripts/desenhos.py` gera os três SVG de `assets/`; a regressão confere que os arquivos batem com o gerador
  (107 casos).

## v2.0 (29/09/2026)

A auditoria passa a rodar em agentes especialistas, no desenho do claude-seo (skill que orquestra, agentes que
auditam em paralelo, contrato de saída consolidado por script).
- **8 agentes em `agentes/`**, somente leitura, um por frente: `sprint-fontes` (onda 1: pessoas únicas, canal,
  CNPJ, `base/pessoas.json`), e na onda 2 `sprint-google-ads`, `sprint-meta-ads`, `sprint-medicao` (com a skill
  `tracking-web-and-capi` carregada), `sprint-clarity`, `sprint-jornada`, `sprint-comercial` e `sprint-mercado`.
  Ferramentas das MCPs liberadas por nome, só as de leitura.
- **Contrato de achados** (`referencias/contrato_achados.md`): JSON por frente com fontes, não medido, números
  com chaves comuns, achados (etapa, tipo, confiança, insumos de impacto, esforço, verificação) e perguntas.
- `consolidar.py`: confere o contrato, ordena (segurança e medição primeiro, depois impacto máximo em R$) e aponta
  a mesma métrica divergindo entre frentes (ex.: lead da plataforma × pessoa única do backup).
- `clarity.py`: Microsoft Clarity pela Data Export API, coleta diária que respeita as 10 chamadas por dia e
  acumula; alertas C1–C6 (robôs, raiva, clique morto, volta rápida, erro de script, rolagem no celular).
- `instalar_agentes.py`: copia os agentes para `.claude/agents/` do projeto e confere a cópia.
- Meta pelo conector do claude.ai (leitura), além do export.
- `SKILL.md` em 7 etapas (0 a 6): as seções por frente viraram agentes; comandos para rodar uma frente só.
- Regressão: 103 casos (agentes sem ferramenta de escrita, scripts citados existem, cópia instalada bate).

## v1.1.3 (29/09/2026)

Da execução pós-sprint da distribuidora de peças automotivas.
- `gtm_auditoria.py`: alerta **G5**, o mesmo acionador como disparo e como exceção da tag (a exceção vence).
- Armadilhas: G5; conversões do Google hospedadas dão MUTATE_NOT_ALLOWED e saem do lance pela meta da campanha.
- Regressão: 44 casos.

## v1.1.2 (28/09/2026)

- README: seção "Como funciona", uma linha por fase (e por frente da auditoria) com o que entra, o que a skill faz,
  a ferramenta, o que sai e o que trava.
- Regressão: confere que todo script citado no README existe (43 casos).

## v1.1.1 (28/09/2026)

- **README com o desenho do workflow no formato de loop** (referência: modelos qualitativos de crescimento da
  Reforge): cada fase leva a sua saída escrita na seta, cores por tipo de passo (informação, decisão, análise,
  entrega, trava) e o ponto em que o loop se fecha (a próxima sprint começa pela memória do cliente).

## v1.1 (28/09/2026)

Aprendizados da sprint de uma distribuidora de peças automotivas (inside sales pelo WhatsApp, CRM DataCrazy) e da
revisão do SaaS de diário de obra.

- **Scripts novos:**
  - `datacrazy.py`: baixa negócios, leads e conversas (sem o token do WhatsApp) e amostra de histórico a 30 req/min;
    resumo por safra que separa lead novo de cliente antigo.
  - `cnpj.py`: valida CNPJ, consulta a Receita (BrasilAPI), classifica Qualificado / Parcial / Fora do perfil e
    tira o CPF do nome de MEI.
- `mcp_http.py`: espera e repete quando a API responde com cota por minuto (429 do GTM).
- **Roteiro (`SKILL.md`):**
  - realizado oficial;
  - CRM pela API;
  - lead novo × cliente antigo;
  - CPL real por pessoa única da mídia paga;
  - qualificação por CNPJ;
  - origem do clique para WhatsApp;
  - estratificação de cada afirmação;
  - tempo por etapa;
  - restrição pela TOC antes do ranking em R$.
- **Referências:**
  - 9 armadilhas novas (duas planilhas de realizado, venda V4 por etiqueta, mix novo × antigo, etiqueta manual
    atrasada, disparo em massa, CRM como registro, CPL sobre todos os leads, entre outras);
  - checklist de CNPJ;
  - ferramentas DataCrazy;
  - priorização com TOC.
- **Documento:** seção Restrições (TOC) com desenho; abas opcionais "Dados do funil" e "Leads por CNPJ".
- **README:** desenho do workflow (Mermaid).
- **Regressão:** 42 casos (15 novos).

## v1.0 (28/09/2026)

Primeira versão, montada a partir de três sprints reais: indústria de plásticos (set/2026), brindes
personalizados (set/2026) e SaaS de diário de obra (28/09/2026).

- `SKILL.md`: roteiro em 11 etapas (memória do cliente, entrevista, auditoria de fontes, mídia, medição e
  integração, jornada e página, comercial e receita, mercado, priorização, documento, execução e fechamento).
- Scripts:
  - `mcp_http.py`: cliente MCP sobre HTTP e webhook de escrita, com nova tentativa para resposta cortada e 5xx do n8n.
  - `ads_auditoria.py`: 15 consultas e alertas A1 a A10.
  - `termos_negativas.py`: recusa negativa que pega termo convertido.
  - `gtm_auditoria.py`: alertas G1 a G4, com o rótulo de conversão conferido contra a conta.
  - `teste_disparo.py`: disparo das tags sem lead.
  - `teste_formulario.py`: envio interceptado.
  - `ads_escrita.py`: valida antes e aplica só com `--aplicar`.
  - `leads.py`: telefone BR, teste, canal e pessoas.
  - `publicar.py`.
- Referências:
  - `armadilhas.md`: 30+ casos.
  - `checklist_auditoria.md`, `priorizacao.md` (impacto em R$, 5W1H com Status), `documento.md` (aba Diagnóstico e
    plano + aba Executado), `execucao.md`, `ferramentas.md`, `negativas_base.json`.
- Memória de cada cliente em `clientes/<cliente>/memoria.md` (git local; fora da cópia pública).
- Regressão: 27 casos sintéticos.
