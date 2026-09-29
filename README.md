# growth-enginner

Skills do Claude Code para o trabalho de growth engineer em agência: projetar, medir, diagnosticar e reportar a
receita do cliente, do clique à venda. Cada skill é uma etapa de um mesmo loop, e cada uma cobre um conjunto das
disciplinas do PDI de growth engineer.

Todo README de skill tem as mesmas três camadas: o **desenho** (as fases, para ler em 30 segundos), o
**"Como funciona"** (uma linha por fase: o que entra, o que a skill faz, a ferramenta, o que sai e o que trava) e o
**detalhe completo** no `SKILL.md` ou, no check-in, na especificação do workflow.

## O loop

Desenho no formato de modelo qualitativo de crescimento (Reforge): as missões do cargo entram como canais lineares,
e as skills formam o loop. Cada passo é uma ação, termina onde o próximo começa e deixa uma saída que pode ser medida.

```mermaid
flowchart TB
    classDef missao fill:#F4F4F4,stroke:#8A8A8A,color:#111
    classDef skill fill:#FFFFFF,stroke:#E50914,stroke-width:2px,color:#111

    subgraph M["Canais lineares · as 5 missões do cargo"]
        direction LR
        M3["Estratégia de tráfego<br/>alinhada ao<br/>go-to-market"]:::missao ~~~ M5["Atribuição<br/>da jornada nas<br/>plataformas"]:::missao ~~~ M2["Auditoria<br/>recorrente"]:::missao ~~~ M4["Execução<br/>de mídia<br/>paga"]:::missao ~~~ M1["Operação direta<br/>em grandes<br/>clientes"]:::missao
    end

    subgraph L["Loop do cliente · uma volta por mês"]
        direction LR
        P["<b>projecao-breakeven</b><br/>diz em que mês<br/>o projeto se paga"]:::skill
        T["<b>tracking-web-and-capi</b><br/>mede cada etapa,<br/>do clique à venda"]:::skill
        S["<b>sprint-growth</b><br/>acha a restrição<br/>e corrige"]:::skill
        C["<b>checkin-ropre</b><br/>reporta realizado<br/>× projetado"]:::skill
        P -->|"meta mês a mês<br/>e CAC permitido"| T
        T -->|"lead e venda<br/>com origem"| S
        S -->|"plano em R$<br/>e Executado"| C
        C -.->|"↺ desvio explicado e premissas novas"| P
    end

    M -->|"alimentam"| L
    style M fill:#FFFFFF,stroke:#CCCCCC
    style L fill:#FFFFFF,stroke:#CCCCCC
```

| Passo | Missão que alimenta | Ação | Saída | Como se mede |
|---|---|---|---|---|
| [`projecao-breakeven`](projecao-breakeven/) | Estratégia de tráfego alinhada ao go-to-market | Lê o histórico, faz a entrevista das premissas e dá o veredito | Planilha com meta mês a mês, CAC permitido e o caminho quando não fecha | Mês de breakeven; projetado de leads, MQL e vendas |
| [`tracking-web-and-capi`](tracking-web-and-capi/) | Atribuição da jornada nas plataformas | Planeja, gera os containers GTM web e servidor pelo template (com validação), audita e conserta Pixel/CAPI, Google Ads, GA4 e CRM | Cada lead e venda chega à plataforma e ao CRM com a origem | Eventos que disparam; conversões com rótulo certo; leads com origem ÷ leads; venda de volta às plataformas |
| [`sprint-growth`](sprint-growth/) | Auditoria recorrente · Execução de mídia paga | Audita a jornada inteira com 8 agentes especialistas em paralelo (mídia, medição, Clarity, jornada, comercial, mercado), acha a restrição (TOC) e executa pelas MCPs | Plano 5W1H priorizado em R$ e aba Executado | Impacto em R$/mês de cada ação; CPL real por pessoa única |
| [`checkin-ropre`](checkin-ropre/) | Operação direta em grandes clientes | Monta o check-in (Resultados, Objetivos, Premissas e riscos, Entregas, Próximos passos) | Deck e documento com a regra de atribuição declarada | Realizado × projetado; o que não foi medido escrito como tal |

## As disciplinas

As 21 disciplinas do PDI de growth engineer, por domínio. A cor é a profundidade esperada no cargo; as letras dizem
qual skill exercita a disciplina (**P** projeção, **T** tracking, **S** sprint, **C** check-in). Borda tracejada =
nenhuma skill cobre ainda.

