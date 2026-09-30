# GTM web e servidor (Stape), Pixel e CAPI

**Leitura:** MCP `gtm` (contas, containers, workspaces, tags, acionadores, variáveis, versões) e
`scripts/gtm_auditoria.py` (G1–G5); testes `scripts/teste_disparo.py` e `scripts/teste_formulario.py`.
**Escrita:** MCP `gtm` no workspace → versão com nome claro → ok → publicar. Container do zero ou refeito: skill
`tracking-web-and-capi` (templates com marcadores e `gerar_containers.py`), nunca cópia de outro cliente.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| G1 | Rótulo de conversão do Google Ads existe na conta | medicao | `gtm_auditoria.py` | um caractere a menos zerou o Lead | crítica |
| G2 | GA4 do servidor não repassa evento do Meta | medicao | `gtm_auditoria.py` | PageView/Lead/Contact do Meta viram evento no GA4 | alta |
| G3 | Tag pausada ou sem acionador | medicao | `gtm_auditoria.py` | conversão que nunca sai | média |
| G4 | Duas tags de conversão com o mesmo rótulo | medicao | `gtm_auditoria.py` | conversão contada 2 vezes | alta |
| G5 | Mesmo acionador como disparo e exceção | medicao | `gtm_auditoria.py` | a exceção vence e a tag nunca dispara | alta |
| G6 | Container herdado de outro cliente | medicao | MCP `gtm` (valor de cada variável constante) | Pixel, domínio, ID de conta ou UA de outra empresa | alta |
| G7 | Mesma conta instalada duas vezes (integração nativa da loja + GTM) | medicao | hits no navegador (parâmetro `gtm=`), `dataLayerTN` | tags do GTM param de enviar | alta |
| G8 | Conversion Linker em todas as páginas | medicao | MCP `gtm` (tag e acionador) | gclid não guardado no cookie | alta |
| G9 | Consentimento: tags esperando aceite; Consent Mode v2 | medicao | `teste_formulario.py` (GTM carregou?), configuração de consentimento | GTM só carrega depois do aceite de marketing | alta |
| G10 | Servidor: domínio próprio, cliente GA4, plano e erros no Stape | medicao | MCP `gtm` (container servidor) + painel do Stape | domínio de terceiro; cota estourada; erro 5xx | alta |
| G11 | Test Event Code em produção e token da CAPI exposto | medicao | MCP `gtm` (variáveis e tags) | eventos viram teste; token visível no container web | crítica |
| G12 | event_id compartilhado entre Pixel e CAPI | medicao | MCP `gtm` + `ads_get_dataset_stats` | deduplicação zerada | alta |
| G13 | Dados do usuário normalizados para EMQ e conversões avançadas | medicao | MCP `gtm` (variáveis de e-mail e telefone) | EMQ baixo; telefone sem +55 | média |
| G14 | Nomenclatura, pastas e prefixos (padrão wGTM/sGTM) | medicao | MCP `gtm` (pastas e nomes) | tag sem prefixo; ninguém sabe o que é | baixa |
| G15 | Workspace com mudança não publicada e histórico de versões | medicao | MCP `gtm` (workspaces, versões) | mudança parada no rascunho; versão sem nome | média |
| G16 | Disparo real no navegador com o rótulo certo | medicao | `teste_disparo.py` | tag que não sai ou sai com rótulo errado | alta |
| G17 | Formulário envia UTM, gclid e fbclid | medicao | `teste_formulario.py` | POST sem origem | alta |
| G18 | Clique no WhatsApp (link, botão, pop-up) vira evento | medicao | `teste_disparo.py` + MCP `gtm` | pop-up que redireciona para wa.me sem disparar tag | média |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-G1 | Corrigir rótulo e ID de conversão (variável ou tag) | G1, G4, G16, A1 | MCP `gtm` no workspace → versão → ok → publicar | versão criada compila; contagem de tags igual | R2 | publicar a versão anterior | `teste_disparo.py` no `gtm.js` publicado; conversões em 48 h |
| CX-G2 | Tirar o GA4 do servidor dos eventos do Meta | G2, GA4 | MCP `gtm` (acionador ou pausa da tag no servidor) | lista de eventos afetados | R2 | versão anterior | contagem única no GA4 em 48 h |
| CX-G3 | Ligar acionador ou reativar tag | G3, G16 | MCP `gtm` | tag e acionador mostrados | R1 | pausar de novo | `teste_disparo.py` |
| CX-G4 | Tirar o acionador da exceção | G5 | MCP `gtm` (`blockingTriggerId`) | exceção que fica e a que sai | R2 | versão anterior | `teste_disparo.py` depois de publicar |
| CX-G5 | Limpar o container herdado ou refazer pelo template | G6, G14 | MCP `gtm` (variáveis certas) ou skill `tracking-web-and-capi` | lista de valores trocados; brief completo | R3 | versão anterior | todas as conversões com `teste_disparo.py` |
| CX-G6 | Um caminho só: integração nativa ou GTM; pausar o outro | G7 | configuração da loja ou MCP `gtm` | hits antes (de onde sai cada um) | R2 | religar o que foi pausado | hits saindo só de um caminho |
| CX-G7 | Conversion Linker em todas as páginas | G8 | MCP `gtm` | tag e acionador All Pages | R1 | pausar | cookie `_gcl_aw` gravado com gclid de teste |
| CX-G8 | Consent Mode v2 e GTM fora da categoria de marketing do banner | G9, GA5 | MCP `gtm` (consentimento) + construtor (`paginas.md` CX-P9) | `teste_formulario.py` antes | R2 | configuração anterior | GTM carrega sem aceite; sinais de consentimento chegando |
| CX-G9 | Servidor em domínio próprio, cliente certo e plano do Stape | G10 | painel do Stape + MCP `gtm` servidor | DNS e cliente mostrados | R2 | domínio anterior | requisições 200 no Stape |
| CX-G10 | Remover Test Event Code; token da CAPI só no servidor; trocar token exposto | G11 | MCP `gtm` + gerenciador de eventos do Meta | onde o token aparece | R2 | — | eventos fora de "teste"; token antigo revogado |
| CX-G11 | event_id igual no Pixel e na CAPI | G12, M14 | MCP `gtm` (variável de event_id nas duas tags) | tags afetadas | R2 | versão anterior | taxa de deduplicação no conjunto de dados |
| CX-G12 | E-mail e telefone normalizados e hasheados no servidor; fbp e fbc | G13, M13 | MCP `gtm` servidor | formato de exemplo | R2 | versão anterior | EMQ subindo em 7 dias |
| CX-G13 | Publicar ou descartar o rascunho, com nome de versão claro | G15 | MCP `gtm` | diferença do workspace mostrada | R2 | versão anterior | versão publicada com nome |
| CX-G14 | Formulário com campos ocultos de origem e script de atribuição; purchase com transaction_id | G17, A20, GA13 | página (`paginas.md` CX-P5) + MCP `gtm` | `teste_formulario.py` antes | R2 | versão anterior | `teste_formulario.py` mostra UTM e gclid no POST |
| CX-G15 | Evento de clique no WhatsApp (link e pop-up) | G18, P10 | MCP `gtm` (acionador de clique ou evento do pop-up) | seletor testado | R2 | versão anterior | `teste_disparo.py` com o clique |

Publicar GTM passa pelo modo automático do Claude Code: se ele negar, pare e deixe a decisão com o usuário.
