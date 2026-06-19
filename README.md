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
```

No Streamlit Cloud, use os mesmos nomes em **Settings > Secrets**.

## Fluxo comercial com Watidy

1. Vá em **Configurações** e sincronize os dados reais do GestãoClick.
2. Ainda em **Configurações**, cadastre o WhatsApp das vendedoras.
3. Use **CRM**, **Portal das Vendedoras** ou **Análise de Cliente** para enviar mensagens via Watidy.
4. Cada envio para cliente ou vendedora fica salvo no histórico Watidy do cliente.

Campos opcionais do Watidy:

- `WATIDY_SEND_PATH`: caminho do endpoint de envio, caso `WATIDY_API_URL` seja apenas a URL base.
- `WATIDY_NUMBER_FIELD`: nome do campo de telefone no JSON. Padrão: `numero`.
- `WATIDY_MESSAGE_FIELD`: nome do campo de mensagem no JSON. Padrão: `mensagem`.

## Observações

- O sistema não usa clientes fictícios.
- A análise depende de dados reais sincronizados do GestãoClick.
- Observações, agendamentos, contatos e mensagens Watidy são compartilhados entre os módulos pelo mesmo SQLite local.
