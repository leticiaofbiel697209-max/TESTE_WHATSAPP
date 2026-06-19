import pandas as pd
import streamlit as st

from services.analytics import (
    calcular_dias_sem_comprar,
    calcular_frequencia_compra,
    calcular_ticket_medio,
    calcular_ultima_compra,
    produtos_mais_comprados,
)
from services.db import get_connection


def _risco(dias, freq):
    if dias is None:
        return "Sem compra"
    if not freq:
        return "Histórico curto"
    if dias > freq * 2:
        return "Crítico"
    if dias > freq * 1.5:
        return "Alto"
    if dias > freq:
        return "Médio"
    return "Baixo"


def _prioridade(risco: str) -> int:
    return {
        "Crítico": 1,
        "Alto": 2,
        "Médio": 3,
        "Histórico curto": 4,
        "Baixo": 5,
        "Sem compra": 6,
    }.get(risco, 9)


def render():
    st.title("Churn")
    st.caption("Clientes que estão passando do próprio ciclo médio de compra.")

    with get_connection() as conn:
        clientes = [dict(r) for r in conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()]
        vendas = [dict(r) for r in conn.execute("SELECT * FROM vendas ORDER BY data DESC").fetchall()]

    linhas = []
    for c in clientes:
        cv = [v for v in vendas if str(v.get("cliente_id")) == str(c.get("id"))]
        ultima = calcular_ultima_compra(cv)
        dias = calcular_dias_sem_comprar(ultima)
        freq = calcular_frequencia_compra(cv)
        risco = _risco(dias, freq)
        produtos = produtos_mais_comprados(cv)
        linhas.append({
            "prioridade": _prioridade(risco),
            "risco_churn": risco,
            "cliente_id": c.get("id"),
            "cliente": c.get("nome_fantasia") or c.get("nome"),
            "telefone": c.get("celular") or c.get("telefone"),
            "vendedor": c.get("vendedor"),
            "ultima_compra": ultima,
            "dias_sem_comprar": dias,
            "frequencia_media": freq,
            "ticket_medio": calcular_ticket_medio(cv),
            "produto_mais_comprado": produtos[0]["produto"] if produtos else "",
            "compras": len(cv),
        })

    df = pd.DataFrame(linhas)
    if df.empty:
        st.warning("Nenhum cliente sincronizado.")
        return

    vendedores = sorted([v for v in df["vendedor"].dropna().unique().tolist() if v])
    c1, c2 = st.columns([1, 1])
    vendedor = c1.selectbox("Vendedora", ["Todas"] + vendedores)
    risco_filtro = c2.selectbox("Risco", ["Todos", "Crítico", "Alto", "Médio", "Baixo", "Histórico curto", "Sem compra"])

    filtrado = df.copy()
    if vendedor != "Todas":
        filtrado = filtrado[filtrado["vendedor"] == vendedor]
    if risco_filtro != "Todos":
        filtrado = filtrado[filtrado["risco_churn"] == risco_filtro]
    filtrado = filtrado.sort_values(["prioridade", "dias_sem_comprar"], ascending=[True, False])

    m1, m2, m3 = st.columns(3)
    m1.metric("Críticos", int((df["risco_churn"] == "Crítico").sum()))
    m2.metric("Alto risco", int((df["risco_churn"] == "Alto").sum()))
    m3.metric("Para observar", int((df["risco_churn"] == "Médio").sum()))

    colunas = [
        "risco_churn",
        "cliente",
        "telefone",
        "vendedor",
        "ultima_compra",
        "dias_sem_comprar",
        "frequencia_media",
        "ticket_medio",
        "produto_mais_comprado",
        "compras",
    ]
    st.dataframe(filtrado[colunas], use_container_width=True, hide_index=True)
