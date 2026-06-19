import pandas as pd
import streamlit as st

from services.comercial import (
    compras_e_orcamentos_cliente,
    enviar_relatorio_diario_vendedoras,
    orcamentos_para_ligar,
    texto_relatorio_vendedora,
)
from services.db import (
    get_connection,
    listar_mensagens_watidy,
    marcar_ja_liguei,
    obter_whatsapp_vendedora,
    registrar_mensagem_watidy,
    salvar_agendamento,
    salvar_observacao,
)
from services.mensagens import mensagem_cliente_padrao, mensagem_vendedora_padrao, telefone_cliente
from services.watidy_api import enviar_mensagem


def _enviar_e_registrar(cliente, destino_tipo: str, numero: str, mensagem: str):
    try:
        resposta = enviar_mensagem(numero, mensagem)
        registrar_mensagem_watidy(
            cliente_id=str(cliente.get("id") or cliente.get("cliente_id") or ""),
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
            cliente_id=str(cliente.get("id") or cliente.get("cliente_id") or ""),
            vendedor=cliente.get("vendedor") or "",
            destino_tipo=destino_tipo,
            numero=numero,
            mensagem=mensagem,
            status="erro",
            erro=str(exc),
        )
        st.error(str(exc))


def _buscar_clientes(termo: str) -> pd.DataFrame:
    with get_connection() as conn:
        if termo:
            like = f"%{termo}%"
            return pd.read_sql_query("""
                SELECT * FROM clientes
                WHERE nome LIKE ? OR nome_fantasia LIKE ? OR cnpj LIKE ? OR cpf LIKE ?
                ORDER BY nome
                LIMIT 80
            """, conn, params=(like, like, like, like))
        return pd.read_sql_query("SELECT * FROM clientes ORDER BY atualizado_em DESC LIMIT 80", conn)


