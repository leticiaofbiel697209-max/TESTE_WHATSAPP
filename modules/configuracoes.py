import pandas as pd
import streamlit as st

from services.db import (
    contar_registros,
    get_connection,
    listar_vendedoras_contatos,
    salvar_vendedora_contato,
)
from services.gestaoclick_api import sincronizar_dados, testar_conexao as testar_gestaoclick
from services.openai_service import testar_conexao as testar_openai
from services.watidy_api import testar_conexao as testar_watidy


def _nomes_vendedoras_sincronizadas():
    with get_connection() as conn:
        return [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT vendedor FROM clientes WHERE vendedor IS NOT NULL AND vendedor <> '' ORDER BY vendedor"
            ).fetchall()
        ]


def render():
    st.title("Configurações")
    st.info("Configure as chaves no .env local ou no st.secrets do Streamlit Cloud.")

    st.subheader("Conexões")
    c1, c2, c3 = st.columns(3)
    if c1.button("Testar GestãoClick"):
        try:
            st.success(testar_gestaoclick()["mensagem"])
        except Exception as e:
            st.error(str(e))
    if c2.button("Testar OpenAI"):
        try:
            st.success(testar_openai()["mensagem"])
        except Exception as e:
            st.error(str(e))
    if c3.button("Testar Watidy"):
        try:
            st.write(testar_watidy())
            st.success("Teste Watidy concluído.")
        except Exception as e:
            st.error(str(e))

    st.subheader("Sincronização GestãoClick")
    if st.button("Sincronizar dados reais agora"):
        try:
            with st.spinner("Sincronizando clientes, vendas e orçamentos reais..."):
                resultado = sincronizar_dados()
            st.success(f"Sincronização concluída: {resultado}")
        except Exception as e:
            st.error(str(e))

    st.subheader("WhatsApp das vendedoras")
    nomes = _nomes_vendedoras_sincronizadas()
    nome = st.selectbox("Vendedora", nomes) if nomes else st.text_input("Vendedora")
    whatsapp = st.text_input("WhatsApp com DDD", placeholder="11999999999")
    ativo = st.checkbox("Ativa", value=True)
    if st.button("Salvar WhatsApp da vendedora"):
        try:
            salvar_vendedora_contato(nome, whatsapp, ativo)
            st.success("Contato da vendedora salvo.")
        except Exception as e:
            st.error(str(e))

    contatos = listar_vendedoras_contatos()
    if contatos:
        st.dataframe(pd.DataFrame(contatos), use_container_width=True)
    else:
        st.info("Nenhum WhatsApp de vendedora cadastrado ainda.")

    st.subheader("Registros salvos no SQLite")
    st.json(contar_registros())
