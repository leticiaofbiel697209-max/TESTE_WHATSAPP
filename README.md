# Central Comercial Novaprint

Sistema web em Python + Streamlit para operação comercial da Novaprint, conectado ao GestãoClick, preparado para waTidy e OpenAI.

## 1. Como instalar

```bash
git clone SEU_REPOSITORIO
cd central_comercial_novaprint
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux/Mac:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Como rodar local

```bash
streamlit run app.py
```

Main file path correto para Streamlit Cloud:

```text
app.py
```

## 3. Como configurar `.env`

Copie o arquivo:

```bash
copy .env.example .env
```

Preencha:

```env
GESTAOCLICK_ACCESS_TOKEN=
GESTAOCLICK_SECRET_TOKEN=
GESTAOCLICK_STORE_ID=
OPENAI_API_KEY=
WATIDY_API_URL=
WATIDY_API_TOKEN=
```

As chaves nunca ficam no código.

## 4. Como configurar secrets no Streamlit Cloud

No Streamlit Cloud, abra o app, vá em **Settings > Secrets** e configure:

```toml
GESTAOCLICK_ACCESS_TOKEN=""
GESTAOCLICK_SECRET_TOKEN=""
GESTAOCLICK_STORE_ID=""
OPENAI_API_KEY=""
WATIDY_API_URL=""
WATIDY_API_TOKEN=""
```

## 5. Como sincronizar GestãoClick

1. Abra o sistema.
2. Vá em **Configurações**.
3. Clique em **Testar GestãoClick**.
4. Clique em **Sincronizar dados reais agora**.
5. O sistema buscará clientes, vendas e orçamentos reais e salvará no SQLite local.

## 6. Como testar waTidy

1. Configure `WATIDY_API_URL` e `WATIDY_API_TOKEN`.
2. Vá em **Configurações**.
3. Clique em **Testar waTidy**.
4. O envio de mensagem só acontece manualmente, com clique humano, na tela de Análise de Cliente.

## 7. Como publicar no GitHub

```bash
git init
git add .
git commit -m "Central Comercial Novaprint inicial"
git branch -M main
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

Depois, no Streamlit Cloud, selecione o repositório e use:

```text
Main file path: app.py
```

## 8. Avisos importantes

- O sistema não possui dados fictícios.
- O sistema não usa clientes de exemplo.
- O sistema não usa JSON fixo como fonte principal.
- A análise de cliente depende de cliente real sincronizado do GestãoClick.
- Observações, agendamentos, histórico de contatos e status "Já Liguei" são compartilhados entre módulos pelo mesmo banco SQLite.
