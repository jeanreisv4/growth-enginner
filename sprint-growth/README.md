# sprint-growth

![versão](https://img.shields.io/badge/versão-1.1-E50914) ![regressão](https://img.shields.io/badge/regressão-42%20casos-111111)

Skill do Claude Code para a **sprint growth** de cliente de agência: audita a jornada inteira, do tráfego à venda,
acha a restrição do sistema pela Teoria das Restrições e entrega um plano 5W1H priorizado por impacto em receita,
com as correções executadas pelas MCPs (Google Ads, GTM, GA4) e registradas numa aba "Executado".

- Mídia: Google Ads pela API (conversões, invasão, lances, índice de qualidade, parcela, sitelinks, destinos,
  termos e negativas) e Meta por export (criativo × qualidade do lead, inclusive CNPJ na Receita).
- Medição: GTM web e servidor contra as conversões da conta, disparo real das tags e envio do formulário
  interceptado (sem criar lead); origem do anúncio até o CRM.
- Jornada e comercial: destino, on-page, formulário, CRM (DataCrazy pela API), lead novo × cliente antigo, motivos
  de perda, time e tempo de cada etapa.
- Receita: realizado da fonte oficial, CPL real por pessoa única da mídia paga, breakeven pela skill
  `projecao-breakeven`.

## Workflow

```mermaid
flowchart TD
    A([Pedido: "sprint growth"]) --> B[0. Memória do cliente<br/>clientes/&lt;c&gt;/memoria.md]
    B --> C[1. Entrevista<br/>uma pergunta por vez]
    C --> D[2. Fontes<br/>realizado oficial · CRM · pessoas únicas]
    D --> E1[3. Mídia<br/>ads_auditoria · termos_negativas<br/>Meta por anúncio · CNPJ]
    D --> E2[4. Medição<br/>gtm_auditoria · teste_disparo<br/>teste_formulario · origem no CRM]
    D --> E3[5. Jornada e página<br/>destino · on-page · oferta]
    D --> E4[6. Comercial e receita<br/>datacrazy: novo × antigo, perdas,<br/>time, tempo por etapa]
    D --> E5[7. Mercado<br/>agente em segundo plano]
    E1 & E2 & E3 & E4 & E5 --> F{8. Restrição TOC}
    F -->|sistema| G[Explorar · subordinar · elevar]
    F -->|mídia| H[Medição a serviço do comercial]
    G & H --> I[Plano priorizado em R$<br/>5W1H com Status]
    I --> J[9. Documento Claude Docs<br/>Diagnóstico e plano · Dados do funil<br/>Leads por CNPJ · Executado]
    J --> K{10. Execução<br/>ok explícito por mudança?}
    K -->|sim| L[Valida → aplica → relê<br/>→ aba Executado]
    K -->|não| J
    L --> M[11. Fechamento<br/>memória · armadilhas · checklist<br/>regressão · CHANGELOG · tag]
    M --> N([Cópia pública<br/>publicar.py --conferir])
```

## Estrutura

- `SKILL.md`: o roteiro em 12 etapas (0 a 11).
- `referencias/`: armadilhas (40+ casos), checklist, priorização (TOC + impacto em R$), documento, execução,
  ferramentas (MCPs, BrasilAPI, DataCrazy) e negativas base.
- `scripts/`:
  - `mcp_http.py`, `ads_auditoria.py`, `termos_negativas.py`, `ads_escrita.py`: Google Ads;
  - `gtm_auditoria.py`, `teste_disparo.py`, `teste_formulario.py`: medição;
  - `leads.py`: pessoa única, teste e canal;
  - `datacrazy.py`: CRM (download, histórico, novo × antigo);
  - `cnpj.py`: qualificação B2B pela Receita;
  - `publicar.py`: gera a cópia pública.
- `templates/cliente/` e `tests/regressao.py`.

Dados de cliente e configuração das MCPs nunca entram neste repositório.
