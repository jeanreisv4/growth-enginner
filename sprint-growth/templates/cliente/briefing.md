# <Cliente> — briefing da sprint

Preenchido uma vez por cliente, antes da sprint, e atualizado quando algo muda. Resposta em branco = pendente: a
sprint não trava, mas o que depende dela fica "não medido" no documento. "Não sei" também é resposta (vira
pendência com dono). `scripts/preflight.py` conta o que está em branco por bloco.

## 1. Dinheiro

| Pergunta | Resposta | Se não souber, onde achar |
| --- | --- | --- |
| Fee mensal da V4 | | contrato ou planilha de projeção |
| Verba de mídia por mês, total e por canal (Google, Meta, outros) | | plano de mídia |
| Margem de contribuição (%) | | DRE do cliente (a margem "de cabeça" já errou por 6 p.p.) |
| Ticket médio por serviço ou produto | | CRM (vendas ganhas) ou financeiro |
| Meta do cliente (receita, vendas ou leads por mês) | | reunião de kickoff |
| Link da projeção de breakeven vigente | | pasta do cliente |

## 2. Operação e oferta

| Pergunta | Resposta | Se não souber, onde achar |
| --- | --- | --- |
| Segmento e modelo (inside sales, e-commerce, SaaS com trial) | | |
| Serviços ou produtos que vende (o core e o que é secundário) | | site, time comercial |
| O que NÃO vende (vira negativa na hora) | | time comercial |
| Modalidades de atendimento (no local do cliente × na sede; entrega; frete e quem paga) | | time comercial |
| Regiões atendidas, evitadas e o porte ou valor mínimo fora da região core | | time comercial |
| Prazo, garantia, provas (certificações, laudos, clientes âncora, anos de mercado) | | site, time comercial |
| Concorrentes que o cliente conhece | | time comercial |

## 3. Regras de contagem

| Pergunta | Resposta | Se não souber, onde achar |
| --- | --- | --- |
| Qual fonte é o realizado oficial (CRM, Growth Pack, planilha) e o que NÃO é fonte | | |
| Como a venda é contada (data de criação ou de ganho; com ou sem recompra) | | |
| Regra de atribuição V4 (o que conta como lead e venda da V4; etiqueta, campo, origem) | | |
| Critério de MQL vigente (documento ou régua) | | fluxo do n8n, CRM |
| "LT" e siglas do cliente: o que significam | | |

## 4. Comercial

| Pergunta | Resposta | Se não souber, onde achar |
| --- | --- | --- |
| Quem atende (pessoas, horário) e por quais canais (WhatsApp, telefone, e-mail) | | |
| Login do CRM: individual ou compartilhado | | |
| Cadência de contato combinada (tentativas, prazo) | | |
| Venda acontece fora do CRM? Existe relatório de faturamento | | financeiro |

## 5. Acessos e donos (o `preflight.py` testa o que estiver no config)

| Item | Resposta (ID, link ou "não temos") | Quem tem acesso |
| --- | --- | --- |
| Google Ads: conta(s) e MCC; conta nova ou antiga | | |
| Meta: conta de anúncios; conector autorizado ou exports | | |
| GA4 da LP e GA4 do site institucional (propriedades) | | |
| GTM web e servidor | | |
| CRM (tipo) e token ou export | | |
| Automação: n8n (fluxos), Make, Zapier, Apps Script | | |
| Planilha de backup de leads (link, abas) | | |
| LP (construtor) e site (CMS), com quem edita | | |
| Clarity (projeto e token) | | |
| Search Console do site | | |
