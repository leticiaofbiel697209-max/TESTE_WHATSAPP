import streamlit as st
from services.db import init_db
from modules import analise_cliente, base_clientes, churn, configuracoes, crm, dashboard, orcamentos, portal_vendedoras

st.set_page_config(page_title="Central Comercial Novaprint", layout="wide")
init_db()

st.sidebar.title("Central Comercial Novaprint")
st.sidebar.caption("CRM CEO integrado ao GestãoClick")
menu = st.sidebar.radio("Menu", [
    "Dashboard CEO",
    "Análise de Cliente",
    "CRM",
    "Portal das Vendedoras",
    "Orçamentos",
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
    elif menu == "CRM":
        crm.render()
    elif menu == "Portal das Vendedoras":
        portal_vendedoras.render()
    elif menu == "Orçamentos":
        orcamentos.render()
    elif menu == "Churn":
        churn.render()
    elif menu == "Base de Clientes":
        base_clientes.render()
    elif menu == "Configurações":
        configuracoes.render()
except Exception as exc:
    st.error("Ocorreu um erro na aplicação.")
    st.exception(exc)
