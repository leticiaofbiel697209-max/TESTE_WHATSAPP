import pandas as pd
import streamlit as st

from services.comercial import orcamentos_para_ligar
from services.db import contar_registros, get_connection, listar_agendamentos


def _valor_total(df: pd.DataFrame) -> float:
    if df.empty or "valor_total" not in df:
        return 0.0
    return float(df["valor_total"].fillna(0).sum())


def render():
    st.title("Dashboard CEO")
    counts = contar_registros()
    orc_ligar = orcamentos_para_ligar(dias_minimos=2, dias_maximos=45)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes na base", counts["clientes"])
    c2.metric("Vendas sincronizadas", counts["vendas"])
    c3.metric("Orçamentos abertos +2 dias", len(orc_ligar))
    c4.metric("Valor em follow-up", f"R$ {_valor_total(orc_ligar):,.2f}")

    st.subheader("Clientes que precisam de ligação")
    if orc_ligar.empty:
        st.success("Nenhum orçamento aberto com 2 dias ou mais.")
    else:
        colunas = [
            "cliente",
            "telefone_contato",
            "vendedor",
            "codigo",
            "data",
            "idade_dias",
            "valor_total",
            "status",
            "produtos",
        ]
        st.dataframe(orc_ligar[colunas], use_container_width=True, hide_index=True)

        por_vendedora = (
            orc_ligar.groupby("vendedor", dropna=False)
            .agg(clientes=("cliente_id", "nunique"), orcamentos=("id", "count"), valor=("valor_total", "sum"))
            .reset_index()
            .sort_values("valor", ascending=False)
        )
        st.subheader("Resumo por vendedora")
        st.dataframe(por_vendedora, use_container_width=True, hide_index=True)

    with get_connection() as conn:
        vendas = pd.read_sql_query("""
            SELECT
                v.data,
                v.valor_total,
                v.status,
                v.vendedor,
                COALESCE(c.nome_fantasia, c.nome) AS cliente,
                COALESCE(c.celular, c.telefone) AS telefone
            FROM vendas v
            LEFT JOIN clientes c ON c.id=v.cliente_id
            ORDER BY v.data DESC
            LIMIT 100
        """, conn)
        orc = pd.read_sql_query("""
            SELECT
                o.data,
                o.valor_total,
                o.status,
                COALESCE(NULLIF(o.vendedor, ''), c.vendedor) AS vendedor,
                COALESCE(c.nome_fantasia, c.nome) AS cliente,
                COALESCE(c.celular, c.telefone) AS telefone,
                o.codigo
            FROM orcamentos o
            LEFT JOIN clientes c ON c.id=o.cliente_id
            ORDER BY o.data DESC
            LIMIT 100
        """, conn)

    tab_vendas, tab_orcamentos, tab_retornos = st.tabs(["Vendas recentes", "Orçamentos recentes", "Retornos"])
    with tab_vendas:
        st.dataframe(vendas, use_container_width=True, hide_index=True)
    with tab_orcamentos:
        st.dataframe(orc, use_container_width=True, hide_index=True)
    with tab_retornos:
        st.dataframe(pd.DataFrame(listar_agendamentos()), use_container_width=True, hide_index=True)