```mermaid
flowchart TB
    classDef max fill:#FDE7E8,stroke:#E50914,color:#111
    classDef sol fill:#E8F0FE,stroke:#3B6FD8,color:#111
    classDef con fill:#F4F4F4,stroke:#8A8A8A,color:#111
    classDef lacuna fill:#FFFFFF,stroke:#8A8A8A,stroke-dasharray:4 3,color:#555

    subgraph G["Geração de demanda"]
        direction LR
        G1["Tráfego Pago<br/>S"]:::sol ~~~ G2["Tráfego Orgânico<br/>S"]:::sol ~~~ G3["Oferta<br/>S"]:::sol ~~~ G4["Narrativa<br/>—"]:::lacuna ~~~ G5["Direção Visual<br/>—"]:::lacuna
    end

    subgraph J["Jornada"]
        direction LR
        J1["Orquestração<br/>de Jornada<br/>S"]:::max ~~~ J2["Inteligência<br/>de Funil<br/>S · P"]:::sol ~~~ J3["Processo<br/>Comercial<br/>S"]:::sol ~~~ J4["CRM Marketing<br/>S · T"]:::sol
    end

    subgraph D["Dados"]
        direction LR
        D1["Tracking<br/>T · S"]:::max ~~~ D2["Mensuração<br/>e Atribuição<br/>T · S · P · C"]:::max ~~~ D3["Arquitetura<br/>de Dados<br/>T · C"]:::max ~~~ D4["Análise<br/>S · P · C"]:::max
    end

    subgraph Y["Sistemas"]
        direction LR
        Y1["Automação e<br/>Orquestração<br/>S · T · C"]:::max ~~~ Y2["IA<br/>S · P · C"]:::max
    end

    subgraph N["Negócios"]
        direction LR
        N1["Economics<br/>P · S"]:::sol ~~~ N2["Repertório e<br/>Referência<br/>S · P"]:::sol ~~~ N3["Produto<br/>—"]:::lacuna ~~~ N4["Comunicação<br/>com Cliente<br/>C"]:::con ~~~ N5["Gestão de Tarefas<br/>e Projetos<br/>S"]:::con ~~~ N6["Gestão de<br/>Pessoas<br/>—"]:::lacuna
    end

    G ~~~ J ~~~ D ~~~ Y ~~~ N
    style G fill:#FFFFFF,stroke:#CCCCCC
    style J fill:#FFFFFF,stroke:#CCCCCC
    style D fill:#FFFFFF,stroke:#CCCCCC
    style Y fill:#FFFFFF,stroke:#CCCCCC
    style N fill:#FFFFFF,stroke:#CCCCCC
```

Legenda: vermelho = Maximizar · azul = Sólido · cinza = Conhecer · tracejado = lacuna.

| Disciplina | Profundidade | Onde a skill exercita |
|---|---|---|
| Orquestração de Jornada | Maximizar | **S**: destino de cada anúncio, página, formulário, WhatsApp e CRM desenhados de ponta a ponta |
| Tracking | Maximizar | **T**: plano e implantação; **S**: auditoria do GTM, disparo real das tags, formulário interceptado |
| Mensuração e Atribuição | Maximizar | **T**: origem até o CRM; **S**: CPL real por pessoa única; **P**: fonte oficial do realizado; **C**: regra de atribuição declarada |
| Arquitetura de Dados | Maximizar | **T**: planilha, n8n e CRM; **C**: ETL extrair, transformar, carregar |
| Análise | Maximizar | **S**: funil estratificado, lead novo × cliente antigo, tempo por etapa; **P**: taxas efetivas; **C**: indicadores do período |
| Automação e Orquestração | Maximizar | **S**: MCPs de Google Ads, GTM e GA4; **T**: n8n e Apps Script; **C**: workflow de agentes |
| IA | Maximizar | As quatro são skills de agente; **S** e **C** usam agentes em paralelo |
| Tráfego Pago | Sólido | **S**: auditoria A1–A10, termos e negativas, criativo × qualidade do lead |
| Tráfego Orgânico | Sólido | **S**: SEO on-page e técnico da página que recebe o tráfego |
| Oferta | Sólido | **S**: oferta do anúncio × oferta da página |
| Inteligência de Funil | Sólido | **S**: onde o funil vaza; **P**: taxa por etapa |
| Processo Comercial | Sólido | **S**: motivos de perda, time, tempo até a primeira ação |
| CRM Marketing | Sólido | **S**: CRM pela API, etiquetas, disparo em massa; **T**: venda offline de volta às plataformas |
| Economics | Sólido | **P**: breakeven, margem, CAC permitido; **S**: impacto em R$ de cada ação |
| Repertório e Referência | Sólido | **S**: pesquisa de mercado e concorrentes; **P**: benchmarks com fonte |
| Comunicação com Cliente | Conhecer | **C**: check-in ROPRE |
| Gestão de Tarefas e Projetos | Conhecer | **S**: 5W1H com status e aba Executado |
| Narrativa · Direção Visual · Produto · Gestão de Pessoas | Sólido / Conhecer | Lacunas: nenhuma skill ainda |

Nenhuma pasta traz dado de cliente: cada skill gera sua cópia pública com o cliente trocado pelo segmento.
