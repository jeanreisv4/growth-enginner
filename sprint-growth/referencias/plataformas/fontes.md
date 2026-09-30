# Fontes: bases, pessoas únicas e atribuição

**Leitura:** backup de leads, planilhas, Growth Pack, realizado oficial, `scripts/leads.py` e `scripts/cnpj.py`.
**Escrita:** só a memória do cliente e o `config.json` (lista de testes); as bases são do cliente.

## Auditoria

| Id | Verificação | Frente | Como verificar | Sinal de problema | Gravidade |
| --- | --- | --- | --- | --- | --- |
| F1 | Período e último dia com dado de cada base | fontes | leitura direta | aba parada meses atrás com números plausíveis | alta |
| F2 | Qual fonte manda e o que não é fonte | fontes | entrevista + memória | dois números para o mesmo mês | alta |
| F3 | Pessoas únicas e testes excluídos | fontes | `leads.py` | linhas ≫ pessoas; teste da equipe contado | alta |
| F4 | Regra de atribuição V4 escrita | fontes | memória | "V4" sem definição | alta |
| F5 | Como a venda é contada (criação × fechamento, recompra) | fontes | entrevista + comparação das três contagens | diferença de 50% entre as contagens | alta |
| F6 | Canal de cada pessoa (gclid, fbclid, UTM, referrer) e o "sem origem" | fontes | `leads.py` (função `canal`) | CPL dividido por todos os leads | alta |
| F7 | Qualificação por CNPJ (lead B2B) | fontes | `cnpj.py` | lead fora do perfil tratado como bom | média |
| F8 | Projetado × realizado da fonte oficial | fontes | planilha de projeção × realizado | realizado de planilha errada | média |
| F9 | Leads da plataforma × linhas do backup, dia a dia | fontes | leads por dia na plataforma (export ou conector) × linhas por dia no backup (não pessoas únicas) | dia com gasto e sem linha; plataforma > linhas no mês | alta |
| F10 | Premissas da projeção vigente com base medida | fontes | ticket e taxas da projeção × CRM; ticket × (fee + mídia) ÷ margem | ticket igual a custo ÷ margem; taxa tirada de 1 mês; "breakeven" sem venda | alta |

## Correção

| Id | Correção | Corrige | Como aplicar | Validar antes | Risco | Voltar atrás | Verificar depois |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CX-F1 | Declarar a fonte oficial e marcar o resto como "não é fonte" ou "não medido" | F1, F2, F8 | memória do cliente + documento | fonte confirmada com o usuário | R1 | — | documento com uma fonte por número |
| CX-F2 | Regra de atribuição e contagem da venda escritas | F4, F5 | memória do cliente | regra lida para o usuário | R1 | — | memória atualizada |
| CX-F3 | Lista de testes no `config.json` do cliente | F3 | `clientes/<c>/config.json` | lista mostrada | R1 | — | `leads.py` sem teste |
| CX-F4 | Origem gravada na entrada, para o canal deixar de ser inferido | F6 | `crm_integracao.md` CX-I2 | — | R2 | — | "sem origem" caindo |
| CX-F5 | Critério de perfil por CNPJ levado ao formulário e à mídia | F7 | `meta_ads.md` CX-M8 + `paginas.md` CX-P4 | CNAEs e porte do perfil aprovados | R2 | — | leads qualificados por CNPJ |
| CX-F6 | Recuperar os leads que a plataforma tem e o backup não | F9 | export da Central de Leads do Meta (90 dias) ou do construtor da página; cruzar por telefone e subir ao CRM | lista dos faltantes mostrada, sem duplicar | R2 | — | contagem plataforma × linhas igual no período |
| CX-F7 | Refazer a projeção com ticket e conversão medidos | F10 | skill `projecao-breakeven` com ticket (média e mediana) e taxas do CRM | premissas lidas com o usuário | R1 | projeção anterior guardada | mês de breakeven com rampa dentro do histórico |

CNPJ na Receita: BrasilAPI (`https://brasilapi.com.br/api/cnpj/v1/{cnpj}`, ~1 req/s, User-Agent de curl), dígito
verificador validado, classe por situação, CNAE principal e secundário e MEI; cruzar com o anúncio e com a resposta de
porte do formulário. Tirar o CPF que a Receita põe no nome do MEI antes de publicar (`scripts/cnpj.py` faz tudo isso).
