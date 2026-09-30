# Implementação: eventos conversacionais (Chatwoot / WhatsApp) cruzados com a origem do lead

> Webhook do Chatwoot → n8n → aba de eventos, com a origem do lead (formulário, LP, campanha, anúncio) em cada linha.

**Status:** ✅ Em uso (v2.0.0) · **Relacionado:** agente `integracao-conversacional`

---

## O desenho que aguenta volume

```
Webhook Chatwoot → responde "ok" na hora → Normalizar (trava da conta, telefone E.164, chave do evento)
  → Cruzar pelo ÍNDICE (zero leitura) → Registrar (append) ─erro→ espera sorteada 20–80 s → nova tentativa
                                                              ─erro→ espera 2–4 min → última tentativa (erro visível)
Agenda 15 min (e GET /reindexar) → lê as abas de leads UMA vez → índice por telefone (DDD|8) no staticData
```

- **Nunca ler planilha no caminho de cada evento.** O desenho antigo lia 3 abas inteiras e fazia "atualizar ou
  incluir" (que lê a aba de eventos) a cada mensagem: ~4 leituras por evento e "The service is receiving too many
  requests" nos picos (250 erros em 27 h no caso de referência).
- O índice guarda, por telefone, a linha que o cruzamento antigo escolheria (a mais avançada no funil; empate, a
  mais recente). **Provar equivalência** antes de trocar: rodar o cruzamento antigo e o novo sobre os mesmos dados
  reais (234 telefones, 0 diferenças).
- **staticData só é escrito pelo caminho do índice**; o caminho do evento só lê, então execuções simultâneas não
  brigam (escrever no staticData em webhook concorrente perde dado).
- **Escrita também tem cota** (~60/min por usuário no Sheets): rajada (ex.: IA do SDR abordando dezenas de leads
  recuperados) derruba o append mesmo com 5 tentativas de 5 s. A fila com espera sorteada espalha as escritas.
  Acima disso, fila de verdade (Data Table do n8n, RabbitMQ).
- Trava de conta: evento de outra conta do Chatwoot é recusado antes de qualquer gravação (serve também para testar
  o webhook de produção sem gravar nada).
- O Chatwoot não reenvia o que o n8n recusou depois de responder "ok": evento perdido não volta.

## Testes

- Evento de teste identificado (`teste_claude`, conta do cliente, sem telefone): prova a gravação. Apagar a linha.
- Evento de outra conta: prova que o webhook recebe, sem gravar.
- Execuções com erro são as únicas guardadas quando `saveDataSuccessExecution` é `none`: "nenhuma execução" pode ser
  sucesso; olhe a aba de destino.

## WhatsApp sem Chatwoot

CRM com WhatsApp nativo (DataCrazy, Kommo): a origem do clique para o WhatsApp (CTWA) só existe se o tracking de
CTWA estiver ligado no CRM (`conversation.sourceReferral` vazio = desligado). Botão de WhatsApp em widget: acionador
no evento do widget, não em clique de link.
