import ast
import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from services.db import get_connection, obter_whatsapp_vendedora, registrar_mensagem_watidy
from services.watidy_api import enviar_mensagem


STATUS_FECHADOS = (
    "aprov",
    "cancel",
    "convert",
    "fatur",
    "final",
    "perdid",
    "recus",
    "vend",
)


def parse_data(value: Any) -> Optional[date]:
    if not value:
        return None
    texto = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(texto[:19], fmt).date()
        except ValueError:
            continue
    return None


def cliente_nome(row: Dict[str, Any]) -> str:
    return row.get("nome_fantasia") or row.get("nome") or row.get("cliente_nome") or "Cliente sem nome"


def telefone_cliente(row: Dict[str, Any]) -> str:
    return row.get("celular") or row.get("telefone") or ""


def produtos_resumo(raw: Any, limite: int = 3) -> str:
    if not raw:
        return ""
    itens = _parse_produtos(raw)
    nomes = []
    for item in itens:
        nome = _nome_produto(item)
        if not nome:
            continue
        qtd = item.get("quantidade") or item.get("qtde") or item.get("qtd")
        valor = item.get("valor_total") or item.get("total") or item.get("valor_venda")
        partes = [str(nome)]
        if qtd:
            partes.append(f"qtd {qtd}")
        if valor:
            partes.append(f"R$ {valor}")
        nomes.append(" - ".join(partes))
    return "; ".join(nomes[:limite])


def _parse_valor(raw: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str):
        return raw
    texto = raw.strip()
    if not texto:
        return None
    try:
        return json.loads(texto)
    except Exception:
        pass
    try:
        return ast.literal_eval(texto)
    except Exception:
        return raw


def _parse_produtos(raw: Any) -> List[Dict[str, Any]]:
    valor = _parse_valor(raw)
    if isinstance(valor, dict):
        valor = [valor]
    produtos = []
    for item in valor or []:
        item = _parse_valor(item)
        if not isinstance(item, dict):
            continue
        produto = _parse_valor(item.get("produto"))
        if isinstance(produto, dict):
            mesclado = {**produto, **{k: v for k, v in item.items() if k != "produto"}}
            produtos.append(mesclado)
        else:
            produtos.append(item)
    return produtos


def _nome_produto(item: Dict[str, Any]) -> str:
    return str(
        item.get("nome_produto")
        or item.get("nome")
        or item.get("descricao")
        or item.get("detalhes")
        or item.get("produto_nome")
        or item.get("titulo")
        or ""
    ).strip()


def status_aberto(status: Any) -> bool:
    texto = str(status or "").lower()
    return not any(palavra in texto for palavra in STATUS_FECHADOS)


def orcamentos_para_ligar(dias_minimos: int = 2, vendedor: Optional[str] = None, dias_maximos: int = 45) -> pd.DataFrame:
    query = """
        SELECT
            o.id,
            o.cliente_id,
            o.codigo,
            o.data,
            o.valor_total,
            o.status,
            COALESCE(NULLIF(o.vendedor, ''), c.vendedor) AS vendedor,
            o.produtos_json,
            o.observacoes,
            c.nome,
            c.nome_fantasia,
            c.cnpj,
            c.cpf,
            c.telefone,
            c.celular,
            c.email
        FROM orcamentos o
        LEFT JOIN clientes c ON c.id = o.cliente_id
    """
    params = []
    if vendedor:
        query += " WHERE COALESCE(NULLIF(o.vendedor, ''), c.vendedor)=?"
        params.append(vendedor)
    query += " ORDER BY o.data DESC LIMIT 2000"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    if df.empty:
        return df

    hoje = date.today()
    linhas = []
    for row in df.to_dict("records"):
        data_orcamento = parse_data(row.get("data"))
        if not data_orcamento:
            continue
        idade = (hoje - data_orcamento).days
        if idade < dias_minimos or idade > dias_maximos or not status_aberto(row.get("status")):
            continue
        row["cliente"] = cliente_nome(row)
        row["telefone_contato"] = telefone_cliente(row)
        row["idade_dias"] = idade
        row["produtos"] = produtos_resumo(row.get("produtos_json"))
        row["valor_total"] = float(row.get("valor_total") or 0)
        linhas.append(row)

    resultado = pd.DataFrame(linhas)
    if not resultado.empty:
        resultado = resultado.sort_values(["vendedor", "idade_dias", "valor_total"], ascending=[True, False, False])
    return resultado


