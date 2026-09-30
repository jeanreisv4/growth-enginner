# Páginas: site, landing page e formulário

**Leitura:** `curl`, render do claude-seo (`~/.claude/skills/seo/scripts/claude-seo run render_page.py`),
`scripts/teste_formulario.py` (envio interceptado), PageSpeed e o Clarity. **Escrita:** quase sempre de quem edita a
página (construtor, desenvolvedor, loja). A correção vira pedido com evidência, dono e prazo; quando a V4 tem acesso
de edição, aplica com ok e registra. Auditoria de SEO completa: `/seo audit <site>`.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| P1 | Destino de cada anúncio responde 200, sem cadeia de redirect, com SSL válido (site, app, painel) | jornada | `curl -I` em cada URL final | 404, redirect duplo, certificado vencido | alta |
| P2 | A oferta do anúncio aparece acima da dobra | jornada | render da página × textos do anúncio | "50% Off" que a página não mostra | alta |
| P3 | Title único, description e H1/H2 com as palavras compradas | jornada | render (`title`, `h1`, `h2`) | H1 genérico; dois titles | média |
| P4 | Formulário: campos obrigatórios, máscara, validação, visível no celular | jornada | `teste_formulario.py` + print do celular | 8 campos obrigatórios; telefone sem máscara; formulário abaixo da dobra | alta |
| P5 | Campos ocultos de origem (UTM, gclid, fbclid) preenchidos | jornada | `teste_formulario.py` com UTM e gclid na URL | POST sem origem | alta |
| P6 | Página de obrigado: noindex, fora do sitemap, conversão única ao recarregar | jornada | render + sitemap + `teste_disparo.py` | obrigado indexado; conversão a cada recarga | média |
| P7 | Velocidade no celular (LCP, INP, CLS) | jornada | PageSpeed da LP principal | LCP acima de 4 s | média |
| P8 | SEO técnico básico: robots.txt, sitemap, canonical, schema, og | jornada | `curl` + render | robots bloqueando a LP; canonical para outra página | baixa |
| P9 | Banner de cookies não bloqueia GTM e atribuição | jornada | `teste_formulario.py` (GTM carregou sem aceite?) | lead sem UTM; GA4 vendo ~25% | alta |
| P10 | Botão de WhatsApp: número certo, mensagem com a origem, abre no celular | jornada | render + clique no teste | número antigo; mensagem sem identificar a campanha | média |
| P11 | Provas e confiança: depoimentos, clientes, preço ou faixa clara | jornada | render | página sem prova nem preço quando o concorrente mostra | baixa |
| P12 | Quem edita a página e com que acesso | jornada | entrevista + memória | ninguém sabe quem mexe no construtor | baixa |
| P13 | Site institucional medido antes de virar destino de mídia | jornada | GTM e GA4 no HTML; acesso da V4 ao GA4 do site | GA4 de outra conta; sem GTM; WhatsApp do site sem medição | média |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-P1 | Corrigir destino, redirect ou certificado | P1, GA11 | quem edita o site ou a hospedagem; URL do anúncio por `google_ads.md` CX-A14 | lista de URLs com o status | R2 | URL anterior | `curl -I` 200 em todas |
| CX-P2 | Oferta do anúncio acima da dobra (ou anúncio alinhado à página) | P2, C4 | pedido ao editor com print; ou CX-A8 / CX-M5 | textos aprovados | R2 | versão anterior | volta rápida e conversão da LP |
| CX-P3 | Title, description e H1/H2 com as palavras compradas | P3, A6 | editor da página | textos propostos | R1 | textos anteriores | índice de qualidade em 14 dias |
| CX-P4 | Formulário mais curto, com máscara e visível no celular | P4, C6 | editor da página | campos que saem aprovados pelo cliente (MQL continua medível) | R2 | formulário anterior | taxa de conversão da LP em 14 dias |
| CX-P5 | Campos ocultos de origem e script de atribuição | P5, G17 | editor da página + `gtm.md` CX-G14 | `teste_formulario.py` antes | R2 | versão anterior | `teste_formulario.py` com UTM e gclid |
| CX-P6 | Obrigado com noindex, fora do sitemap e conversão única | P6 | editor + GTM (acionador uma vez por página) | página e tag mostradas | R1 | configuração anterior | recarga não duplica no `teste_disparo.py` |
| CX-P7 | Velocidade: imagens, scripts de terceiros, fonte | P7 | pedido ao desenvolvedor com o relatório do PageSpeed | itens de maior ganho | R2 | versão anterior | LCP no PageSpeed |
| CX-P8 | SEO técnico básico (ou `/seo audit` completo quando o contrato cobre SEO) | P8 | editor da página ou skill `seo` | itens listados | R1 | valores anteriores | `curl` de robots, sitemap e canonical |
| CX-P9 | Banner: GTM e atribuição fora da categoria de marketing; Consent Mode v2 | P9, G9, GA5 | configuração do construtor + `gtm.md` CX-G8 | `teste_formulario.py` antes | R2 | configuração anterior | GTM carrega sem aceite |
| CX-P10 | Botão de WhatsApp com número certo e mensagem que identifica a origem | P10 | editor da página + `gtm.md` CX-G15 | link testado no celular | R1 | link anterior | conversa chega com a mensagem de origem |
| CX-P11 | Provas e preço na página | P11, MK2, MK4 | pedido ao cliente e ao editor | conteúdo aprovado | R2 | versão anterior | conversão da LP |
| CX-P12 | Registrar dono e acesso de edição de cada página | P12 | memória do cliente | — | R1 | — | memória atualizada |
| CX-P13 | GTM no site, acesso ao GA4 e teste site × LP antes de mover verba | P13 | GTM no site + pedido de acesso + campanha dividida por 30 dias | custo por conversa de cada destino | R2 | voltar à LP | custo por conversa e por orçamento por destino |
