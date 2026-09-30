# Mercado

**Leitura:** WebSearch, WebFetch, termos de pesquisa do Google Ads e Biblioteca de Anúncios do Meta. **Escrita:**
nenhuma; o mercado corrige a oferta e a mensagem, na página e no anúncio.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| MK1 | Concorrentes que aparecem nos termos de pesquisa e na memória | mercado | GAQL `search_term_view` + memória | concorrente comprando o mesmo termo sem ser mapeado | média |
| MK2 | Preço com unidade (mês, usuário, obra) | mercado | página do concorrente, com URL e data | cliente muito acima sem explicar por quê | média |
| MK3 | Oferta de entrada: teste grátis, prazo, garantia | mercado | página do concorrente | concorrente com teste e o cliente sem | média |
| MK4 | Provas: clientes, números, selos | mercado | página do concorrente | cliente sem prova nenhuma | baixa |
| MK5 | Anúncios ativos e ângulo no Meta | mercado | Biblioteca de Anúncios (`ads_library_search`) | concorrente com ângulo que o cliente não usa | baixa |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-MK1 | Mensagem e oferta do anúncio ajustadas ao que o mercado mostra | MK1, MK3, MK5 | `google_ads.md` CX-A8 e `meta_ads.md` CX-M5 | textos aprovados pelo cliente | R2 | textos anteriores | CTR e custo por lead |
| CX-MK2 | Preço, oferta de entrada e provas na página | MK2, MK3, MK4 | `paginas.md` CX-P11 | conteúdo aprovado | R2 | versão anterior | conversão da LP |
