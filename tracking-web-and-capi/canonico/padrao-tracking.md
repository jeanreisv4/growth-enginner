# Padrão de Tracking da V4 Company (Contrato de Dados)

> Este é o documento mestre. Toda implementação deve aderir a ele.
> Mudanças neste arquivo são versionadas e comunicadas à operação.

**Status:** 📝 Em construção — preencher no próximo chat
**Última revisão:** 2026-05-17
**Owner:** Growth Engineer

---

## 1. Por que existe (a dor)

> **TODO próximo chat:** detalhar a dor da operação atual (200 operadores, falta de padrão, decisões com dados ruins, retrabalho, baixa qualidade entre clientes).
> Usar a conversa em `artefatos-referencia/conversa-inicial.md` como insumo.

## 2. Stack obrigatória

Toda implementação obrigatoriamente usa:

- [ ] Google Tag Manager Web (cliente)
- [ ] Google Tag Manager Server (SSGTM) via stape.io
- [ ] Meta Pixel + Meta CAPI **deduplicados** via `event_id` compartilhado
- [ ] Google Ads (Conversion Linker + tags de conversão)
- [ ] Google Analytics 4 (Web + Server-relay opcional)
- [ ] Storage de leads (Google Sheets **OU** CRM padronizado)

## 3. Eventos obrigatórios (mínimo viável)

| Evento | Quando | Onde dispara |
|--------|--------|--------------|
| PageView | toda página | GTM Web → SSGTM |
| Lead | submit do form da LP | GTM Web → SSGTM |
| MQL | qualificou (se aplicável na LP) | GTM Web → SSGTM |
| Contact | clique no botão WhatsApp | GTM Web → SSGTM |
| SQL | qualificou no comercial | Back-pass (Sheets/CRM → SSGTM) |
| Purchase | venda fechada | Back-pass (Sheets/CRM → SSGTM) |

## 4. Schema de dados (contrato)

> **TODO próximo chat:** consolidar o schema das 24 colunas da planilha do WK como padrão de dados.
> Definir: nome do campo, tipo, origem, obrigatoriedade, validação.

## 5. Valores controlados

### Status
`Lead | MQL | SQL | Cliente | Perdido`

### Motivo Perdido
`Fora do perfil | Sem orçamento | Foi pra concorrente | Sem retorno do cliente | Projeto cancelado | Timing errado | Outro`

### Origem (padrão `Canal - Ativo`)
- `LP - <nome da LP>`
- `Meta Lead Ads - <nome do form>`
- `WhatsApp Direto - LP | Ads | Outros`
- `Indicação`
- `Outros`

## 6. Modelo de valor (proxy)

**Modelo A (recomendado): LUCRO como proxy**

Fórmulas:
```
Lucro/venda = Ticket Médio × Margem Bruta
Valor SQL   = Lucro × Taxa SQL→Venda
Valor MQL   = Valor SQL × Taxa MQL→SQL
Valor Lead  = Valor MQL × Taxa Lead→MQL
```

Diferenciar valores por canal quando taxas variam (ex: Google qualifica melhor que Meta).

## 7. Critérios de auditoria

Ver `checklist-auditoria.md`.

## 8. Implementações por ferramenta

- `implementacoes/sheets.md` — clientes sem CRM (maioria)
- `implementacoes/crm-kommo.md` — clientes com Kommo
- (futuras): `crm-rd.md`, `crm-hubspot.md`, `crm-pipedrive.md`

## 9. Princípios não-negociáveis

1. **Deduplicação Browser+Server sempre** — Pixel sozinho não vale
2. **Token CAPI em gerenciador de senhas** — nunca em prints/commits
3. **Test code apagado antes de produção** — senão eventos viram teste
4. **Funil completo até Venda** — tracking só está pronto com back-pass funcionando
5. **Auditoria obrigatória antes do go-live**

---

## Próximos passos para completar este documento

1. [ ] Expandir seção 1 (a dor) — usar conversa-inicial como insumo
2. [ ] Detalhar seção 4 (schema completo das 24 colunas)
3. [ ] Adicionar exemplos numéricos no Modelo A
4. [ ] Listar EMQ mínimo aceitável e como medir
5. [ ] Detalhar processo de versionamento deste documento
