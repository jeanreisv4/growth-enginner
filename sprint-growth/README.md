# sprint-growth

![versão](https://img.shields.io/badge/versão-1.1.1-E50914) ![regressão](https://img.shields.io/badge/regressão-42%20casos-111111)

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
flowchart TB
    classDef entrada fill:#F4F4F4,stroke:#8A8A8A,color:#111
    classDef decisao fill:#FFF4D6,stroke:#C98A00,color:#111
    classDef calculo fill:#E8F0FE,stroke:#3B6FD8,color:#111
    classDef saida fill:#E3F6E8,stroke:#2E9A4F,color:#111
    classDef trava fill:#FDE7E8,stroke:#E50914,color:#111
    classDef loop fill:#FFFFFF,stroke:#E50914,stroke-dasharray:4 3,color:#E50914

    subgraph P["0–2 · Preparação"]
        direction LR
        P0["Memória<br/>do cliente"]:::entrada --> P1["Entrevista<br/>uma pergunta<br/>por vez"]:::entrada --> P2{"Qual é o<br/>realizado<br/>oficial?"}:::decisao --> P3["Fontes<br/>pessoa única<br/>sem teste"]:::calculo
    end

    subgraph A["3–7 · Auditoria, em paralelo"]
        direction LR
        A1["Mídia<br/>Google e Meta<br/>CPL real, CNPJ"]:::calculo
        A2["Medição<br/>GTM, disparo,<br/>formulário, CRM"]:::calculo
        A3["Jornada<br/>destino, página,<br/>oferta"]:::calculo
        A4["Comercial<br/>novo × antigo,<br/>perdas, tempos"]:::calculo
        A5["Mercado<br/>agente em<br/>segundo plano"]:::calculo
        A1 ~~~ A2 ~~~ A3 ~~~ A4 ~~~ A5
    end

    subgraph D["8 · Decisão"]
        direction LR
        D1{"Restrição<br/>(TOC)"}:::decisao
        D1 -->|do sistema| D2["Explorar,<br/>subordinar,<br/>elevar"]:::trava
        D1 -->|da mídia| D3["Medição a<br/>serviço do<br/>comercial"]:::trava
        D2 --> D4["Plano em R$<br/>5W1H com<br/>Status"]:::saida
        D3 --> D4
    end

    subgraph X["9–10 · Documento e execução"]
        direction LR
        X1["Claude Docs<br/>Diagnóstico · Dados<br/>CNPJ · Executado"]:::saida --> X2{"Ok explícito<br/>para esta<br/>mudança?"}:::decisao
        X2 -->|sim| X3["Valida, aplica,<br/>relê e registra"]:::saida
        X2 -->|não| X1
    end

    subgraph F["11 · Fechamento"]
        direction LR
        F1["Memória,<br/>armadilhas,<br/>checklist"]:::entrada --> F2["Regressão,<br/>CHANGELOG, tag"]:::trava --> F3["Cópia pública<br/>conferida"]:::saida
        F3 -.-> F4(("↺ a próxima<br/>sprint começa<br/>pela memória")):::loop
    end

    P -->|"premissas e fontes<br/>confiáveis"| A
    A -->|"achados com<br/>número e fonte"| D
    D -->|"plano priorizado<br/>em R$"| X
    X -->|"Executado<br/>registrado"| F
    style P fill:#FFFFFF,stroke:#CCCCCC
    style A fill:#FFFFFF,stroke:#CCCCCC
    style D fill:#FFFFFF,stroke:#CCCCCC
    style X fill:#FFFFFF,stroke:#CCCCCC
    style F fill:#FFFFFF,stroke:#CCCCCC
```

Legenda: cinza = informação ou registro · amarelo = decisão · azul = análise · verde = entrega ·
vermelho = trava ou prioridade · ↺ = onde o loop se fecha. Na seta entre as fases, a saída de cada uma.

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
