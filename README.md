# Central Comercial Novaprint

Sistema web em Python + Streamlit para operação comercial da Novaprint, conectado ao GestãoClick, Watidy e OpenAI.

## Como instalar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar local

```bash
streamlit run app.py
```

Main file path para Streamlit Cloud:

```text
app.py
```

## Configuração

Copie `.env.example` para `.env` e preencha:

```env
GESTAOCLICK_ACCESS_TOKEN=
GESTAOCLICK_SECRET_TOKEN=
GESTAOCLICK_STORE_ID=
OPENAI_API_KEY=
WATIDY_API_URL=
WATIDY_API_TOKEN=
WATIDY_SEND_PATH=
WATIDY_NUMBER_FIELD=numero
WATIDY_MESSAGE_FIELD=mensagem
WATIDY_AUTH_HEADER=Authorization
WATIDY_TOKEN_PREFIX=Bearer
```

No Streamlit Cloud, use os mesmos nomes em **Settings > Secrets**.

## Fluxo comercial com Watidy

1. Vá em **Configurações** e sincronize os dados reais do GestãoClick.
2. Ainda em **Configurações**, cadastre o WhatsApp das vendedoras.
3. Use **CRM e Orçamentos** para trabalhar clientes com orçamento aberto há 2 dias ou mais.
4. Use **Análise de Cliente** para buscar um cliente e ver compras, orçamentos, produtos, histórico e mensagem.
5. Use **Portal das Vendedoras** para filtrar carteira e orçamentos por vendedora.
6. Cada envio para cliente ou vendedora fica salvo no histórico Watidy do cliente.

## Relatório diário das 08:00

O app tenta enviar automaticamente, uma vez por dia após 08:00, o relatório de clientes que cada vendedora precisa ligar.

Regras do relatório:

- orçamento aberto com 2 dias ou mais;
- cliente identificado, telefone, vendedora, valor e produtos quando disponíveis;
- envio agrupado por vendedora para o WhatsApp cadastrado em **Configurações**.

Importante: em Streamlit, o envio automático roda quando o app está ativo depois das 08:00. Se o app estiver desligado, use o botão **Enviar relatório diário agora** dentro de **CRM e Orçamentos**.

Campos opcionais do Watidy:

- `WATIDY_SEND_PATH`: caminho do endpoint de envio, caso `WATIDY_API_URL` seja apenas a URL base.
- `WATIDY_NUMBER_FIELD`: nome do campo de telefone no JSON. Padrão: `numero`.
- `WATIDY_MESSAGE_FIELD`: nome do campo de mensagem no JSON. Padrão: `mensagem`.
- `WATIDY_AUTH_HEADER`: nome do cabeçalho do token. Padrão: `Authorization`.
- `WATIDY_TOKEN_PREFIX`: prefixo do token. Padrão: `Bearer`.

Se aparecer `Cannot POST /api/enviar-texto`, o servidor foi encontrado, mas a rota de envio está errada. Ajuste `WATIDY_API_URL` e `WATIDY_SEND_PATH` com a rota exata fornecida pelo Watidy e teste em **Configurações > Diagnóstico e envio de teste do Watidy**.

## Observações

- O sistema não usa clientes fictícios.
- A análise depende de dados reais sincronizados do GestãoClick.
- Observações, agendamentos, contatos e mensagens Watidy são compartilhados entre os módulos pelo mesmo SQLite local.
