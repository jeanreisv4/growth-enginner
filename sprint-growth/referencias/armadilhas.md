# Armadilhas (cada uma já custou um diagnóstico errado)

Formato: o que aconteceu · como detectar · o que fazer. Cliente entre parênteses (anonimizado na cópia pública).

## Fontes e contagem

- **Mesma métrica, três números.** Vendas do mês podiam ser lançamento manual, CRM por criação ou CRM por
  fechamento, com diferença de 50%+ (indústria de plásticos). Detectar: comparar as três. Fazer: faturamento = data de
  fechamento; safra (eficiência de mídia) = data de criação; declarar no documento.
- **"Ganha" que não é venda.** Pipeline de pré-vendas marcava "Ganha" na passagem para qualificação, com valor
  padrão (indústria de plásticos: 68% exatamente R$ 1.500). Fazer: filtrar só os pipelines de venda antes de calcular ticket.
- **Aba congelada.** Abas bd CRM / bd Analytics paradas meses atrás, com números plausíveis (indústria de plásticos, brindes personalizados).
  Detectar: último dia com dado por base. Fazer: "não medido", nunca zero, e perguntar qual fonte manda.
- **CPL sobre todos os leads.** Dividir a verba por todas as pessoas (inclusive diretas, orgânicas e de outra conta)
  deu R$ 74; o CPL real, só com pessoas únicas da mídia paga V4, é R$ 116 (SaaS de diário de obra). Fazer: CPL = verba ÷ pessoas únicas
  com origem paga da V4, mês a mês e por canal; mostrar o "sem origem" à parte.
- **Linha ≠ pessoa.** Reenvio de formulário, trial + clique em "comprar" e testes da equipe inflam leads
  (SaaS de diário de obra: 152 linhas → 131 pessoas; 65 registros de teste no painel). Fazer: `scripts/leads.py`.
- **Telefone BR.** Comparar últimos dígitos casa 20 de 420; tirar +55 e comparar DDD + 8 finais casa 220
  (indústria de plásticos). Cadastros antigos não têm o 9.
- **Sigla ambígua.** "LT de 3 meses" era tempo de casa, não vida do assinante (SaaS de diário de obra). Perguntar sempre.
- **Duas planilhas com "realizado".** A planilha de projeção tinha um realizado próprio (errado: Google 14× a
  conta) e o oficial estava no Growth Pack, contado à mão (distribuidora de peças automotivas). Detectar: perguntar qual planilha é o realizado
  antes do primeiro gráfico. Fazer: realizado só da fonte oficial; a outra entra só com o projetado.
- **Venda V4 por etiqueta do CRM ≠ contagem manual.** Etiqueta "Lead V4" some quando o vendedor não marca, e safra
  (mês de criação) ≠ mês do ganho (distribuidora de peças automotivas: 16 × 23 em agosto). Fazer: mostrar o número oficial e a conciliação
  mês a mês, pelo mês do ganho.
- **Mix de cliente escondendo a causa.** "Entrada estável e taxa caindo" parecia fechamento; era a recompra da base
  (cliente antigo fecha ~30%, lead novo 2–4%) que caiu de 328 para 100 negócios (distribuidora de peças automotivas). Fazer: sempre separar lead novo
  (negócio aberto no dia do cadastro) de cliente antigo antes de falar em conversão; comparar V4 com lead novo.
- **Etiqueta de origem manual e atrasada.** "Lead V4" posta à mão com 7,8 dias de mediana (distribuidora de peças automotivas): o mês corrente
  sempre parece pior. Detectar: histórico do lead (quem e quando adicionou a etiqueta). Fazer: automação de etiqueta.
- **Disparo em massa inflando conversas.** 4.246 conversas num dia (distribuidora de peças automotivas). Ver distribuição por dia antes de concluir.
- **CRM como registro, não processo.** 1 em 3 negócios nasce já em orçamento/pago; ganho de cliente antigo em 1 min.
  Tempo por etapa só vale para lead novo.
- **Receita sem fonte completa.** Painel sem status de pago e lista de assinantes vista pela metade (SaaS de diário de obra).
  Fazer: reportar piso ("pelo menos 2") e o limite, nunca extrapolar.

## Mídia

- **Conta invadida.** 26 campanhas criadas em 43 minutos com 3.150 palavras de cassino e páginas de golpe
  (SaaS de diário de obra). Detectar: `ads_auditoria.py` A4. Fazer: revisar acessos, 2 etapas; o histórico de alterações da API
  só volta 30 dias.
- **Âncora que não existe.** 12 sitelinks para `#1`…`#6` caíam todos no topo (SaaS de diário de obra). A8.
- **Troca de destino que derruba lead.** Anúncios trocados do site para a LP: R$ 849 → 1 lead, contra ~R$ 176
  por lead no site (SaaS de diário de obra). A9. Comparar custo por lead por destino antes de trocar.
- **Promessa que a página não sustenta.** "50% Off nos Planos" sem desconto na página (SaaS de diário de obra). Risco de
  reprovação por declaração enganosa e nota baixa de página.
- **Grátis não é negativa** quando o produto tem teste grátis ("diário de obra gratuito" converteu — SaaS de diário de obra).
- **Marca colada ≠ produto.** "diariodeobra" é concorrente; "diario de obra" é o produto (SaaS de diário de obra).
- **Renomeação.** "Lead Ads | Interesses" era a mesma campanha "03 - [V4]…" renomeada — só o ID prova (SaaS de diário de obra).
- **Segunda conta de anúncios.** IDs de campanha com sufixo diferente dos da V4 (…0325 × …0769) e leads "sem
  permissão" no formulário (SaaS de diário de obra).
