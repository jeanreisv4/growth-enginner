# Microsoft Clarity

**Leitura:** `scripts/clarity.py` (Data Export API: 10 chamadas por projeto por dia, só as últimas 24–72 h) e, para
ver o que o número mostra, gravações e mapas de calor pela interface. **Escrita:** não há; as correções são na
página, no GTM ou na mídia.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| C1 | Sessões de robô e de qual canal | clarity | `clarity.py resumo` (C1) | mais de 30% de robô; robô vindo de mídia paga | alta |
| C2 | Clique de raiva nas páginas de mídia | clarity | `clarity.py resumo` (C2) + gravações | 5%+ das sessões | média |
| C3 | Clique morto (parece botão e não é) | clarity | `clarity.py resumo` (C3) + mapa de calor | 10%+ das sessões | média |
| C4 | Volta rápida (promessa do anúncio × página) | clarity | `clarity.py resumo` (C4) | 10%+ das sessões na LP do anúncio | alta |
| C5 | Erro de script | clarity | `clarity.py resumo` (C5) + console | 5%+ das sessões; formulário pode estar quebrado | alta |
| C6 | Rolagem no celular × computador | clarity | `clarity.py resumo` (C6) | celular abaixo de 70% do computador; formulário abaixo da dobra | média |
| C7 | Clarity instalado em todas as páginas de mídia, com mascaramento | clarity | página renderizada + configurações do projeto | LP sem Clarity; dado pessoal visível nas gravações | média |
| C8 | Integração do Clarity com o GA4 | clarity | configurações do projeto | segmentos do GA4 indisponíveis nas gravações | baixa |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-C1 | Cortar a origem do robô (posicionamento, parceiro de pesquisa, rede) | C1 | `meta_ads.md` CX-M7 ou `google_ads.md` CX-A10 | robôs por canal | R2 | reverter a exclusão | robôs abaixo de 30% na próxima coleta |
| CX-C2 | Consertar o elemento de raiva ou clique morto (ou torná-lo clicável) | C2, C3 | pedido a quem edita a página, com a gravação | gravação e elemento marcados | R2 | versão anterior da página | taxa do alerta na próxima coleta |
| CX-C3 | Alinhar a promessa do anúncio com o que aparece acima da dobra | C4 | `paginas.md` CX-P2 e anúncio (CX-A8 ou CX-M5) | print do anúncio e da página | R2 | textos anteriores | volta rápida caindo |
| CX-C4 | Corrigir o erro de script | C5 | pedido ao desenvolvedor com o erro do console | erro reproduzido | R2 | — | erro de script abaixo de 5% |
| CX-C5 | Formulário ou botão principal acima da dobra no celular | C6 | `paginas.md` CX-P4 | print do celular | R2 | layout anterior | rolagem e conversão no celular |
| CX-C6 | Instalar pelo GTM em todas as páginas e ligar o mascaramento | C7 | MCP `gtm` (tag do Clarity) + configurações do projeto | páginas sem Clarity listadas | R1 | pausar a tag | sessões aparecendo nas páginas |
| CX-C7 | Ligar a integração com o GA4 | C8 | configurações do projeto | propriedade certa | R1 | desligar | segmentos do GA4 no Clarity |
