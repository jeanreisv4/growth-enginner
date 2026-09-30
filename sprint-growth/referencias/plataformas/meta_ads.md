# Meta Ads

**Leitura:** conector Meta Ads do claude.ai (entidades, insights, anomalias, conjunto de dados, logs de atividade)
ou exports CSV. **Escrita:** o mesmo conector (`ads_update_entity`, `ads_activate_entity`, `ads_create_*`,
`ads_pixel_event_*`, públicos), só no modo correção e com ok; ação que o conector marca como
`requires_user_confirmation` passa pelo usuário. Pixel e CAPI no navegador e no servidor estão em `gtm.md`.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| M1 | Gasto, resultado e custo por campanha, conjunto e anúncio, mês a mês, pelo ID | meta-ads | conector (`ads_get_ad_entities`, insights) | campanha renomeada lida como nova; custo subindo sem causa | alta |
| M2 | Evento de otimização do conjunto é o que vira venda | meta-ads | conector (conjunto: `optimization_goal`, evento) | otimizando clique ou conversa quando a venda vem do formulário | alta |
| M3 | Criativo × qualidade do lead (porte, CNPJ, campo de qualificação) | meta-ads | `base/pessoas.json` × anúncio | anúncio barato trazendo lead fora do perfil | alta |
| M4 | Segunda conta de anúncios ou campanhas fora do export | meta-ads | IDs do backup × IDs da conta | sufixo de ID diferente; leads "sem permissão" | média |
| M5 | Fadiga: frequência, CTR caindo, anúncio antigo | meta-ads | insights por semana | frequência > 3 em público frio; CTR em queda | média |
| M6 | Estrutura: conjuntos fragmentados, aprendizado limitado, sobreposição de públicos | meta-ads | conector (status de aprendizado, orçamentos) | muitos conjuntos com pouca verba e "aprendizado limitado" | média |
| M7 | Públicos: exclusão de clientes e leads, remarketing × frio | meta-ads | conector (públicos, custo por lead por público) | remarketing mais caro que o frio; cliente recebendo anúncio | média |
| M8 | Posicionamentos e dispositivos | meta-ads | insights por posicionamento | Audience Network trazendo lead ruim ou robô | média |
| M9 | Formulário nativo: perguntas de qualificação, alta intenção, campo de MQL | meta-ads | conector (formulários) + backup | formulário "mais volume" sem pergunta; MQL que parou de marcar | alta |
| M10 | Parâmetros de URL com nome, não ID | meta-ads | conector (`url_tags` do criativo) | utm_source 1202… vira "Unassigned" no GA4 | média |
| M11 | Anomalias e quedas com data | meta-ads | `ads_insights_anomaly_signal`, `ads_insights_performance_trend`, logs | queda sem mudança nossa registrada | média |
| M12 | Anúncios reprovados, limite de gasto, pagamento | meta-ads | conector (`ads_get_errors`, status) | anúncio principal reprovado; conta limitada | alta |
| M13 | Qualidade do conjunto de dados (EMQ) de Lead e Purchase | medicao | `ads_get_dataset_quality` | EMQ < 6 no evento que otimiza | alta |
| M14 | Deduplicação Pixel + CAPI e eventos fantasma | medicao | `ads_get_dataset_stats`, `ads_pixel_event_read` | evento contado 2 vezes; add-to-cart em página sem carrinho | alta |
| M15 | Conversões personalizadas e eventos padrão | medicao | `ads_get_customconversions` | regra de URL que não bate com a página de obrigado | média |
| M16 | Acessos ao Business Manager, parceiros e 2 etapas | meta-ads | interface do Business Manager | pessoa ou parceiro desconhecido com acesso total | alta |
| M17 | Clique para WhatsApp: a origem do anúncio chega ao CRM | meta-ads | conversas no CRM (`sourceReferral`/ctwaId) | conversa de anúncio sem origem no CRM | média |
| M18 | Referência de custo do setor e do leilão | meta-ads | `ads_insights_industry_benchmark`, `ads_insights_auction_ranking_benchmarks` | CPM ou CPL muito acima do setor | baixa |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-M1 | Pausar anúncio ou conjunto com custo por lead qualificado ruim | M1, M3, M5, M8 | conector `ads_update_entity` (status PAUSED) | lista com gasto e leads qualificados de cada um | R1 | `ads_activate_entity` | custo por lead qualificado da conta em 7 dias |
| CX-M2 | Redistribuir orçamento para o que traz lead qualificado mais barato | M1, M3, M18 | conector `ads_update_entity` (orçamento) | valores antes e depois | R2 | orçamento anterior | custo por lead qualificado em 7 dias |
| CX-M3 | Evento de otimização certo em conjunto novo (não editar o que está rodando) | M2 | conector `ads_create_ad_set` + anúncios copiados | evento com volume (≥ 50/semana ideal) | R3 | reativar o conjunto antigo | leitura após o aprendizado: custo por venda |
| CX-M4 | Consolidar estrutura: menos conjuntos, orçamento na campanha | M6 | conector (campanha nova) | orçamento e públicos mostrados | R3 | reativar a estrutura antiga | saída do aprendizado; custo por lead |
| CX-M5 | Criativos novos a partir dos vencedores, criados pausados para revisão | M5, M3 | conector `ads_create_creative`, `ads_create_ad` | textos e imagens aprovados pelo usuário | R2 | pausar | CTR e custo por lead qualificado em 7 dias |
| CX-M6 | Públicos: excluir clientes e leads; remarketing com janela certa | M7 | conector (`ads_create_custom_audience`, atualização) | tamanho do público | R2 | remover a exclusão | alcance e custo por lead do remarketing |
| CX-M7 | Tirar posicionamento que traz lead ruim | M8 | conector (conjunto novo ou atualização) | leads por posicionamento | R2 | posicionamento de volta | custo por lead qualificado |
| CX-M8 | Formulário nativo com perguntas de qualificação e alta intenção | M9 | interface (formulário novo ligado ao anúncio) | perguntas aprovadas pelo cliente | R2 | formulário anterior | taxa de MQL do formulário |
| CX-M9 | Parâmetros de URL com nome da campanha, conjunto e anúncio | M10 | conector (`url_tags` do anúncio ou criativo) | exemplo de URL final | R1 | parâmetros anteriores | GA4 sem "Unassigned" da Meta em 48 h |
| CX-M10 | Achar a mudança por trás da anomalia e voltar | M11 | `ads_account_get_activity_logs` + atualização da entidade | log com data e autor | R2 | valor anterior | métrica de volta ao nível |
| CX-M11 | Anúncio reprovado, limite ou pagamento | M12 | interface | motivo | R2 | — | anúncio entregando |
| CX-M12 | Evento e conversão personalizada certos | M15 | conector `ads_pixel_event_create/update` | regra de URL testada | R2 | evento anterior | evento aparecendo no conjunto de dados |
| CX-M13 | Acessos: remover desconhecidos, exigir 2 etapas | M16 | interface do Business Manager | lista de acessos | R2 | re-adicionar | lista final conferida |
| CX-M14 | Segunda conta: pedir acesso ou tirar do realizado V4 | M4 | pedido ao cliente; regra de atribuição na memória | IDs das campanhas de fora | R1 | — | realizado sem a outra conta |

EMQ e deduplicação (M13, M14) se corrigem no servidor e no navegador: `gtm.md` (CX-G11, CX-G12). A origem do
clique para WhatsApp (M17) se corrige no CRM: `crm_integracao.md` (CX-I9).
