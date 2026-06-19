import pandas as pd
import streamlit as st

from services.comercial import compras_e_orcamentos_cliente
from services.db import get_connection


def render():
    st.title("Base de Clientes")

    with get_connection() as conn:
        vendedores = [
            r[0]
            for r in conn.execute("""
                SELECT vendedor FROM (
                    SELECT DISTINCT vendedor FROM clientes WHERE vendedor IS NOT NULL AND vendedor <> ''
                    UNION
                    SELECT DISTINCT vendedor FROM orcamentos WHERE vendedor IS NOT NULL AND vendedor <> ''
                    UNION
                    SELECT DISTINCT vendedor FROM vendas WHERE vendedor IS NOT NULL AND vendedor <> ''
                )
                ORDER BY vendedor
            """).fetchall()
        ]

    c1, c2 = st.columns([2, 1])
    termo = c1.text_input("Buscar cliente, fantasia, CNPJ, CPF, telefone ou e-mail")
    vendedor = c2.selectbox("Vendedora", ["Todas"] + vendedores)

    query = """
        SELECT
            c.id,
            COALESCE(c.nome_fantasia, c.nome) AS cliente,
            c.nome,
            c.nome_fantasia,
            c.cnpj,
            c.cpf,
            COALESCE(c.celular, c.telefone) AS telefone,
            c.email,
            c.vendedor,
            v.ultima_compra,
            COALESCE(v.compras, 0) AS compras,
            COALESCE(v.valor_comprado, 0) AS valor_comprado,
            COALESCE(o.orcamentos, 0) AS orcamentos,
            o.ultimo_orcamento
        FROM clientes c
        LEFT JOIN (
            SELECT cliente_id, MAX(data) AS ultima_compra, COUNT(*) AS compras, SUM(COALESCE(valor_total, 0)) AS valor_comprado
            FROM vendas
            GROUP BY cliente_id
        ) v ON v.cliente_id=c.id
        LEFT JOIN (
            SELECT cliente_id, MAX(data) AS ultimo_orcamento, COUNT(*) AS orcamentos
            FROM orcamentos
            GROUP BY cliente_id
        ) o ON o.cliente_id=c.id
    """
    filtros = []
    params = []
    if termo:
        like = f"%{termo}%"
        filtros.append("""
            (
                c.nome LIKE ? OR c.nome_fantasia LIKE ? OR c.cnpj LIKE ? OR c.cpf LIKE ?
                OR c.telefone LIKE ? OR c.celular LIKE ? OR c.email LIKE ?
            )
        """)
        params.extend([like, like, like, like, like, like, like])
    if vendedor != "Todas":
        filtros.append("c.vendedor=?")
        params.append(vendedor)
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += " ORDER BY cliente"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        st.warning("Nenhum cliente encontrado.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes encontrados", len(df))
    c2.metric("Clientes com compra", int((df["compras"] > 0).sum()))
    c3.metric("Clientes com orçamento", int((df["orcamentos"] > 0).sum()))

    st.dataframe(df, use_container_width=True, hide_index=True)

    labels = {
        f"{row.get('cliente')} | {row.get('cnpj') or row.get('cpf') or 'sem documento'}": row
        for row in df.to_dict("records")
    }
    selecionado = st.selectbox("Ver detalhes do cliente", list(labels.keys()))
    cliente = labels[selecionado]
    dados = compras_e_orcamentos_cliente(str(cliente["id"]))

    tab_compras, tab_orcamentos = st.tabs(["Compras do cliente", "Orçamentos do cliente"])
    with tab_compras:
        st.dataframe(dados["compras"], use_container_width=True, hide_index=True)
    with tab_orcamentos:
        st.dataframe(dados["orcamentos"], use_container_width=True, hide_index=True)
