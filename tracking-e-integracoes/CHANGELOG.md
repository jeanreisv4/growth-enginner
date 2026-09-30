# Changelog — tracking-e-integracoes (antes tracking-web-and-capi)

## v2.0.0 — 2026-09-30

**Renomeada para `tracking-e-integracoes`** (era `tracking-web-and-capi`): a skill passou a cobrir o lead entrando no
CRM e a venda voltando às plataformas, não só o tracking da página. Nasceu da integração completa de uma distribuidora
de automatizadores (distribuidora de automatizadores) num dia: devolução ao Meta e ao Google, Lead Ads direto no n8n, recuperação de leads
perdidos, correção do Chatwoot e revisão das automações.

- **Modo 4, `integrar`** (`latest.md`): mapa pelos agentes → entrada medida (formulário × CRM) → decisões do usuário →
  montar desligado → testar sem gravar → ligar e recuperar com ok → revisão das automações.
- **4 agentes** em `agentes/` (instalados por `scripts/instalar_agentes.py`): `integracao-crm`, `integracao-meta`,
  `integracao-google-ads`, `integracao-conversacional`; contrato em `referencias/contrato_integracao.md`.
- **Guias novos**: `implementacoes/meta-lead-ads.md` (app próprio, erros 1349048 e "Invalid Scopes", credencial pela
  API, um webhook por app, teste sem gravar, recuperação em lotes), `google-ads-offline.md` (Data Manager, conversões
  secundárias, conversões otimizadas para leads só pela UI), `conversacional-chatwoot.md` (índice em cache, fila com
  espera sorteada), `crm-conectores.md` (contrato de CRM; Kommo, RD Station CRM, HubSpot, Pipedrive, DataCrazy,
  NectarCRM, GoHighLevel).
- **Scripts novos**: `auditar_entrada.py` (formulário × CRM por semana e origem: acha a semana em que a integração
  parou) e `n8n_meta_leads.py` (leads do formulário pela credencial de Lead Ads, sem dado pessoal, workflow temporário
  apagado).
- Checklist: seção 14 (integrações). Troubleshoot: lead fora do CRM com planilha recebendo; credencial OAuth sem Connect.
- `publicar.py`: cliente anonimizado só como palavra inteira; ids do cliente novo na conferência; nomes dos outros
  clientes como rede de segurança.
- Desenhos: "tracking & integrações", quatro modos. Regressão: 90 → 100 casos.

## v1.2.3 — 2026-09-30

- `meta_leadgen`: a devolução busca o id do lead do formulário instantâneo no Meta pelo telefone (token da página com
  a credencial Facebook Lead Ads, formulários e leads dos últimos 90 dias com paginação, `acharLeadId` no núcleo).
  Testado na distribuidora de automatizadores: 816 leads lidos, 41% dos telefones do funil casaram.
- Nós HTTP aceitam credencial de serviço (`predefinedCredentialType`).

## v1.2.2 — 2026-09-30

- Primeiro teste real (distribuidora de automatizadores, lead em "Orçamento enviado" → SQL aceito pela CAPI, nota escrita no lead) mostrou:
  resposta `hal+json` do Kommo lida como texto (nós HTTP agora pedem JSON e o código aceita texto) e celular sem o
  9º dígito (o modo direto manda as duas versões do telefone).
- Test Event Code marca o envio em lista separada: o teste não bloqueia o envio de verdade do mesmo lead.

## v1.2.1 — 2026-09-30

- Devolução em **modo direto** (`meta_via: "direto"`): n8n → API de Conversões sem sGTM, com hash no núcleo
  (`metaGraph`) e credencial Query Auth; o container de servidor não recebe peças nesse modo.
- Armadilhas da distribuidora de automatizadores: Data Client fora da galeria, constante vazia recusada pela API do GTM, 142 com outro sentido
  no pós-venda, lead que só nasce qualificado, container da Stape desativado (`/healthy` 404).
- Regressão: 77 → 82 casos.

## v1.2.0 — 2026-09-30

**Devolução do CRM às plataformas (Kommo → n8n → sGTM/Meta e Google Ads).** Pedido da distribuidora de automatizadores
(leads do formulário instantâneo no Kommo, SQL e venda de volta ao Meta e ao Google).

- `scripts/devolucao.py`: a partir do bloco `devolucao` do brief, gera o workflow do n8n (webhook com resposta
  imediata → lead e contato na API → evento → sGTM e Data Manager API → nota no lead, sem reenviar o que já foi),
  as peças do sGTM para container existente e o resumo; valida o bloco (etapa 143, nome no lugar do id, token no
  brief, Google sem campo de clique...).
