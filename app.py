from datetime import datetime, time
import os

import streamlit as st

from modules import analise_cliente, base_clientes, churn, configuracoes, crm, dashboard, portal_vendedoras
from services.comercial import enviar_relatorio_diario_vendedoras
from services.db import init_db

st.set_page_config(page_title="Central Comercial Novaprint", layout="wide")
init_db()


def _config(name: str) -> str:
    try:
        if name in st.secrets and st.secrets[name]:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, "")


def _tentar_relatorio_0800():
    if datetime.now().time() < time(8, 0):
        return
    if not _config("WATIDY_API_URL") or not _config("WATIDY_API_TOKEN"):
        return
    try:
        enviar_relatorio_diario_vendedoras(force=False)
    except Exception:
        pass


_tentar_relatorio_0800()

st.sidebar.title("Central Comercial Novaprint")
st.sidebar.caption("CRM CEO integrado ao GestãoClick e Watidy")
menu = st.sidebar.radio("Menu", [
    "Dashboard CEO",
    "Análise de Cliente",
    "CRM e Orçamentos",
    "Portal das Vendedoras",
    "Churn",
    "Base de Clientes",
    "Configurações",
])

st.markdown("""
<style>
.block-container {padding-top: 1.5rem;}
[data-testid="stSidebar"] {background: #111827;}
[data-testid="stSidebar"] * {color: #f9fafb;}
.stMetric {background: #f9fafb; border: 1px solid #e5e7eb; padding: 14px; border-radius: 14px;}
</style>
""", unsafe_allow_html=True)

try:
    if menu == "Dashboard CEO":
        dashboard.render()
    elif menu == "Análise de Cliente":
        analise_cliente.render()
    elif menu == "CRM e Orçamentos":
        crm.render()
    elif menu == "Portal das Vendedoras":
        portal_vendedoras.render()
    elif menu == "Churn":
        churn.render()
    elif menu == "Base de Clientes":
        base_clientes.render()
    elif menu == "Configurações":
        configuracoes.render()
except Exception as exc:
    st.error("Ocorreu um erro na aplicação.")
    st.exception(exc)
