# Aula: Padrão de Tracking — V4 Marketing

> Aula presencial obrigatória para toda a operação (200 pessoas).
> Duração estimada: 2h (1h teoria + 1h prática)
> Formato: slides em HTML + apresentação ao vivo

**Status:** 📝 Em construção (estrutura modular — preencher próximo chat)
**Owner:** Growth Engineer + Chapter Lead Mídia Paga
**Versão:** v1.0.0

---

## Estrutura da aula (5 módulos)

### Módulo 1: Por que tracking importa (15 min)

> **Objetivo:** instalar a dor antes de mostrar a solução.

Tópicos:
- O custo de não ter padrão (case de operação anterior — dados ruins)
- O que dados ruins fazem com o algoritmo do Meta/Google
- Por que 80% das agências têm tracking ruim (e por que isso é uma vantagem competitiva)
- Como tracking afeta CAC, LTV e ROAS reais

> **TODO:** trazer 2-3 cases reais (mesmo anônimos) de antes/depois

### Módulo 2: Anatomia de um tracking moderno (20 min)

Tópicos:
- O funil completo: Lead → MQL → SQL → Cliente
- Stack obrigatória da V4 Company (GTM Web + SSGTM + Pixel + CAPI + GA4 + Google Ads)
- Por que SSGTM existe (adblockers, ITP iOS, cookie depreciation)
- O conceito de deduplicação Browser + Server (event_id)
- Event Match Quality (EMQ) explicado pra não-técnico

> **TODO:** criar diagrama visual do funil e da stack

### Módulo 3: Schema de dados e nomenclatura (15 min)

Tópicos:
- O contrato de dados (campos obrigatórios)
- Por que dropdown vence checkbox
- Padrão de nomenclatura: `Canal - Ativo`
- Status do funil (Lead/MQL/SQL/Cliente/Perdido) e motivos de perda
- Por que `motivo_perdido` ≠ `observacao`

> **TODO:** mostrar exemplo prático de planilha bem vs mal formatada

### Módulo 4: Decisões obrigatórias e tier único (15 min)

Tópicos:
- A regra: avançado pra todos (sem flexibilidade)
- Stape Free aguenta a maioria dos clientes
- Modelo de valor proxy (lucro) — fórmulas
- Por que diferenciar valor por canal (Meta vs Google)
- O que NÃO entra no padrão (varia por cliente)

> **TODO:** trazer cálculo do WK como exemplo numérico

### Módulo 5: Auditoria e processo (10 min)

Tópicos:
- Skill `tracking-web-and-capi` no Claude Code
- Os 3 modos: planejar, auditar, troubleshoot
- Quem audita quem (Coordenador valida operador)
- Critérios bloqueantes vs atenção
- Cadência: auditoria antes de TODO go-live

---

## Parte prática (1h)

### Demo 1: Caso WK Carpetes (sem CRM) — 30 min

Passo a passo do caso real:
- Setup do GTM Web (com prints)
- Setup do GTM Server (stape)
- Configuração da planilha (script automático)
- Validação no Meta Test Events
- Configuração do back-pass via Apps Script

> **TODO:** prints serão fornecidos pelo Jean (V4)

### Demo 2: Caso CRM (com Kommo) — 20 min

Mesmo fluxo, com diferenças no storage e back-pass.

> **TODO:** definir cliente para o caso CRM

### Q&A — 10 min

---

## Material complementar

Após a aula, operadores recebem:
- Link da skill `tracking-web-and-capi` no Claude Code
- Acesso à pasta `growth-engineer/` do repo skills_colli_co
- Templates prontos pra usar (planilha, JSONs GTM)
- Canônico em PDF pra consulta offline

## Quiz de aprendizado

Ao final, 10 perguntas múltipla escolha:

> **TODO:** elaborar 10 perguntas

Exemplos:
1. O que diferencia Lead de MQL?
2. Por que SSGTM é importante?
3. Qual o efeito de deixar Test Event Code em produção?
4. Como calcular valor proxy de um Lead?
5. ...

## Material a produzir

- [ ] Slides em HTML/Markdown (presentation mode)
- [ ] Slides em PDF (consulta offline)
- [ ] Diagrama do funil + stack
- [ ] 10 perguntas do quiz
- [ ] Lista de cases de antes/depois pra trazer

## Logística

- Local: sala da empresa
- Público: ~200 pessoas (operação inteira)
- Pré-requisito: ter Claude Code instalado (treinamento separado)
- Pós-aula: piloto com 5-10 clientes nos próximos 30 dias