- `templates/devolucao/nucleo.js`: leitura dos dois formatos de webhook do Kommo, telefone E.164, e-mail
  normalizado (gmail sem pontos para o Google), `fbc` a partir do `fbclid`, `lead_id` do Meta validado (15-17
  dígitos, em texto), SHA-256 em JS puro, `event_id` estável por lead e evento. O mesmo arquivo roda no n8n e nos testes.
- `gerar_containers.py`: com o bloco, o sGTM sai com o Data Client (template da Stape em
  `templates/gtm/data-client.tpl`), acionadores com chave e as tags `00.5+ | Meta CAPI - <evento>` já corrigidas
  (system_generated, sem fbp inventado, IP/UA do lead, hora da etapa); acionador do site protegido quando o nome
  do evento coincide.
- Google Ads pela **Data Manager API**: a Google Ads API não aceita mais novos importadores offline (15/06/2026).
- `implementacoes/crm-kommo.md` deixa de ser esqueleto; Bloco E no protocolo; 10 armadilhas novas; 4 itens no
  checklist; 5 linhas no troubleshoot.
- Regressão: 40 → 77 casos (núcleo, validação, container com devolução e os nós Code do n8n rodando com o n8n simulado).

## v1.1.5 — 2026-09-29

- Armadilhas: integração nativa da loja (Nuvemshop) com a mesma conta do Google Ads; container herdado de outro cliente.

## v1.1.4 — 2026-09-29

- **Nomenclatura dos templates igual à dos containers recentes da operação:** `wGTM | <domínio>` (era `WEB |`) e
  `sGTM | <domínio>`; pastas ⚙️ Configurações · 🟢 Google Ads · 🟠 GA4 · 🔵 Meta Ads · 🔵 Meta CAPI · 🟣 Acionadores ·
  🧩 Data Layer (Cookies entrou em Configurações; 7 pastas no Web); `00.0 | Google Ads - Vinculador de conversões`,
  `00.0 | Data Layer - Persist Form Data`, `PageView` sem espaço. A padronização mora no gerador dos templates, então
  regerar não desfaz.

## v1.1.3 — 2026-09-29

- README com desenhos animados no estilo do claude-seo, em vermelho V4: capa (comandos digitados; o evento indo ao
  Meta pelo navegador e pelo servidor com o mesmo event_id; a venda voltando do CRM), fluxo do sinal pelos três modos
  até a venda voltar, e o contrato de eventos (de onde sai cada evento, destinos e valor proxy do Modelo A).
- `scripts/desenhos.py` gera os três SVG de `assets/`; a regressão confere que batem com o gerador.

## v1.1.2 — 2026-09-29

- Armadilha e linha no troubleshoot: o mesmo acionador como disparo e como exceção da tag (G5 da auditoria de GTM).

## v1.1.1 — 2026-09-28

- `README.md`: seção "Como funciona", uma linha por fase com o que entra, o que a skill faz, a ferramenta, o que
  sai e o que trava.
- `tests/regressao.py`: confere que todo script citado no README existe (nesta skill ou na `sprint-growth`).

## v1.1.0 — 2026-09-28

Aprendizados de cinco sprints growth (SaaS de obra, indústria, brindes, distribuidora de peças, móveis planejados)
e de auditorias de GTM levados para a skill, e o repositório público limpo de dados do cliente piloto.

### Segurança
- **Nenhum ID de cliente no repositório.** Os containers do piloto viraram `templates/gtm/web.json` e
  `templates/gtm/server.json`, com marcadores (`__META_PIXEL_ID__`, `__LABEL_LEAD__`, `__SSGTM_URL__`,
  `__REGRA_MQL__`...) no lugar de Pixel, Google Ads, GA4, rótulos, Stape, domínio, Clarity e Test Event Code. O caso
  real fica em `clientes/` (git local, fora da cópia pública). A seção 11 do checklist deixou de listar os IDs
  reais e passou a exigir container gerado pelo template.
- O brief do gerador recusa token da CAPI: o token vai direto no GTM Server.

### Adicionado
- `scripts/gerar_containers.py`: preenche os marcadores a partir do brief e valida antes de entregar. Bloqueia
  marcador sobrando, formato de Pixel/Ads/GA4, rótulo vazio, só com dígitos (ID e rótulo trocados) ou repetido, URL
  do servidor de exemplo ou sem https, Test Event Code em produção, seletor vazio, contagem de pastas e tags,
  `inheritEventName` diferente de `"override"`. Sem critério de MQL, tira tags, variável e acionador de MQL.
