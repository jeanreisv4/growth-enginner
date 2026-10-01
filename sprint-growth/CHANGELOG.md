# Changelog


## v2.2.2 — 2026-09-30

Aprendizados da otimização de uma fábrica de acessórios para cortina (B2B, só Google Ads, planilha sem CRM).
- `referencias/armadilhas.md` (Mídia): pacing com programação de anúncios (diário = verba ÷ dias com anúncio, conferir
  nos dias 10 e 20); palavra genérica de B2B em frase puxando consumidor final (filtro de lojista no título fixo, negativas
  e MQL de volta como conversão secundária); madrugada e domingo em B2B (A18/CX-A10).
- `publicar.py`: nome do cliente no mapa de anonimização.

## v2.2.1 — 2026-09-30

- A skill irmã virou `tracking-e-integracoes` (antes `tracking-web-and-capi`): referências trocadas (SKILL, README,
  agente `sprint-medicao`, catálogos de GTM e CRM); integração e devolução apontam para o modo `integrar` dela, os
  agentes `integracao-*` e o `auditar_entrada.py` (formulário × CRM por semana).
## v2.2 (30/09/2026)

Entrevista no começo, uma vez, para a sprint rodar automatizada e sem retrabalho.
- **Briefing** (`templates/cliente/briefing.md`): formulário único por cliente em cinco blocos (dinheiro, operação e
  oferta, regras de contagem, comercial, acessos e donos), com "onde achar se não souber". Em branco = pendente.
- **Pré-voo** (`scripts/preflight.py`): antes dos agentes, testa Google Ads (conta, veiculação suspensa, gasto de 30
  dias), GTM, GA4 da LP e do site (token vencido, sem permissão), CRM (GET direto com o token; Kommo e DataCrazy), n8n
  (API e fluxos do cliente), planilhas públicas, páginas (GTM e GA4 no HTML, GA4 de outra conta) e Clarity (só a
  chave), e grava `preflight.md` com ok · falta · atenção · manual e como resolver. Somente leitura.
- **`referencias/entrevista.md`**: ordem (memória → briefing → config → pré-voo → perecíveis → lacunas), o que expira
  (leads do Meta em 90 dias, Clarity em 72 h, histórico do Google Ads em 30 dias) e o formato de cada export.
- SKILL.md: seção 1 reescrita; `templates/cliente/config.json` com propriedade do GA4 do site, ID interno do container,
  fluxos do n8n, planilha de backup, LPs e site institucional.
- `publicar.py --conferir` recusa a cópia pública com qualquer ID dos `config.json` de clientes (conta, container,
  propriedade, Pixel, planilha): testes da v2.1.1 levavam o ID real de um Pixel e de um GA4; trocados por fictícios.
- Regressão: +13 casos do pré-voo, da entrevista e do publicador.

## v2.1.1 (30/09/2026)

Aprendizados da sprint de uma empresa de revestimento industrial (Meta + Google, Kommo, n8n, Make, GreatPages).
- **Catálogo +11 itens e +11 correções** (142 e 119): plataforma × linhas do backup por dia (F9) e premissas da
  projeção com base medida (F10); credencial do CRM testada direto (I12), coluna de controle só com o marcador do
  próprio fluxo (I13) e destino da LP desde o primeiro dia de mídia (I14); caixa de entrada triada (V11), régua de MQL
  que separa (V12) e qualificação por região × modalidade em negócio com logística (V13); resíduo de invasão nos
  ativos da conta nova (A29); conjunto de região que não entrega a região (M19); site institucional medido antes de
  virar destino (P13).
- **Armadilhas novas**: leads da plataforma × pessoas únicas, ticket circular, resíduo de invasão, verba no pior
  anúncio, filtro que esconde credencial morta, Make mudando o layout, LP sem destino, GA4 do site de outra conta,
  Kommo (busca por nome, caixa de entrada fora do `/leads`, data retroativa e perda em lote), formulário sem toque no
  CRM, régua de MQL reescalada e negócio com logística; na execução, credencial do n8n com domínios, arquivo bruto com
  segredo e token do GA4 renovado.
- **Agentes**: comercial lê o Kommo (etapa de entrada por filtro, casar por telefone, régua de MQL); fontes cruza
  plataforma × linhas por dia e as premissas da projeção; medição olha credencial, coluna de controle, destino da LP e
  site; Google Ads procura resíduo de invasão e mede a demanda disponível.
- `gtm_auditoria.py` mascara segredos (token da API de Conversões, chaves, senhas) antes de gravar `gtm_raw.json`.
- `termos_negativas.py` ignora chaves de comentário (`_nota`) no arquivo de negativas do cliente.
- `publicar.py`: nome do cliente novo no mapa de anonimização.

## v2.1 (30/09/2026)

Dois modos com catálogo completo por plataforma, para a sprint cobrir 100% do que se verifica e do que se corrige.
- **`referencias/plataformas/`**: fontes, Google Ads, Meta Ads, GA4, GTM web e servidor, Clarity, páginas, CRM e
  integração, comercial e mercado. Cada arquivo tem a tabela **Auditoria** (id, verificação, frente, como verificar,
  sinal de problema, gravidade) e a tabela **Correção** (id `CX-…`, o que corrige, como aplicar, validar antes, risco,
  voltar atrás, verificar depois). 131 itens de auditoria, 108 correções; todo item tem correção.
- **`referencias/modos.md`**: auditoria (somente leitura, cobertura item a item) e correção (preparar, validar, mostrar,
  ok, aplicar, reler, registrar, monitorar), com risco R1/R2/R3. Substitui `execucao.md`; o catálogo substitui
  `checklist_auditoria.md`.
- `catalogo.py`: lê e confere o catálogo; `--frente` lista os itens de cada agente.
- Contrato de achados: `cobertura` (status de cada item da frente), `item` e `correcao_id` em cada achado.
- `consolidar.py`: cobertura por frente, itens não verificados e críticos ou altos sem status; recusa id de outra frente.
- Agentes: cobertura do catálogo obrigatória. 5W1H ganha a coluna Correção.
- Regressão: 124 casos (catálogo íntegro, item sem correção reprovado, README = catálogo, cobertura no consolidado).

## v2.0.3 (29/09/2026)

- Armadilhas: integração nativa da loja com a mesma conta do Google Ads (tags do GTM param de enviar) e container
  copiado de outro cliente (constantes erradas e sobras).

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
