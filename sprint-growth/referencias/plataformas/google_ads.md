# Google Ads

**Leitura:** MCP do Google Ads (GAQL) e `scripts/ads_auditoria.py` (alertas A1–A10) pelo endpoint da MCC do cliente
(`googleads_diretas`, `googleads_squad`, `googleads_nayara`). **Escrita:** webhook do n8n por
`scripts/ads_escrita.py` (validateOnly por padrão; `--aplicar` só com ok). Armadilhas: seção Mídia e Execução.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| A1 | Conversão principal com registro no período | google-ads | `ads_auditoria.py` | principal zerada (rótulo errado ou tag quebrada) | crítica |
| A2 | Uma conversão principal por categoria | google-ads | `ads_auditoria.py` | Lead e MQL principais: cada MQL conta 2 | alta |
| A3 | Principais de YouTube, ligação ou importação sem uso | google-ads | `ads_auditoria.py` | lance aprendendo com sinal que não é lead | média |
| A4 | Campanhas estranhas, criadas em rajada ou com palavras de cassino | google-ads | `ads_auditoria.py` | conta invadida | crítica |
| A5 | Lances sem teto e local "presença ou interesse" | google-ads | `ads_auditoria.py` | gasto fora da região; CPC sem limite | média |
| A6 | Índice de qualidade ≤ 3 com gasto | google-ads | `ads_auditoria.py` | página ou anúncio fora do termo | média |
| A7 | Parcela de impressões perdida por classificação | google-ads | `ads_auditoria.py` | perde leilão por nota, não por verba | média |
| A8 | Sitelinks apontando para âncora ou página que existe | google-ads | `ads_auditoria.py --site` | 12 sitelinks para `#1`…`#6` caindo no topo | baixa |
| A9 | Troca de destino no período e custo por lead de cada destino | google-ads | `ads_auditoria.py` | destino novo com custo por lead muito maior | média |
| A10 | Orçamento × gasto | google-ads | `ads_auditoria.py` | orçamento abaixo do gasto real ou limitado o mês todo | baixa |
| A11 | Metas de conversão da campanha com a categoria certa como lance | google-ads | GAQL `campaign_conversion_goal` | campanha só contando ligação; formulário fora do lance | alta |
| A12 | Conversão da plataforma × pessoas únicas do backup | google-ads | GAQL por ação × `base/pessoas.json` | clique no WhatsApp, ligação ou campanha inteligente inflando "leads" | alta |
| A13 | Termos de pesquisa por intenção e gasto | google-ads | `scripts/termos_negativas.py` | gasto em login, emprego, concorrente, fora do produto | média |
| A14 | Negativas que bloqueiam termo que converte | google-ads | `termos_negativas.py` (recusadas) + GAQL de negativas | negativa pegando termo com conversão | alta |
| A15 | Palavras com volume e correspondência coerente | google-ads | GAQL `keyword_view` + Planejador (usuário confere) | palavra sem volume ou ampla sem negativas | média |
| A16 | Anúncios: força, título com o termo, promessa que a página sustenta, caminho exibido | google-ads | GAQL `ad_group_ad` + `curl` da página | "50% Off" que a página não mostra | média |
| A17 | Recursos: frases de destaque, snippets, imagem, logotipo, formulário | google-ads | GAQL `campaign_asset`, `asset` | campanha de pesquisa sem recursos | baixa |
| A18 | Rede, idioma, programação e dispositivo | google-ads | GAQL `campaign.network_settings`, `ad_schedule_view` | Display ou parceiros ligados em campanha de pesquisa | média |
| A19 | Estratégia de lance × volume e valor de conversão | google-ads | GAQL `campaign.bidding_strategy_type` | CPA desejado com < 30 conversões/mês; ROAS sem valor | média |
| A20 | Marcação automática (gclid) e sufixo de URL | google-ads | GAQL `customer.auto_tagging_enabled`, `final_url_suffix` | lead chegando sem gclid | alta |
| A21 | Conversão importada do GA4 e tag nativa ao mesmo tempo | google-ads | GAQL `conversion_action.type` | a mesma ação contada pelas duas | alta |
| A22 | Conversões avançadas e venda de volta (offline) | google-ads | GAQL + configuração da ação | Google otimizando por lead, sem SQL nem venda | média |
| A23 | Acessos e verificação em duas etapas | google-ads | GAQL `customer_user_access` + interface | usuário desconhecido; admin sem 2 etapas | alta |
| A24 | Anúncios reprovados, restrição de política, conta suspensa | google-ads | GAQL `ad_group_ad.policy_summary` | anúncio principal reprovado ou limitado | alta |
| A25 | Recomendações aplicadas automaticamente | google-ads | interface (Recomendações → aplicação automática) | Google mudando lance e palavra sozinho | média |
| A26 | Performance Max e Demand Gen: grupos, sinais, marca, expansão de URL | google-ads | GAQL `asset_group`, `campaign` | PMax comprando a própria marca; URL expandida para página errada | média |
| A27 | Leilão: concorrentes e sobreposição | google-ads | interface (Informações do leilão) | concorrente novo tomando parcela | baixa |
| A28 | Listas de público e exclusão de clientes | google-ads | GAQL `user_list` | remarketing sem lista ou cliente recebendo anúncio | baixa |
| A29 | Ativos da conta sem resíduo de invasão (telefone, sitelinks, conversões de outro país ou empresa) | google-ads | GAQL `customer_asset` e `campaign_asset` (CALL com `country_code`), `conversion_action` | telefone de outro país no nível da conta; conversão criada por invasor | crítica |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-A1 | Deixar uma conversão principal por categoria; as outras viram secundárias | A2, A3, A12, A21 | `ads_escrita.py` (`conversion_action.primary_for_goal`); hospedadas pela meta da campanha (CX-A2) | validateOnly; lista de ações antes e depois | R3 | marcar a ação como principal de novo | GAQL: uma principal por categoria; conversões de 7 dias × backup |
| CX-A2 | Metas da campanha: categoria certa como lance, a errada fora | A11, A3 | `ads_escrita.py` (`campaign_conversion_goal.biddable`) | validateOnly | R3 | biddable de volta | GAQL das metas; conversões da campanha em 7 dias |
| CX-A3 | Segurança: pausar campanhas e palavras invasoras, remover acessos, exigir 2 etapas | A4, A23 | `ads_escrita.py` (status PAUSED); acessos e 2 etapas pela interface | lista do que será pausado com o gasto | R1 | reativar (se era legítimo) | GAQL de status; `change_event` sem nova rajada |
| CX-A4 | Local por presença e teto de lance | A5 | `ads_escrita.py` (`geo_target_type_setting`, limites) | validateOnly | R2 | valor anterior guardado na memória | gasto fora da região = 0 em 7 dias |
| CX-A5 | Negativas em lista compartilhada | A13 | `ads_escrita.py --negativas` | lista inteira com o gasto que bloqueia; recusadas fora | R1 | remover a negativa | gasto nos termos bloqueados = 0; conversões estáveis |
| CX-A6 | Remover negativa que bloqueia termo convertido | A14 | `ads_escrita.py` (remove critério) | termo e conversões que voltam a entrar | R1 | adicionar de novo | termo recebendo impressão em 7 dias |
| CX-A7 | Palavras novas ou correspondência ajustada, só com volume confirmado | A15, A6 | `ads_escrita.py` (`ad_group_criterion`) | usuário confere volume no Planejador | R2 | pausar a palavra | impressões e CPC da palavra em 7 dias |
| CX-A8 | Anúncio novo com o termo no título e promessa que a página sustenta; pausar o antigo depois da aprovação | A16, A6, A7 | `ads_escrita.py` (cria `ad_group_ad`) | validateOnly; textos mostrados ao usuário | R2 | reativar o antigo | aprovação; CTR e índice de qualidade em 14 dias |
| CX-A9 | Recursos: sitelinks para URL real, frases, snippets, imagem | A8, A17 | `ads_escrita.py` (`asset` + `campaign_asset`) | cada URL responde 200 | R1 | remover o recurso | GAQL do recurso aprovado |
| CX-A10 | Rede, idioma, programação e dispositivo | A18 | `ads_escrita.py` (`network_settings`, critérios) | validateOnly | R2 | valor anterior | gasto em Display/parceiros = 0 |
| CX-A11 | Estratégia de lance compatível com volume e valor | A19, A5 | `ads_escrita.py` (`bidding_strategy`) | volume de conversão dos 30 dias mostrado | R3 | estratégia anterior guardada | leitura depois de 2 semanas: CPA e volume |
| CX-A12 | Marcação automática e sufixo de URL com UTM | A20 | `ads_escrita.py` (`customer.auto_tagging_enabled`, `final_url_suffix`) | `teste_formulario.py` com gclid antes | R2 | valor anterior | lead novo chega com gclid (backup) |
| CX-A13 | Orçamento redistribuído pelo impacto em R$ | A10, A7, A27 | `ads_escrita.py` (`campaign_budget`) | valores exatos antes e depois | R2 | orçamento anterior | gasto e parcela perdida por orçamento em 7 dias |
| CX-A14 | Destino de volta para a página com menor custo por lead | A9 | `ads_escrita.py` (anúncio novo com a URL final) | custo por lead dos dois destinos | R2 | reativar o anúncio anterior | custo por lead do destino em 14 dias |
| CX-A15 | SQL e venda de volta ao Google (upload offline ou CSV) | A22 | `ads_escrita.py` (upload); conta nova: CSV em Metas → Conversões → Uploads | 3 linhas de teste com gclid real | R2 | desativar a ação offline | conversões offline aparecendo com o valor |
| CX-A16 | Corrigir anúncio reprovado ou contestar | A24 | interface (ou anúncio novo por CX-A8) | motivo da política | R2 | — | anúncio aprovado |
| CX-A17 | Desligar a aplicação automática de recomendações | A25 | interface | lista do que está ligado | R1 | religar | `change_event` sem mudança do Google |
| CX-A18 | PMax: excluir a marca, ajustar sinais, controlar expansão de URL | A26 | interface e API onde houver | termos de marca na PMax | R2 | valores anteriores | gasto de marca na PMax = 0 |
| CX-A19 | Públicos: excluir clientes, criar listas de remarketing | A28 | `ads_escrita.py` (`user_list`, exclusão) | tamanho das listas | R2 | remover a exclusão | alcance e custo do remarketing |
| CX-A20 | Desvincular o ativo estranho e incluir o telefone real | A29 | `ads_escrita.py` (`customerAssetOperation.remove`; o ativo fica na biblioteca) | validateOnly | R2 | vincular o ativo de novo | GAQL: vínculo REMOVED |

## Não dá pela API (vai pela interface)

- Conversões hospedadas pelo Google (YouTube, ações locais, ligações de campanha inteligente, metas do Universal
  Analytics): MUTATE_NOT_ALLOWED. Tire do lance pela meta da campanha (CX-A2).
- Upload de conversão por clique em conta nova (CUSTOMER_NOT_ALLOWLISTED): CSV com
  `Parameters:TimeZone=America/Sao_Paulo` e colunas Google Click ID, GBRAID, Conversion Name, Conversion Time,
  Conversion Value, Conversion Currency.
- Verificação em duas etapas, aplicação automática de recomendações e Informações do leilão.
- Planejador de palavras-chave sem acesso Basic: o usuário confere o volume antes de a palavra subir.