- **Público quente mais caro que o frio.** R$ 133 × R$ 52 por lead (SaaS de diário de obra). Checar antes de escalar remarketing.
- **Criativo com CTR alto e sem verba.** O algoritmo não entregou (R$ 47) — testar com orçamento próprio antes
  de descartar (SaaS de diário de obra).
- **Métrica quebrada × dado quebrado.** Se só as métricas com um certo denominador variam 10x, o denominador é
  suspeito (projeção, cliente de climatização).

## Medição

- **Rótulo com um caractere a menos.** A tag disparava, mas o rótulo não existia: "00.2 Lead" zerou o trimestre
  e o Google só aprendia com o MQL (SaaS de diário de obra). `gtm_auditoria.py` G1 + `teste_disparo.py`.
- **Mesmo acionador como disparo e como exceção.** A tag do Google Ads do pop-up de WhatsApp tinha o evento do
  pop-up nos dois campos: a exceção vence e a conversão nunca saiu, enquanto Meta e GA4 contavam (distribuidora de peças automotivas).
  `gtm_auditoria.py` G5 + `teste_disparo.py` depois de publicar.
- **Duas conversões principais na mesma categoria.** Lead e MQL principais = cada MQL conta 2 (SaaS de diário de obra). A2.
- **Categoria sem lance.** "Enviar formulário" não era biddable na meta da conta; as campanhas só contavam ligação
  (indústria de plásticos). Conferir `campaign_conversion_goal`.
- **GA4 do servidor duplicando.** Tag GA4 no sGTM disparando em PageView/Lead/Contact/MQL do Meta (SaaS de diário de obra). G2.
- **GTM preso no banner de cookies.** Construtor de página (GreatPages) carrega GTM e script de atribuição só
  depois do aceite de marketing: GA4 vê ~25% da LP e o lead chega sem UTM (SaaS de diário de obra). `teste_formulario.py`.
  Correção fica no construtor (tirar da categoria Marketing / Consent Mode), não no GTM.
- **UTM do Meta com ID.** utm_source e utm_medium com ID de campanha/conjunto → GA4 "Unassigned" (SaaS de diário de obra).
- **Eventos principais que nunca disparam.** GA4 com key events de template e os eventos reais desmarcados (SaaS de diário de obra).
- **Pixel com evento fantasma.** Meta reportando add-to-cart em página sem carrinho (brindes personalizados).
- **Mídia apontando para o site errado.** Julho inteiro no site B2B sem checkout (brindes personalizados).
- **Clarity não é histórico.** A Data Export API só devolve as últimas 24–72 h e 10 chamadas por projeto por dia
  (a cota é do projeto: outra ferramenta usando o mesmo token come a sua). Colete no primeiro dia da sprint e
  todo dia depois; com menos de 7 dias acumulados, a confiabilidade é média. `clarity.py` não repete chamada do dia.
- **Campo do Clarity com nome não documentado.** A documentação só mostra os campos de Traffic; os de fricção são
  lidos pelo padrão do nome. Se o resumo listar campo não reconhecido, ajuste `clarity.linhas()` antes de concluir.

## Funil e comercial

- **Canal que gera lead e não alimenta a etapa seguinte.** 57 de 59 leads do formulário nativo do Meta nunca
  entraram no painel de trial (SaaS de diário de obra).
- **Follow-up parado.** Último "em contato" em 28/08; 7 pessoas clicaram em "assinar" e ninguém falou com elas
  (SaaS de diário de obra). As 2 vendas vieram de leads contatados.
- **Capacidade comercial é a restrição.** Correlação leads × vendas negativa; mais verba não vira venda
  (indústria de plásticos). Testar lead × capacidade antes de pedir verba.
- **IA de primeiro atendimento sem segundo toque.** 77 negócios parados em "Ativado IA" (indústria de plásticos).

## Execução

- **Agente não conversa.** O agente de frente não pergunta ao usuário; o que falta vem em `perguntas` no JSON.
  Não o use para validar mudança nem para pedir ok: execução é sempre da conversa principal.
- **Agente novo só aparece em conversa nova.** Depois de `instalar_agentes.py`, a conversa aberta não enxerga o
  agente; até lá, rode a frente com `general-purpose` passando o arquivo do agente como instrução.

- **Publicar GTM, criar fluxo no n8n, extrair código de painel**: o modo automático pode negar. Parar, explicar,
  deixar com o usuário. Nunca contornar.
- **Upload de conversão offline** em conta nova: API recusa (Data Manager API). Gerar CSV para upload manual.
- **Conversões do YouTube** não mudam pela API. Nem as do Google hospedadas (ações locais, ligações de campanha
  inteligente, metas do Universal Analytics, instalação de app): MUTATE_NOT_ALLOWED. Tire do lance pela meta da
  campanha (`campaign_conversion_goal.biddable = false` por categoria), que a API aceita (distribuidora de peças automotivas).
- **Workspace do GTM usado** depois de criar versão: pegar o workspace novo antes de editar.
- **n8n corta resposta grande** (IncompleteRead) ou devolve 502: `mcp_http.py` tenta de novo; reduza a consulta.
