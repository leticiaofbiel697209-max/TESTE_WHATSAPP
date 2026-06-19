import pandas as pd
import streamlit as st

from services.db import (
    get_connection,
    listar_mensagens_watidy,
    marcar_ja_liguei,
    obter_whatsapp_vendedora,
    registrar_mensagem_watidy,
    salvar_agendamento,
    salvar_observacao,
)
from services.mensagens import (
    mensagem_cliente_padrao,
    mensagem_vendedora_padrao,
    telefone_cliente,
)
from services.watidy_api import enviar_mensagem


def _enviar_e_registrar(cliente, destino_tipo: str, numero: str, mensagem: str, origem: str):
    try:
        resposta = enviar_mensagem(numero, mensagem)
        registrar_mensagem_watidy(
            cliente_id=str(cliente["id"]),
            vendedor=cliente.get("vendedor") or "",
            destino_tipo=destino_tipo,
            numero=numero,
            mensagem=mensagem,
            status="enviado",
            resposta=resposta,
        )
        st.success(f"Mensagem enviada para {destino_tipo} pelo Watidy.")
    except Exception as exc:
        registrar_mensagem_watidy(
            cliente_id=str(cliente["id"]),
            vendedor=cliente.get("vendedor") or "",
            destino_tipo=destino_tipo,
            numero=numero,
            mensagem=mensagem,
            status="erro",
            erro=str(exc),
        )
        st.error(str(exc))


def render():
    st.title("CRM")
    with get_connection() as conn:
        clientes = pd.read_sql_query("SELECT * FROM clientes ORDER BY atualizado_em DESC", conn)
    if clientes.empty:
        st.warning("Nenhum cliente sincronizado.")
        return

    st.dataframe(clientes, use_container_width=True)
    cliente_id = st.selectbox("Cliente para ação", clientes["id"].astype(str).tolist())
    cliente = clientes[clientes["id"].astype(str) == cliente_id].iloc[0].to_dict()

    st.subheader(cliente.get("nome_fantasia") or cliente.get("nome") or "Cliente")
    st.caption(f"Vendedora: {cliente.get('vendedor') or 'não informada'}")

    obs = st.text_area("Observação")
    col1, col2 = st.columns(2)
    if col1.button("Salvar observação no CRM") and obs.strip():
        salvar_observacao(cliente_id, "CRM", "usuario", obs.strip())
        st.success("Observação salva.")
    data = col2.date_input("Retorno")
    if st.button("Agendar retorno no CRM"):
        salvar_agendamento(cliente_id, "CRM", "usuario", str(data), obs)
        st.success("Agendamento salvo.")
    if st.button("Marcar Já Liguei no CRM"):
        marcar_ja_liguei(cliente_id, "CRM")
        st.success("Já Liguei registrado.")

    st.divider()
    st.subheader("WhatsApp pelo Watidy")
    tab_cliente, tab_vendedora, tab_historico = st.tabs(["Cliente", "Vendedora", "Histórico"])

    with tab_cliente:
        numero_cliente = st.text_input("Número do cliente", value=telefone_cliente(cliente))
        mensagem_cliente = st.text_area(
            "Mensagem para o cliente",
            value=mensagem_cliente_padrao(cliente),
            height=150,
            key=f"crm_msg_cliente_{cliente_id}",
        )
        if st.button("Enviar para cliente via Watidy"):
            _enviar_e_registrar(cliente, "cliente", numero_cliente, mensagem_cliente, "CRM")

    with tab_vendedora:
        numero_vendedora = st.text_input(
            "WhatsApp da vendedora",
            value=obter_whatsapp_vendedora(cliente.get("vendedor") or ""),
            help="Cadastre ou ajuste esse número em Configurações.",
        )
        mensagem_vendedora = st.text_area(
            "Mensagem para a vendedora",
            value=mensagem_vendedora_padrao(cliente, mensagem_cliente_padrao(cliente)),
            height=170,
            key=f"crm_msg_vendedora_{cliente_id}",
        )
        if st.button("Enviar para vendedora via Watidy"):
            _enviar_e_registrar(cliente, "vendedora", numero_vendedora, mensagem_vendedora, "CRM")

    with tab_historico:
        mensagens = listar_mensagens_watidy(cliente_id)
        if mensagens:
            st.dataframe(pd.DataFrame(mensagens), use_container_width=True)
        else:
            st.info("Nenhuma mensagem Watidy registrada para este cliente.")