def _painel_cliente(cliente):
    cliente_id = str(cliente.get("id") or cliente.get("cliente_id") or "")
    st.caption(f"Vendedora: {cliente.get('vendedor') or 'não informada'}")

    col1, col2, col3 = st.columns(3)
    obs = col1.text_area("Observação", key=f"obs_{cliente_id}")
    data = col2.date_input("Retorno", key=f"retorno_{cliente_id}")
    col3.write("")
    col3.write("")
    if col1.button("Salvar observação", key=f"salvar_obs_{cliente_id}") and obs.strip():
        salvar_observacao(cliente_id, "CRM", "usuario", obs.strip())
        st.success("Observação salva.")
    if col2.button("Agendar retorno", key=f"agendar_{cliente_id}"):
        salvar_agendamento(cliente_id, "CRM", "usuario", str(data), obs)
        st.success("Retorno agendado.")
    if col3.button("Já liguei", key=f"liguei_{cliente_id}"):
        marcar_ja_liguei(cliente_id, "CRM")
        st.success("Contato registrado.")

    tab_cliente, tab_vendedora, tab_historico, tab_movimento = st.tabs([
        "Mensagem ao cliente",
        "Avisar vendedora",
        "Histórico Watidy",
        "Compras e orçamentos",
    ])

    with tab_cliente:
        numero_cliente = st.text_input("Número do cliente", value=telefone_cliente(cliente), key=f"num_cliente_{cliente_id}")
        mensagem_cliente = st.text_area(
            "Mensagem para o cliente",
            value=mensagem_cliente_padrao(cliente),
            height=150,
            key=f"msg_cliente_{cliente_id}",
        )
        if st.button("Enviar para cliente via Watidy", key=f"env_cliente_{cliente_id}"):
            _enviar_e_registrar(cliente, "cliente", numero_cliente, mensagem_cliente)

    with tab_vendedora:
        numero_vendedora = st.text_input(
            "WhatsApp da vendedora",
            value=obter_whatsapp_vendedora(cliente.get("vendedor") or ""),
            key=f"num_vendedora_{cliente_id}",
        )
        mensagem_vendedora = st.text_area(
            "Mensagem para a vendedora",
            value=mensagem_vendedora_padrao(cliente, mensagem_cliente_padrao(cliente)),
            height=170,
            key=f"msg_vendedora_{cliente_id}",
        )
        if st.button("Enviar para vendedora via Watidy", key=f"env_vendedora_{cliente_id}"):
            _enviar_e_registrar(cliente, "vendedora", numero_vendedora, mensagem_vendedora)

    with tab_historico:
        mensagens = listar_mensagens_watidy(cliente_id)
        if mensagens:
            st.dataframe(pd.DataFrame(mensagens), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma mensagem Watidy registrada para este cliente.")

    with tab_movimento:
        dados = compras_e_orcamentos_cliente(cliente_id)
        st.markdown("**Compras**")
        st.dataframe(dados["compras"], use_container_width=True, hide_index=True)
        st.markdown("**Orçamentos**")
        st.dataframe(dados["orcamentos"], use_container_width=True, hide_index=True)


def render():
    st.title("CRM e Orçamentos")
    st.caption("Prioridade: clientes com orçamento aberto há 2 dias ou mais.")

    tab_follow, tab_busca, tab_relatorio = st.tabs(["Para ligar hoje", "Buscar cliente", "Relatório diário 08:00"])

    with tab_follow:
        vendedor_filtro = st.text_input("Filtrar vendedora", placeholder="Opcional")
        df = orcamentos_para_ligar(dias_minimos=2, vendedor=vendedor_filtro.strip() or None)
        if df.empty:
            st.success("Nenhum orçamento aberto com 2 dias ou mais para este filtro.")
        else:
            colunas = ["cliente", "telefone_contato", "vendedor", "codigo", "data", "idade_dias", "valor_total", "status", "produtos"]
            st.dataframe(df[colunas], use_container_width=True, hide_index=True)

            opcoes = {
                f"{row['cliente']} | {row.get('codigo') or row.get('id')} | {row.get('vendedor')} | {row.get('idade_dias')} dias": row
                for row in df.to_dict("records")
            }
            escolha = st.selectbox("Selecionar orçamento para ação", list(opcoes.keys()))
            row = opcoes[escolha]
            cliente = {
                "id": row.get("cliente_id"),
                "nome": row.get("nome"),
                "nome_fantasia": row.get("nome_fantasia"),
                "telefone": row.get("telefone"),
                "celular": row.get("celular"),
                "email": row.get("email"),
                "vendedor": row.get("vendedor"),
            }
            st.subheader(row.get("cliente"))
            st.write({
                "orçamento": row.get("codigo") or row.get("id"),
                "data": row.get("data"),
                "dias_em_aberto": row.get("idade_dias"),
                "valor": row.get("valor_total"),
                "status": row.get("status"),
                "produtos": row.get("produtos"),
            })
            _painel_cliente(cliente)

    with tab_busca:
        termo = st.text_input("Buscar por cliente, fantasia, CNPJ ou CPF")
        clientes = _buscar_clientes(termo.strip())
        if clientes.empty:
            st.warning("Nenhum cliente encontrado.")
        else:
            st.dataframe(clientes, use_container_width=True, hide_index=True)
            labels = {
                f"{r.get('nome_fantasia') or r.get('nome')} | {r.get('cnpj') or r.get('cpf') or ''}": r
                for r in clientes.to_dict("records")
            }
            selecionado = st.selectbox("Cliente", list(labels.keys()))
            _painel_cliente(labels[selecionado])

    with tab_relatorio:
        df = orcamentos_para_ligar(dias_minimos=2)
        if df.empty:
            st.info("Nenhum cliente para incluir no relatório diário.")
        else:
            vendedores = [v for v in df["vendedor"].dropna().unique().tolist() if v]
            vendedor = st.selectbox("Prévia por vendedora", vendedores)
            previa = texto_relatorio_vendedora(vendedor, df[df["vendedor"] == vendedor])
            st.text_area("Prévia da mensagem das 08:00", value=previa, height=260)
            if st.button("Enviar relatório diário agora"):
                st.write(enviar_relatorio_diario_vendedoras(force=True))
        st.info("O envio automático dispara uma vez ao dia quando o app estiver rodando depois das 08:00.")
