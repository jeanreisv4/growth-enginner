# Modos da sprint: auditoria e correção

A sprint tem dois modos. Eles usam o mesmo catálogo (`referencias/plataformas/`): cada plataforma lista **tudo o
que se verifica** (tabela Auditoria, ids como `A1`, `M3`, `GA2`) e **tudo o que se corrige** (tabela Correção, ids
`CX-…`). Todo item de auditoria tem pelo menos uma correção que o resolve; a regressão confere.

| Pedido do usuário | Modo | O que roda |
| --- | --- | --- |
| "sprint growth do cliente X", "diagnóstico", "audita a conta" | **auditoria** (e depois, se ele quiser, correção) | etapas 0–4 do `SKILL.md` |
| "sprint ads do cliente X", "audita só o GTM" | **auditoria de uma frente** | memória + agente da frente + `consolidar.py --frentes` |
| "executa o plano", "corrige o A2 da distribuidora de peças automotivas", "pode aplicar as negativas" | **correção** | este arquivo, seção Correção |
| "corrige o GTM do cliente X" sem auditoria recente | **auditoria da frente primeiro**, depois correção | nunca corrigir sem o achado com número |

## Auditoria (somente leitura)

**Entra:** memória do cliente, entrevista, acessos. **Sai:** documento (Diagnóstico e plano) com o plano 5W1H em
que cada linha aponta a correção do catálogo (`CX-…`).

1. Cada agente lê o arquivo da sua plataforma e verifica **todos** os itens da tabela Auditoria em que ele é a
   frente. No JSON de achados, o campo `cobertura` traz o status de cada id: `ok`, `achado`, `nao_medido` (com o
   motivo em `nao_medido`) ou `nao_se_aplica` (ex.: e-commerce sem formulário).
2. `consolidar.py` lê a cobertura e lista, por frente, o que **não foi verificado**. Item sem status é lacuna da
   auditoria, não "ok". Nenhuma sprint fecha com item de gravidade crítica ou alta sem status.
3. Nada é alterado em conta, container, CRM, fluxo ou página. Testes interceptam o envio (`teste_formulario.py`)
   ou disparam sem gclid com GA4 e Meta bloqueados (`teste_disparo.py`).

## Correção (com ok explícito para cada mudança)

**Entra:** um achado com número (da sprint ou de uma auditoria da frente feita agora) e a correção do catálogo que
o resolve. **Sai:** a mudança aplicada, relida e registrada na aba Executado e em `clientes/<cliente>/memoria.md`.

### Ciclo de cada correção

1. **Preparar**: montar a mudança exata a partir da linha `CX-…` (o que muda, onde, de quanto para quanto).
2. **Validar antes**: `validateOnly` no Google Ads (`scripts/ads_escrita.py` sem `--aplicar`), rascunho e versão
   no GTM sem publicar, backup do fluxo do n8n, cópia da configuração atual (orçamento, lance, status) na memória.
3. **Mostrar em linguagem de negócio**: o que muda, por quê (o achado com o número), o risco (R1, R2, R3), como
   voltar atrás e como vamos saber se funcionou. Listas (negativas, públicos) vão inteiras, com o gasto que bloqueiam.
4. **Ok explícito do usuário** para aquela mudança ou para um pacote que ele nomeia ("pode aplicar CX-A6 e CX-A10").
   R3 pede ok à parte, nunca dentro de um pacote.
5. **Aplicar** pela ferramenta da coluna "Como aplicar".
6. **Reler**: consulta na API, `gtm.js` publicado, teste de disparo, execução do fluxo. Só então dizer "feito".
7. **Registrar**: aba Executado (data, ação, onde, por quê com o número, verificação) e memória do cliente, com o
   valor anterior para voltar atrás.
8. **Monitorar**: a coluna "Verificar depois" diz quando e o que olhar. R3 ganha a data de leitura na memória
   (janela de aprendizado: ~2 semanas no Google Ads, ~50 eventos por conjunto no Meta).

### Risco

| Nível | O que é | Exemplos | Regra |
| --- | --- | --- | --- |
| **R1** | reversível na hora, sem efeito no aprendizado | pausar anúncio ou tag, negativa, sitelink, dimensão do GA4 | pode ir em pacote nomeado |
| **R2** | muda configuração; a volta é conhecida e guardada | nova versão do GTM, orçamento, anúncio novo, fluxo do n8n, UTMs | backup antes; ok por mudança ou pacote nomeado |
| **R3** | mexe no aprendizado da plataforma ou é difícil de desfazer | conversão principal, estratégia de lance, evento de otimização do Meta, container novo, excluir | ok à parte, data de leitura, nunca na sexta à tarde |

### Regras que não mudam

- **Pausar antes de apagar.** Apagar só com pedido explícito e depois de dias pausado sem efeito.
- **Nunca criar dado falso em sistema do cliente.** Lead de teste inevitável: nome "TESTE TECNICO - IGNORAR" e aviso.
- **Modo automático negou?** Pare, explique o que ia fazer e por quê, deixe a decisão com o usuário. Não tente outro
  caminho para o mesmo resultado.
- **Correção de outra frente.** Várias correções vivem em outra plataforma (o A1 do Google Ads se corrige no GTM,
  `CX-G1`). Siga o id; não improvise a correção na plataforma onde o sintoma apareceu.
- **Correção que depende do cliente** (página, comercial, construtor): vira pedido com evidência (gravação do
  Clarity, print, número), dono e prazo no 5W1H. Não conta como "feito" até a verificação passar.
