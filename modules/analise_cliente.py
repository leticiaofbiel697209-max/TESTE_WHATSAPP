import json

import pandas as pd
import streamlit as st

from services import analytics
from services.comercial import compras_e_orcamentos_cliente
from services.db import (get_connection, listar_agendamentos, listar_historico_cliente,
                         listar_observacoes, marcar_ja_liguei, salvar_agendamento,
                         salvar_observacao, obter_whatsapp_vendedora,
                         registrar_mensagem_watidy)
from services.mensagens import mensagem_vendedora_padrao
from services.openai_service import gerar_mensagem_whatsapp
from services.watidy_api import enviar_mensagem


def _buscar_clientes_local(termo: str):
    if not termo:
        return []
    like = f"%{termo}%"
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM clientes
            WHERE nome LIKE ? OR nome_fantasia LIKE ? OR cnpj LIKE ? OR cpf LIKE ?
            ORDER BY nome LIMIT 50
        """, (like, like, like, like)).fetchall()
        return [dict(r) for r in rows]


def _vendas(cliente_id: str):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM vendas WHERE cliente_id=? ORDER BY data DESC", (cliente_id,)).fetchall()]


def _orcamentos(cliente_id: str):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM orcamentos WHERE cliente_id=? ORDER BY data DESC", (cliente_id,)).fetchall()]


def render():
    st.title("Análise de Cliente")
    st.warning("A análise só funciona após selecionar um cliente real sincronizado do GestãoClick.")

    termo = st.text_input("Buscar por razão social, nome fantasia ou CNPJ")
    clientes = _buscar_clientes_local(termo)
    if not termo:
        st.info("Digite parte do nome, fantasia ou CNPJ para localizar um cliente real.")
        return
    if not clientes:
        st.error("Nenhum cliente encontrado no banco local. Sincronize o GestãoClick em Configurações.")
        return

    labels = {f"{c.get('nome') or ''} | {c.get('nome_fantasia') or ''} | {c.get('cnpj') or c.get('cpf') or ''}": c for c in clientes}
    selecionado_label = st.selectbox("Clientes encontrados", list(labels.keys()))
    cliente = labels[selecionado_label]
    cliente_id = cliente["id"]

    vendas = _vendas(cliente_id)
    orcamentos = _orcamentos(cliente_id)
    compras_orcamentos = compras_e_orcamentos_cliente(cliente_id)
    observacoes = listar_observacoes(cliente_id)
    agendamentos = listar_agendamentos(cliente_id)
    historico = listar_historico_cliente(cliente_id)

    ultima = analytics.calcular_ultima_compra(vendas)
    dias = analytics.calcular_dias_sem_comprar(ultima)
    ticket = analytics.calcular_ticket_medio(vendas)
    freq = analytics.calcular_frequencia_compra(vendas)
    produtos = analytics.produtos_mais_comprados(vendas)
    sugestao = analytics.sugerir_recompra_regra(vendas)

    st.subheader(cliente.get("nome") or "Cliente sem nome")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Última compra", ultima.strftime("%d/%m/%Y") if ultima else "Sem histórico")
    c2.metric("Dias sem comprar", dias if dias is not None else "-")
    c3.metric("Ticket médio", f"R$ {ticket:,.2f}")
    c4.metric("Frequência média", f"{freq} dias" if freq else "Insuficiente")

    st.write({
        "nome": cliente.get("nome"),
        "nome_fantasia": cliente.get("nome_fantasia"),
        "cnpj": cliente.get("cnpj"),
        "telefone": cliente.get("telefone") or cliente.get("celular"),
        "email": cliente.get("email"),
        "vendedor": cliente.get("vendedor"),
    })

    st.subheader("O que este cliente compra e orça")
    tab_compras_cliente, tab_orcamentos_cliente = st.tabs(["Compras", "Orçamentos"])
    with tab_compras_cliente:
        compras_df = compras_orcamentos["compras"]
        if compras_df.empty:
            st.info("Nenhuma compra encontrada para este cliente.")
        else:
            colunas = [c for c in ["data", "codigo", "valor_total", "status", "vendedor", "produtos"] if c in compras_df.columns]
            st.dataframe(compras_df[colunas], use_container_width=True, hide_index=True)
    with tab_orcamentos_cliente:
        orc_df = compras_orcamentos["orcamentos"]
        if orc_df.empty:
            st.info("Nenhum orçamento encontrado para este cliente.")
        else:
            colunas = [c for c in ["data", "codigo", "valor_total", "status", "vendedor", "produtos", "observacoes"] if c in orc_df.columns]
            st.dataframe(orc_df[colunas], use_container_width=True, hide_index=True)

    st.subheader("Sugestão de recompra")
    st.write("Produto sugerido:", sugestao.get("produto_sugerido") or "Sem sugestão segura")
    st.write("Motivo:", sugestao.get("motivo"))

    st.subheader("Produtos mais comprados")
    if produtos:
        st.dataframe(pd.DataFrame(produtos), use_container_width=True)
    else:
        st.info("Sem produtos comprados registrados nas vendas sincronizadas.")

    tab1, tab2, tab3, tab4 = st.tabs(["Observações", "Agendamentos", "WhatsApp", "JSON real"])

    with tab1:
        texto = st.text_area("Nova observação")
        if st.button("Salvar observação"):
            if texto.strip():
                salvar_observacao(cliente_id, "Análise de Cliente", "usuario", texto.strip())
                st.success("Observação salva.")
                st.rerun()
            else:
                st.error("Digite uma observação.")
        st.dataframe(pd.DataFrame(observacoes), use_container_width=True)

    with tab2:
        data_retorno = st.date_input("Data de retorno")
        obs_ret = st.text_input("Observação do retorno")
        if st.button("Agendar retorno"):
            salvar_agendamento(cliente_id, "Análise de Cliente", "usuario", str(data_retorno), obs_ret)
            st.success("Retorno agendado.")
            st.rerun()
        if st.button("Marcar Já Liguei"):
            marcar_ja_liguei(cliente_id, "Análise de Cliente")
            st.success("Contato registrado como Já Liguei.")
            st.rerun()
        st.dataframe(pd.DataFrame(agendamentos), use_container_width=True)

    with tab3:
        contexto = {"cliente": cliente, "vendas": vendas, "orcamentos": orcamentos, "sugestao": sugestao}
        if st.button("Gerar mensagem WhatsApp com IA"):
            try:
                st.session_state["mensagem_whatsapp"] = gerar_mensagem_whatsapp(cliente, contexto)
            except Exception as e:
                st.error(str(e))
        mensagem = st.text_area("Mensagem", value=st.session_state.get("mensagem_whatsapp", ""), height=160)
        numero = st.text_input("Número para envio", value=cliente.get("celular") or cliente.get("telefone") or "")
        if st.button("Enviar via waTidy agora"):
            try:
                resposta = enviar_mensagem(numero, mensagem)
                registrar_mensagem_watidy(
                    cliente_id=cliente_id,
                    vendedor=cliente.get("vendedor") or "",
                    destino_tipo="cliente",
                    numero=numero,
                    mensagem=mensagem,
                    status="enviado",
                    resposta=resposta,
                )
                st.success("Mensagem enviada pelo waTidy.")
            except Exception as e:
                registrar_mensagem_watidy(
                    cliente_id=cliente_id,
                    vendedor=cliente.get("vendedor") or "",
                    destino_tipo="cliente",
                    numero=numero,
                    mensagem=mensagem,
                    status="erro",
                    erro=str(e),
                )
                st.error(str(e))

        st.divider()
        st.markdown("**Avisar vendedora responsável**")
        numero_vendedora = st.text_input(
            "Número da vendedora",
            value=obter_whatsapp_vendedora(cliente.get("vendedor") or ""),
        )
        mensagem_vendedora = st.text_area(
            "Mensagem para vendedora",
            value=mensagem_vendedora_padrao(cliente, mensagem),
            height=150,
        )
        if st.button("Enviar aviso para vendedora via waTidy"):
            try:
                resposta = enviar_mensagem(numero_vendedora, mensagem_vendedora)
                registrar_mensagem_watidy(
                    cliente_id=cliente_id,
                    vendedor=cliente.get("vendedor") or "",
                    destino_tipo="vendedora",
                    numero=numero_vendedora,
                    mensagem=mensagem_vendedora,
                    status="enviado",
                    resposta=resposta,
                )
                st.success("Aviso enviado para a vendedora pelo waTidy.")
            except Exception as e:
                registrar_mensagem_watidy(
                    cliente_id=cliente_id,
                    vendedor=cliente.get("vendedor") or "",
                    destino_tipo="vendedora",
                    numero=numero_vendedora,
                    mensagem=mensagem_vendedora,
                    status="erro",
                    erro=str(e),
                )
                st.error(str(e))

    with tab4:
        dados_reais = {
            "cliente": cliente,
            "vendas": vendas,
            "orcamentos": orcamentos,
            "observacoes": observacoes,
            "agendamentos": agendamentos,
            "historico": historico,
            "metricas": {
                "ultima_compra": str(ultima) if ultima else None,
                "dias_sem_comprar": dias,
                "ticket_medio": ticket,
                "frequencia_media": freq,
                "produtos_mais_comprados": produtos,
                "sugestao": sugestao,
            },
        }
        st.json(dados_reais)
