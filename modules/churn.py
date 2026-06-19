import pandas as pd
import streamlit as st
from services.analytics import calcular_dias_sem_comprar, calcular_frequencia_compra, calcular_ultima_compra
from services.db import get_connection


def render():
    st.title("Churn")
    with get_connection() as conn:
        clientes = [dict(r) for r in conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()]
        vendas = [dict(r) for r in conn.execute("SELECT * FROM vendas ORDER BY data DESC").fetchall()]
    linhas = []
    for c in clientes:
        cv = [v for v in vendas if str(v.get("cliente_id")) == str(c.get("id"))]
        ultima = calcular_ultima_compra(cv)
        dias = calcular_dias_sem_comprar(ultima)
        freq = calcular_frequencia_compra(cv)
        risco = "Sem histórico"
        if dias is not None and freq:
            risco = "Alto" if dias > freq * 1.5 else "Médio" if dias > freq else "Baixo"
        linhas.append({"cliente_id": c.get("id"), "nome": c.get("nome"), "vendedor": c.get("vendedor"), "ultima_compra": ultima, "dias_sem_comprar": dias, "frequencia_media": freq, "risco_churn": risco})
    st.dataframe(pd.DataFrame(linhas), use_container_width=True)
