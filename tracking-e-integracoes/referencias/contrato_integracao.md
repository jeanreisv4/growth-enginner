# Contrato dos agentes de integração

Todo agente `integracao-*` devolve dois arquivos em `<SAIDA>/` e termina com uma linha de resumo.

## `<SAIDA>/integracao-<frente>.json`

```json
{
  "frente": "crm | meta | google-ads | conversacional",
  "cliente": "<cliente>",
  "periodo": "2026-09-01..2026-09-30",
  "resumo": "uma frase com o número que importa",
  "numeros": {"<chave>": {"valor": 0, "unidade": "", "fonte": ""}},
  "achados": [{
    "id": "CRM-01",
    "titulo": "Automação parou de criar lead no CRM em 31/08",
    "evidencia": "57 de 66 leads do formulário de 16 a 30/09 fora do CRM (Graph /{form}/leads × /contacts por telefone)",
    "gravidade": "critica | alta | media | baixa",
    "confianca": "alta | media | baixa",
    "correcao": {"o_que": "", "como": "", "risco": "R1 | R2 | R3", "testar_antes": "", "desfazer": ""}
  }],
  "cobertura": [{"verificacao": "entrada formulário × CRM por semana", "status": "ok | achado | nao_medido | nao_se_aplica"}],
  "perguntas": ["o que só o usuário responde"],
  "fontes": ["o que foi lido, de onde, e o que ficou sem ler"]
}
```

- **Risco**: R1 lê ou cria algo desligado/secundário; R2 muda algo em produção que se desfaz com backup; R3 mexe
  em dado de cliente final, lance ou publicação (sempre com ok explícito do usuário para aquela mudança).
- Nenhum nome, telefone ou e-mail de pessoa nos achados; nenhum token em arquivo, JSON ou print.

## `<SAIDA>/integracao-<frente>.md`

O mesmo em texto corrido para o usuário: o que funciona, o que quebrou (com número e data), o que corrigir primeiro.

## Regras comuns

1. **Somente leitura** por padrão. Escrita em cliente (n8n, CRM, GTM, conta de anúncios) volta como correção proposta;
   quem aplica é a conversa principal, com ok explícito do usuário.
2. **Testar sem gravar** antes de propor ligar: workflow temporário com o nó de gravação desligado, `validateOnly`,
   código de teste do Meta. Workflow temporário é apagado no fim.
3. **Backup** do workflow (JSON) antes de qualquer proposta de mudança nele.
4. **Credencial**: segredo nunca passa pelo chat nem por arquivo do repositório; vai para `~/.config/<pasta>/` com
   `pbpaste >` ou direto na interface. Script que usa segredo roda por caminho absoluto em `~/Cursor/...`.
5. Casar pessoa por **telefone (DDD + 8 dígitos)**, nunca por nome.
