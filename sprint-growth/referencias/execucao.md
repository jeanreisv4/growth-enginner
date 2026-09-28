# Execução das correções

## Regras
1. **Validar antes.** Google Ads: validateOnly (`scripts/ads_escrita.py` sem `--aplicar`). GTM: editar no
   workspace, criar versão, conferir compilação e contagem de tags antes de publicar.
2. **Ok explícito do usuário para cada mudança** (ou um "pode executar" que nomeia o pacote). Mostrar o que muda,
   em linguagem de negócio, antes de aplicar. Listas (negativas) são mostradas inteiras com o gasto que bloqueiam.
3. **Reler depois.** Consulta na API / gtm.js publicado / teste de disparo. Só então dizer "feito".
4. **Registrar** na aba Executado e em `clientes/<cliente>/memoria.md`.
5. **Pausar em vez de apagar** (tags, palavras): dá para voltar atrás. Guardar backup antes de mexer em fluxo do n8n.
6. **Nunca criar dado falso em sistema do cliente para testar.** Testes interceptam o envio (teste_formulario) ou
   disparam sem gclid com GA4/Meta bloqueados (teste_disparo). Se um lead de teste for inevitável, nome
   "TESTE TECNICO - IGNORAR" e avisar.
7. **Modo automático negou?** Pare, explique o que ia fazer e por quê, deixe a decisão com o usuário. Não tente
   outro caminho para o mesmo resultado.

## O que já se sabe que não dá pela API
- Conversões hospedadas pelo YouTube (MUTATE_NOT_ALLOWED) → interface.
- Upload de conversão por clique em conta nova (CUSTOMER_NOT_ALLOWLISTED) → CSV em Metas → Conversões → Uploads,
  com `Parameters:TimeZone=America/Sao_Paulo` e colunas Google Click ID, GBRAID, Conversion Name, Conversion Time,
  Conversion Value, Conversion Currency.
- Verificação em duas etapas dos usuários → interface.
- Construtor de página (GreatPages) → configuração do construtor.