- `templates/brief_exemplo.json` e `templates/planilha/` (planilha de leads e Apps Script, sem dado do piloto).
- `referencias/armadilhas.md`: 25 erros vistos em cliente em quatro grupos (tags e containers, página e
  consentimento, conta de anúncios e GA4, volta da venda), cada um com como detectar e o que fazer.
- `tests/regressao.py`: 36 casos sem rede (anonimato dos templates, cada validação, sem MQL, Clarity, a regra de
  MQL executada em JavaScript, CLI ponta a ponta).
- `README.md` com o desenho do workflow (três modos, saída de cada fase na seta, o loop fechando em
  "erro novo vira armadilha e teste").
- `playbook/caso-piloto-carpetes.md`: o caso piloto sem identificadores.

### Alterado
- `latest.md`: Fase 4 pelo gerador; Modo 2 com os testes automáticos da `sprint-growth` (`gtm_auditoria.py`,
  `teste_disparo.py`, `teste_formulario.py`) e as MCPs do n8n; 10 erros novos na tabela do troubleshoot.
- `canonico/checklist-auditoria.md`: seções 12 (conta de anúncios e GA4) e 13 (origem até o CRM e volta da venda).
- `SKILL.md`: versão, ferramentas, regras de segurança e fechamento.
- Removidos `v1.0.0.md` (fica na tag `v1.0.0`) e `artefatos-referencia/` (virou `templates/` e `clientes/`).

## v1.0.0 — 2026-05-17

### Adicionado
- Skill inicial com 3 modos: planejar, auditar, troubleshoot
- Contrato de dados (canonico/padrao-tracking.md) — em construção
- Checklist de auditoria (canonico/checklist-auditoria.md) — em construção
- Implementação A (Sheets) — em construção, baseada no caso piloto
- Implementação B (CRM Kommo) — em construção
- Playbook caso cliente piloto (carpetes B2B) — em construção
- Aula teórica em slides — em construção
- Base de conhecimento de erros conhecidos (em latest.md)

### Refinamento — 2026-05-17 (pós-criação)

- **Skill renomeada** para `tracking-web-and-capi` (era `tracking-stack`; passou brevemente por `tracking-inside-sales-web-and-api`). Nome final reflete escopo geral: web pixel + CAPI server, aplicável a qualquer nicho.
- **Terminologia corrigida**: "agência" → "V4 Company" em 10 referências internas (V4 é assessoria, não agência). Mantida apenas em `aula/slides.md` L22 onde o contexto é mercado em geral.
- **MODO 1 — Fase 1, Bloco D ampliado** (de 4 inputs para 7 sub-blocos):
  - D.1 Identificadores das plataformas (Pixel, Google Ads, GA4)
  - D.2 Conversion Labels (Lead, MQL, Contact)
  - D.3 Meta CAPI (Access Token com aviso de segurança + Test Event Code)
  - D.4 SSGTM (URL, plano, custom domain)
  - D.5 Cliente (domínio, LP, obrigado, WhatsApp)
  - D.6 Selectors do form
  - D.7 Critério MQL (com opção "não aplicável")
- **MODO 1 — Fase 4 reescrita** como "Geração dos JSONs (Web + Server)":
  - Princípio canônico explícito (nomenclatura, emojis e estrutura de pastas **não mudam** entre clientes)
  - Mapa formal de substituição Web (13 placeholders → Bloco D)
  - Mapa formal de substituição Server (4 placeholders → Bloco D)
  - 5 validações pré-entrega obrigatórias (grep zero-placeholder, contagem de tags, emojis presentes, JSON válido, `inheritEventName: "override"`)
  - Entrega definida: `gtm-web-<cliente>.json` + `gtm-server-<cliente>.json` + resumo auditável
- **Checklist de auditoria — Seção 11 nova**: "Templates limpos (zero placeholder do piloto)" com 11 itens, todos bloqueantes. Previne vazamento de IDs/tokens/selectors do piloto em outros clientes.
- **v1.0.0.md sincronizado** com latest.md (mesma versão durante a fase de construção).

### Notas
- Versão inicial baseada no caso piloto cliente piloto (carpetes B2B)
- Artefatos de referência em `artefatos-referencia/`
- Conteúdo de canonico/ e implementacoes/ a ser preenchido nas próximas iterações
