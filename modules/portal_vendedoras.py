import pandas as pd
import streamlit as st

from services.comercial import produtos_resumo
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


def _enviar_e_registrar(cliente, destino_tipo: str, numero: str, mensagem: str):
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
    st.title("Portal das Vendedoras")
    with get_connection() as conn:
        vendedores = [
            r[0]
            for r in conn.execute(
                """
                SELECT vendedor FROM (
                    SELECT DISTINCT vendedor FROM clientes WHERE vendedor IS NOT NULL AND vendedor <> ''
                    UNION
                    SELECT DISTINCT vendedor FROM orcamentos WHERE vendedor IS NOT NULL AND vendedor <> ''
                    UNION
                    SELECT DISTINCT vendedor FROM vendas WHERE vendedor IS NOT NULL AND vendedor <> ''
                    UNION
                    SELECT DISTINCT nome AS vendedor FROM vendedores_contatos WHERE nome IS NOT NULL AND nome <> ''
                )
                ORDER BY vendedor
                """
            ).fetchall()
        ]
    vendedor = st.selectbox("Vendedor responsável", vendedores) if vendedores else None
    if not vendedor:
        st.warning("Nenhum vendedor encontrado nos clientes sincronizados.")
        return

    with get_connection() as conn:
        clientes = pd.read_sql_query("""
            SELECT DISTINCT c.*
            FROM clientes c
            LEFT JOIN orcamentos o ON o.cliente_id=c.id
            LEFT JOIN vendas v ON v.cliente_id=c.id
            WHERE c.vendedor=? OR o.vendedor=? OR v.vendedor=?
            ORDER BY c.nome
        """, conn, params=(vendedor, vendedor, vendedor))
        orc = pd.read_sql_query("""
            SELECT
                o.*,
                COALESCE(c.nome_fantasia, c.nome) AS cliente,
                COALESCE(c.celular, c.telefone) AS telefone
            FROM orcamentos o
            LEFT JOIN clientes c ON c.id=o.cliente_id
            WHERE COALESCE(NULLIF(o.vendedor, ''), c.vendedor)=?
            ORDER BY o.data DESC
            LIMIT 300
        """, conn, params=(vendedor,))

    st.subheader("Carteira")
    carteira = clientes.copy()
    if not carteira.empty:
        carteira["cliente"] = carteira["nome_fantasia"].fillna("").where(carteira["nome_fantasia"].fillna("") != "", carteira["nome"])
        carteira["telefone_contato"] = carteira["celular"].fillna("").where(carteira["celular"].fillna("") != "", carteira["telefone"])
        carteira = carteira[["id", "cliente", "cnpj", "cpf", "telefone_contato", "email", "vendedor"]]
    st.dataframe(carteira, use_container_width=True, hide_index=True)
    st.subheader("Orçamentos do vendedor")
    if not orc.empty:
        orc["produtos"] = orc["produtos_json"].apply(produtos_resumo)
        colunas_orc = ["cliente", "telefone", "codigo", "data", "valor_total", "status", "produtos"]
        st.dataframe(orc[colunas_orc], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum orçamento encontrado para esta vendedora.")

    if clientes.empty:
        st.info("Essa vendedora ainda não tem clientes vinculados na base sincronizada.")
        return

    opcoes_clientes = {
        f"{r.get('nome_fantasia') or r.get('nome')} | {r.get('cnpj') or r.get('cpf') or r.get('id')}": r
        for r in clientes.to_dict("records")
    }
    cliente_label = st.selectbox("Cliente", list(opcoes_clientes.keys()))
    cliente = opcoes_clientes[cliente_label]
    cliente_id = str(cliente["id"])

    texto = st.text_area("Observação compartilhada")
    if st.button("Salvar observação") and texto.strip():
        salvar_observacao(cliente_id, "Portal das Vendedoras", vendedor, texto.strip())
        st.success("Observação salva e visível nos outros módulos.")
    data = st.date_input("Agendar retorno")
    if st.button("Salvar agendamento"):
        salvar_agendamento(cliente_id, "Portal das Vendedoras", vendedor, str(data), texto)
        st.success("Agendamento salvo e visível nos outros módulos.")
    if st.button("Já liguei"):
        marcar_ja_liguei(cliente_id, "Portal das Vendedoras", vendedor)
        st.success("Contato registrado.")

    st.divider()
    st.subheader("WhatsApp pelo Watidy")
    tab_cliente, tab_vendedora, tab_historico = st.tabs(["Cliente", "Minha vendedora", "Histórico"])

    with tab_cliente:
        numero_cliente = st.text_input("Número do cliente", value=telefone_cliente(cliente))
        mensagem_cliente = st.text_area(
            "Mensagem para o cliente",
            value=mensagem_cliente_padrao(cliente),
            height=150,
            key=f"portal_msg_cliente_{cliente_id}",
        )
        if st.button("Enviar para cliente via Watidy"):
            _enviar_e_registrar(cliente, "cliente", numero_cliente, mensagem_cliente)

    with tab_vendedora:
        numero_vendedora = st.text_input(
            "WhatsApp da vendedora",
            value=obter_whatsapp_vendedora(vendedor),
            help="Cadastre ou ajuste esse número em Configurações.",
        )
        mensagem_vendedora = st.text_area(
            "Mensagem para a vendedora",
            value=mensagem_vendedora_padrao(cliente, mensagem_cliente_padrao(cliente)),
            height=170,
            key=f"portal_msg_vendedora_{cliente_id}",
        )
        if st.button("Enviar aviso para vendedora via Watidy"):
            _enviar_e_registrar(cliente, "vendedora", numero_vendedora, mensagem_vendedora)

    with tab_historico:
        mensagens = listar_mensagens_watidy(cliente_id)
        if mensagens:
            st.dataframe(pd.DataFrame(mensagens), use_container_width=True)
        else:
            st.info("Nenhuma mensagem Watidy registrada para este cliente.")
