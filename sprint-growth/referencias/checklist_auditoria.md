# Checklist de auditoria

Cada linha: verificação · ferramenta · sinal de problema. Marque no `clientes/<cliente>/memoria.md` o que foi
feito e o que ficou "não medido".

## Fontes
- [ ] Período e último dia com dado de cada base · leitura direta · base parada no meio do período
- [ ] Qual fonte manda / o que não é fonte · entrevista · dois números para o mesmo mês
- [ ] Pessoas únicas e testes excluídos · `scripts/leads.py` · linhas ≫ pessoas
- [ ] Regra de atribuição V4 escrita · entrevista · "V4" sem definição

## Google Ads (`scripts/ads_auditoria.py`)
- [ ] Gasto por campanha e mês · A10 orçamento × gasto
- [ ] Conversões: principal zerada (A1), duplicada (A2), sem uso (A3), metas da campanha biddable
- [ ] Acessos e campanhas estranhas (A4)
- [ ] Lances e local (A5)
- [ ] Nota ≤ 3 com gasto (A6) e parcela perdida por classificação (A7)
- [ ] Sitelinks (A8, com `--site`) e destinos (A9)
- [ ] Termos: gasto por intenção, login/concorrente/fora do produto · `scripts/termos_negativas.py`
- [ ] Anúncios: promessa × página; caminho exibido; títulos com a busca

## Meta (agente `sprint-meta-ads`)
- [ ] Gasto e leads por criativo e mês (conector do Meta ou export)
- [ ] Qualidade do lead por criativo (porte, CNPJ, qualificação) cruzando com o backup
- [ ] Campanhas fora do export (IDs no backup que não estão no export)
- [ ] Marcação de MQL do formulário nativo continua viva
- [ ] UTMs com nome, não ID

## Medição e integração
- [ ] GTM web/servidor · `scripts/gtm_auditoria.py` (G1–G5)
- [ ] Disparo real com rótulo certo · `scripts/teste_disparo.py`
- [ ] Formulário leva UTM/gclid e GTM carrega sem aceite · `scripts/teste_formulario.py`
- [ ] GA4: eventos principais que disparam; vínculo com Ads; "Unassigned"
- [ ] Lead chega ao destino (planilha, n8n, CRM, painel) com origem e vira a etapa seguinte

## Clarity (`scripts/clarity.py`, agente `sprint-clarity`)
- [ ] Token do projeto no `config.json` do cliente (arquivo fora do repositório) · primeira coleta com `--dias 3`
- [ ] Robôs acima de 30% das sessões, e de qual canal (C1)
- [ ] Raiva, clique morto, volta rápida e erro de script nas páginas que recebem mídia (C2–C5)
- [ ] Rolagem do celular × computador (C6); formulário abaixo da dobra no celular
- [ ] Campos não reconhecidos no resumo (nome de campo da API conferido na primeira coleta real)

## Página e SEO
- [ ] Um `<title>`, description, H1/H2 com as palavras compradas, og, schema
- [ ] robots.txt, sitemap (sem página de obrigado), canonical
- [ ] Formulário: campos obrigatórios; página de obrigado com noindex único
- [ ] Certificados SSL (site, app, painel)

## Comercial e receita
- [ ] Funil por etapa com o que não é medido declarado
- [ ] Último contato registrado; quem pediu compra e não foi atendido
- [ ] Vendas por data de fechamento; novo × recorrente; piso quando a fonte é parcial
- [ ] Margem de contribuição (DRE) e breakeven · skill `projecao-breakeven`

## Mercado
- [ ] Concorrentes dos termos de pesquisa: preço, trial, CTA, provas · agente de pesquisa + conferência de 2 preços

- Leads B2B com campo CNPJ: consultar na BrasilAPI (https://brasilapi.com.br/api/cnpj/v1/{cnpj}, ~1 req/s, User-Agent
  de curl), validar dígito verificador, classificar por situação, CNAE principal/secundário e MEI; cruzar com anúncio e
  com a resposta de porte do formulário. Tirar o CPF que a Receita põe no nome de MEI antes de publicar.
