# GA4

**Leitura:** `analytics-mcp` (relatórios, eventos por página, canais) e MCP `ga4admin` (listas de eventos
principais, vínculos, dimensões, fluxos). **Escrita:** `ga4admin` (eventos principais, vínculo com Google Ads,
dimensões, propriedade) só no modo correção e com ok; o resto pela interface.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| GA1 | Eventos principais são os que disparam de verdade | medicao | `ga4admin` (eventos principais) × `analytics-mcp` (contagem) | evento de template marcado; evento real desmarcado | alta |
| GA2 | Vínculo com o Google Ads ativo | medicao | `ga4admin` (vínculos) | sem vínculo: sem público nem importação | alta |
| GA3 | "Unassigned" e "(not set)" nos canais | medicao | `analytics-mcp` por canal e origem/mídia | UTM com ID; origem sem regra de canal | alta |
| GA4 | Evento duplicado (navegador + servidor) | medicao | `analytics-mcp` eventos por fluxo + GTM servidor | GA4 do servidor repassando evento do Meta | alta |
| GA5 | Cobertura: GA4 carrega antes do aceite de cookies | medicao | sessões GA4 × cliques do Ads; `teste_formulario.py` | GA4 vendo ~25% da LP | alta |
| GA6 | Tráfego interno e referências indesejadas | medicao | interface (filtros de dados, referências) | gateway de pagamento ou domínio próprio como origem | média |
| GA7 | Domínios cruzados (site, LP, checkout) | medicao | `analytics-mcp` referências próprias | sessão partida ao trocar de domínio | média |
| GA8 | Retenção de dados, fuso e moeda | medicao | `ga4admin` (propriedade) | retenção de 2 meses; fuso fora de São Paulo | baixa |
| GA9 | Dimensões personalizadas usadas nos relatórios | medicao | `ga4admin` (dimensões) | parâmetro do evento sem dimensão (MQL, formulário) | baixa |
| GA10 | Medição otimizada gerando evento falso | medicao | `analytics-mcp` form_start/form_submit × leads | form_submit sem lead correspondente | média |
| GA11 | Sessões do Google × cliques do Google Ads | medicao | `analytics-mcp` × GAQL | menos de 70% dos cliques viram sessão | média |
| GA12 | Acessos à propriedade | medicao | interface | acesso de gente de fora | média |
| GA13 | E-commerce: purchase com valor e transaction_id único | medicao | `analytics-mcp` (purchase, receita) | compra duplicada ou sem valor | alta |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-GA1 | Marcar os eventos reais como principais e desmarcar os de template | GA1 | `ga4admin` (criar e excluir evento principal) | contagem de 30 dias de cada evento | R2 | marcar de volta | evento principal com contagem em 48 h |
| CX-GA2 | Vincular o GA4 ao Google Ads | GA2 | `ga4admin` (criar vínculo) | conta e propriedade certas | R2 | excluir o vínculo | vínculo aparece nas duas pontas |
| CX-GA3 | Grupo de canais personalizado para origens sem regra | GA3 | interface (Admin → Grupos de canais) | origens que caem em "Unassigned" | R1 | apagar o grupo | "Unassigned" caindo em 7 dias (o UTM do Meta é CX-M9) |
| CX-GA4 | Tirar a duplicação do servidor | GA4 | `gtm.md` CX-G2 | contagem por fluxo antes | R2 | versão anterior do GTM | evento com contagem única em 48 h |
| CX-GA5 | GA4 e GTM fora do bloqueio do banner (Consent Mode v2) | GA5 | `gtm.md` CX-G8 + `paginas.md` CX-P9 | cobertura antes (sessões × cliques) | R2 | configuração anterior do banner | cobertura acima de 70% em 7 dias |
| CX-GA6 | Filtro de tráfego interno e lista de referências indesejadas | GA6 | interface (Coleta de dados, configurações da tag) | IPs e domínios listados | R1 | desativar o filtro | origem indesejada some em 48 h |
| CX-GA7 | Domínios cruzados na tag do Google | GA7 | interface (configurações da tag) | lista de domínios | R2 | tirar o domínio | referências próprias somem em 7 dias |
| CX-GA8 | Retenção de 14 meses, fuso e moeda | GA8 | `ga4admin` (atualizar propriedade) e interface (retenção) | valores atuais | R1 | valores anteriores | propriedade relida |
| CX-GA9 | Dimensões personalizadas para os parâmetros usados | GA9 | `ga4admin` (criar dimensão) | nome e parâmetro | R1 | arquivar a dimensão | dimensão com dados em 48 h |
| CX-GA10 | Desligar formulários da medição otimizada | GA10 | interface (fluxo → medição otimizada) | form_submit × leads | R1 | religar | form_submit falso some |
| CX-GA11 | Achar por que o clique não vira sessão (redirect, tag tardia, banner) | GA11 | `paginas.md` CX-P1 e `gtm.md` CX-G8 | cliques × sessões por página | R2 | — | razão sessões ÷ cliques em 7 dias |
| CX-GA12 | Remover acessos de fora | GA12 | interface | lista de acessos | R2 | re-adicionar | lista conferida |
| CX-GA13 | Purchase com valor e transaction_id único | GA13 | `gtm.md` CX-G14 ou configuração da loja | pedido de teste interceptado | R2 | versão anterior | receita do GA4 × plataforma da loja |
