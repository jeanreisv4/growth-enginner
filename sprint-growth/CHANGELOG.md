# Changelog

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