def compras_e_orcamentos_cliente(cliente_id: str) -> Dict[str, pd.DataFrame]:
    with get_connection() as conn:
        compras = pd.read_sql_query(
            "SELECT * FROM vendas WHERE cliente_id=? ORDER BY data DESC LIMIT 200",
            conn,
            params=(cliente_id,),
        )
        orcamentos = pd.read_sql_query(
            "SELECT * FROM orcamentos WHERE cliente_id=? ORDER BY data DESC LIMIT 200",
            conn,
            params=(cliente_id,),
        )
    if not compras.empty:
        compras["produtos"] = compras["produtos_json"].apply(produtos_resumo)
    if not orcamentos.empty:
        orcamentos["produtos"] = orcamentos["produtos_json"].apply(produtos_resumo)
    return {"compras": compras, "orcamentos": orcamentos}


def texto_relatorio_vendedora(vendedor: str, df: pd.DataFrame) -> str:
    total = float(df["valor_total"].fillna(0).sum()) if not df.empty else 0
    clientes = int(df["cliente_id"].nunique()) if not df.empty else 0
    linhas = [
        f"Bom dia, {vendedor}!",
        "",
        "RELATÓRIO COMERCIAL - FOLLOW-UP DE ORÇAMENTOS",
        f"Clientes para ligar: {clientes}",
        f"Orçamentos em aberto: {len(df)}",
        f"Valor em negociação: R$ {total:,.2f}",
        "",
        "Prioridade de hoje:",
        "",
    ]
    ordenado = df.sort_values(["valor_total", "idade_dias"], ascending=[False, False])
    for idx, row in enumerate(ordenado.to_dict("records"), start=1):
        valor = float(row.get("valor_total") or 0)
        linhas.append(
            f"{idx}. {row.get('cliente')} - R$ {valor:,.2f}"
        )
        linhas.append(f"   Contato: {row.get('telefone_contato') or 'sem telefone'}")
        linhas.append(f"   Orçamento: {row.get('codigo') or row.get('id')} | {row.get('idade_dias')} dias em aberto")
        if row.get("produtos"):
            linhas.append(f"   Produtos: {row.get('produtos')}")
    linhas.append("")
    linhas.append("Ação: ligar, registrar retorno no CRM e atualizar próximo passo.")
    return "\n".join(linhas)


def enviar_relatorio_diario_vendedoras(force: bool = False) -> Dict[str, Any]:
    hoje = date.today().isoformat()
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rotinas_envio (
                chave TEXT,
                data TEXT,
                status TEXT,
                detalhe TEXT,
                criado_em TEXT,
                PRIMARY KEY (chave, data)
            )
        """)
        ja_enviado = conn.execute(
            "SELECT status FROM rotinas_envio WHERE chave='relatorio_0800' AND data=? AND status='enviado'",
            (hoje,),
        ).fetchone()
        if ja_enviado and not force:
            return {"enviado": False, "motivo": "Relatório de hoje já foi enviado."}

    df = orcamentos_para_ligar(dias_minimos=2)
    if df.empty:
        return {"enviado": False, "motivo": "Nenhum orçamento aberto com 2 dias ou mais."}

    enviados = []
    erros = []
    for vendedor, grupo in df.groupby("vendedor", dropna=True):
        if not vendedor:
            continue
        numero = obter_whatsapp_vendedora(str(vendedor))
        if not numero:
            erros.append({"vendedor": vendedor, "erro": "WhatsApp da vendedora não cadastrado."})
            continue
        mensagem = texto_relatorio_vendedora(str(vendedor), grupo)
        try:
            resposta = enviar_mensagem(numero, mensagem)
            registrar_mensagem_watidy("", str(vendedor), "vendedora_relatorio_diario", numero, mensagem, "enviado", resposta)
            enviados.append({"vendedor": vendedor, "clientes": int(len(grupo))})
        except Exception as exc:
            registrar_mensagem_watidy("", str(vendedor), "vendedora_relatorio_diario", numero, mensagem, "erro", erro=str(exc))
            erros.append({"vendedor": vendedor, "erro": str(exc)})

    status = "enviado" if enviados else "erro"
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO rotinas_envio (chave, data, status, detalhe, criado_em) VALUES ('relatorio_0800', ?, ?, ?, ?)",
            (hoje, status, json.dumps({"enviados": enviados, "erros": erros}, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    return {"enviado": bool(enviados), "enviados": enviados, "erros": erros}
