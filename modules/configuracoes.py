import streamlit as st
from services.db import contar_registros
from services.gestaoclick_api import sincronizar_dados, testar_conexao as testar_gestaoclick
from services.openai_service import testar_conexao as testar_openai
from services.watidy_api import testar_conexao as testar_watidy


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
    if c3.button("Testar waTidy"):
        try:
            st.write(testar_watidy())
            st.success("Teste waTidy concluído.")
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

    st.subheader("Registros salvos no SQLite")
    st.json(contar_registros())
