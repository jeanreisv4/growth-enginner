# Contrato de achados (o que cada agente entrega)

Cada agente de frente grava dois arquivos em `clientes/<cliente>/sprints/<AAAA-MM-DD>/achados/`:

- `<frente>.json` — no formato abaixo; é o que `scripts/consolidar.py` lê, confere e junta.
- `<frente>.md` — o relatório da frente para leitura humana (tabelas, contas, o raciocínio).

Frentes: `fontes`, `google-ads`, `meta-ads`, `medicao`, `clarity`, `jornada`, `comercial`, `mercado`.

## Formato do JSON

```json
{
  "frente": "google-ads",
  "cliente": "distribuidora-pecas",
  "periodo": {"inicio": "2026-07-01", "fim": "2026-09-28"},
  "fontes": [
    {"nome": "Google Ads 1234567890 (API)", "periodo": "01/07–28/09", "ultimo_dia": "2026-09-28", "confiabilidade": "alta"}
  ],
  "nao_medido": ["conversões offline: upload bloqueado na conta"],
  "numeros": {
    "gasto_google": {"valor": 18230.5, "unidade": "R$", "fonte": "Google Ads API, 01/07–28/09"},
    "leads_google": {"valor": 212, "unidade": "leads", "fonte": "conversão 00.2 Lead (Ads)"}
  },
  "achados": [
    {
      "id": "ADS-01",
      "titulo": "Conversão principal 00.2 Lead sem nenhum registro em 90 dias",
      "evidencia": "0 conversões de 00.2 Lead × 212 leads com gclid no backup (Ads API + leads.py)",
      "etapa": "medicao",
      "tipo": "medicao",
      "confianca": "alta",
      "impacto": {"volume": 212, "ganho_min": 0.0, "ganho_max": 0.0, "taxas_seguintes": 1, "ticket": 0,
                  "base": "não gera receita direta; destrava o lance por conversão"},
      "correcao": "Corrigir o rótulo da tag 01 - GAds - Lead no GTM web",
      "como_executar": "MCP GTM (rascunho, versão, ok do usuário, publicar)",
      "esforco": "15 min",
      "verificacao": "teste_disparo.py mostra o hit com o rótulo certo; conversões > 0 em 48 h"
    }
  ],
  "perguntas": ["Qual das duas contas de anúncios (sufixo 01 e 02) é da V4?"]
}
```

## Campos

| Campo | Regra |
| --- | --- |
| `fontes[].confiabilidade` | `alta`, `media` ou `baixa`. Base parada no meio do período é `baixa` e o buraco vai em `nao_medido`. |
| `nao_medido` | Tudo que a frente não conseguiu medir, com o motivo. Nunca vira zero. |
| `numeros` | Os números que outras frentes também medem (gasto, leads, pessoas, sessões, vendas). Chave em `snake_case`, sempre com unidade e fonte. O consolidador aponta **divergência** quando a mesma chave vem de duas frentes com mais de 10% de diferença. |
| `achados[].id` | Prefixo da frente + número: `FON`, `ADS`, `META`, `MED`, `CLA`, `JOR`, `COM`, `MER`. |
| `achados[].evidencia` | O número e de onde ele saiu. Achado sem número é hipótese e vai com `confianca: baixa`. |
| `achados[].etapa` | `trafego`, `conversao`, `medicao`, `integracao`, `comercial`, `margem`, `seguranca`, `mercado`. |
| `achados[].tipo` | `seguranca`, `medicao`, `vazamento` ou `otimizacao`. Segurança e medição vêm antes no plano (`priorizacao.md`). |
| `achados[].confianca` | `alta` (volume e taxa medidos), `media` (volume medido, taxa estimada), `baixa` (premissa). |
| `achados[].impacto` | Opcional. Insumos da fórmula de `priorizacao.md`: impacto = volume × ganho × taxas seguintes × ticket, em R$/mês. `ganho_min` e `ganho_max` dão a faixa. Use `null` quando não houver base; o consolidador escreve "sem base". |
| `achados[].esforco` | `5 min`, `15 min`, `1 h`, `1–2 dias` ou `processo comercial`. |
| `achados[].verificacao` | Como saber que a correção funcionou **e** como saber que falhou. |
| `perguntas` | O que só o usuário responde. O agente não pergunta: escreve aqui e segue. |

## Chaves comuns em `numeros` (a mesma chave medida por fontes diferentes)

Use estes nomes para que o consolidador compare as frentes. Divergência acima de 10% vira linha no consolidado
(ex.: plataforma contando lead que o backup não tem = conversão inflada ou duplicada).

| Chave | fontes (backup) | google-ads / meta-ads (plataforma) | medicao (GA4) | comercial (CRM) |
| --- | --- | --- | --- | --- |
| `leads_google` | pessoas únicas com origem Google Ads V4 | conversões de lead da conta | evento de lead com origem google / cpc | — |
| `leads_meta` | pessoas únicas com origem Meta Ads V4 | resultado de lead da conta | evento de lead com origem Meta pago | — |
| `leads_total` | pessoas únicas sem teste | — | evento de lead, todas as origens | leads criados no CRM no período |
| `gasto_google` / `gasto_meta` | — | gasto da conta | — | — |
| `vendas_v4` | — | — | — | vendas pela regra de atribuição |

Chave só de uma frente (ex.: `cpl_real_google`, `sessoes_clarity`) entra normalmente; ela só não é comparada.

## Regras para todo agente

1. **Somente leitura.** Nenhuma escrita em conta, GTM, CRM, n8n ou formulário. A correção vai no campo `correcao`;
   quem executa é a conversa principal, com o ok do usuário.
2. **Não inventar número.** O que não foi medido vai em `nao_medido`, e a pergunta vai em `perguntas`.
3. **Ler antes:** `clientes/<cliente>/memoria.md`, `clientes/<cliente>/config.json` e a seção da frente em
   `referencias/armadilhas.md`.
4. **Dado bruto fica na pasta do cliente** (`ads/`, `gtm/`, `crm/`, `clarity/`…), nunca no JSON de achados.
5. **Nada de credencial** em arquivo de achados (token, chave, telefone da equipe).
