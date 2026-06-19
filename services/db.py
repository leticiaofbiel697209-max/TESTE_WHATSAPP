import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "central_comercial.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id TEXT PRIMARY KEY,
                nome TEXT,
                nome_fantasia TEXT,
                cnpj TEXT,
                cpf TEXT,
                telefone TEXT,
                celular TEXT,
                email TEXT,
                vendedor TEXT,
                atualizado_em TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id TEXT PRIMARY KEY,
                cliente_id TEXT,
                codigo TEXT,
                data TEXT,
                valor_total REAL,
                status TEXT,
                vendedor TEXT,
                produtos_json TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orcamentos (
                id TEXT PRIMARY KEY,
                cliente_id TEXT,
                codigo TEXT,
                data TEXT,
                valor_total REAL,
                status TEXT,
                vendedor TEXT,
                produtos_json TEXT,
                observacoes TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS observacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id TEXT,
                origem TEXT,
                usuario TEXT,
                texto TEXT NOT NULL,
                criado_em TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id TEXT,
                origem TEXT,
                usuario TEXT,
                data_retorno TEXT,
                observacao TEXT,
                concluido INTEGER DEFAULT 0,
                criado_em TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id TEXT,
                origem TEXT,
                canal TEXT,
                resultado TEXT,
                observacao TEXT,
                criado_em TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendedores_contatos (
                nome TEXT PRIMARY KEY,
                whatsapp TEXT,
                ativo INTEGER DEFAULT 1,
                atualizado_em TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mensagens_watidy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id TEXT,
                vendedor TEXT,
                destino_tipo TEXT,
                numero TEXT,
                mensagem TEXT,
                status TEXT,
                resposta_json TEXT,
                erro TEXT,
                criado_em TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        """)
        conn.commit()


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _json(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False, default=str)


def salvar_cliente(cliente: Dict[str, Any]):
    cliente_id = str(cliente.get("id") or cliente.get("codigo") or cliente.get("cliente_id") or "").strip()
    if not cliente_id:
        raise ValueError("Cliente sem ID retornado pelo GestãoClick.")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO clientes (id, nome, nome_fantasia, cnpj, cpf, telefone, celular, email, vendedor, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nome=excluded.nome,
                nome_fantasia=excluded.nome_fantasia,
                cnpj=excluded.cnpj,
                cpf=excluded.cpf,
                telefone=excluded.telefone,
                celular=excluded.celular,
                email=excluded.email,
                vendedor=excluded.vendedor,
                atualizado_em=excluded.atualizado_em
        """, (
            cliente_id,
            cliente.get("nome") or cliente.get("razao_social"),
            cliente.get("nome_fantasia") or cliente.get("fantasia"),
            cliente.get("cnpj"),
            cliente.get("cpf"),
            cliente.get("telefone"),
            cliente.get("celular"),
            cliente.get("email"),
            cliente.get("vendedor") or cliente.get("vendedor_nome"),
            _now(),
        ))
        conn.commit()


def salvar_venda(venda: Dict[str, Any]):
    venda_id = str(venda.get("id") or venda.get("codigo") or venda.get("numero") or "").strip()
    if not venda_id:
        raise ValueError("Venda sem ID retornada pelo GestãoClick.")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO vendas (id, cliente_id, codigo, data, valor_total, status, vendedor, produtos_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                cliente_id=excluded.cliente_id,
                codigo=excluded.codigo,
                data=excluded.data,
                valor_total=excluded.valor_total,
                status=excluded.status,
                vendedor=excluded.vendedor,
                produtos_json=excluded.produtos_json
        """, (
            venda_id,
            str(venda.get("cliente_id") or venda.get("id_cliente") or venda.get("cliente", {}).get("id") or ""),
            venda.get("codigo") or venda.get("numero"),
            venda.get("data") or venda.get("data_venda") or venda.get("criado_em"),
            float(venda.get("valor_total") or venda.get("total") or 0),
            venda.get("status") or venda.get("situacao"),
            venda.get("vendedor") or venda.get("vendedor_nome"),
            _json(venda.get("produtos") or venda.get("itens")),
        ))
        conn.commit()


def salvar_orcamento(orcamento: Dict[str, Any]):
    orcamento_id = str(orcamento.get("id") or orcamento.get("codigo") or orcamento.get("numero") or "").strip()
    if not orcamento_id:
        raise ValueError("Orçamento sem ID retornado pelo GestãoClick.")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO orcamentos (id, cliente_id, codigo, data, valor_total, status, vendedor, produtos_json, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                cliente_id=excluded.cliente_id,
                codigo=excluded.codigo,
                data=excluded.data,
                valor_total=excluded.valor_total,
                status=excluded.status,
                vendedor=excluded.vendedor,
                produtos_json=excluded.produtos_json,
                observacoes=excluded.observacoes
        """, (
            orcamento_id,
            str(orcamento.get("cliente_id") or orcamento.get("id_cliente") or orcamento.get("cliente", {}).get("id") or ""),
            orcamento.get("codigo") or orcamento.get("numero"),
            orcamento.get("data") or orcamento.get("data_orcamento") or orcamento.get("criado_em"),
            float(orcamento.get("valor_total") or orcamento.get("total") or 0),
            orcamento.get("status") or orcamento.get("situacao"),
            orcamento.get("vendedor") or orcamento.get("vendedor_nome"),
            _json(orcamento.get("produtos") or orcamento.get("itens")),
            orcamento.get("observacoes") or orcamento.get("observacao"),
        ))
        conn.commit()


def salvar_observacao(cliente_id: str, origem: str, usuario: str, texto: str):
    with get_connection() as conn:
        conn.execute("INSERT INTO observacoes (cliente_id, origem, usuario, texto, criado_em) VALUES (?, ?, ?, ?, ?)",
                     (cliente_id, origem, usuario, texto, _now()))
        conn.commit()


def listar_observacoes(cliente_id: str) -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM observacoes WHERE cliente_id=? ORDER BY criado_em DESC", (cliente_id,)).fetchall()
        return [dict(r) for r in rows]


def salvar_agendamento(cliente_id: str, origem: str, usuario: str, data_retorno: str, observacao: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO agendamentos (cliente_id, origem, usuario, data_retorno, observacao, concluido, criado_em)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (cliente_id, origem, usuario, data_retorno, observacao, _now()))
        conn.commit()


def listar_agendamentos(cliente_id: Optional[str] = None) -> List[dict]:
    with get_connection() as conn:
        if cliente_id:
            rows = conn.execute("SELECT * FROM agendamentos WHERE cliente_id=? ORDER BY data_retorno ASC", (cliente_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM agendamentos ORDER BY data_retorno ASC").fetchall()
        return [dict(r) for r in rows]


def marcar_ja_liguei(cliente_id: str, origem: str = "CRM", usuario: str = "usuario", observacao: str = "Já liguei"):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO contatos (cliente_id, origem, canal, resultado, observacao, criado_em)
            VALUES (?, ?, 'telefone', 'ja_liguei', ?, ?)
        """, (cliente_id, origem, observacao, _now()))
        conn.commit()


def salvar_vendedora_contato(nome: str, whatsapp: str, ativo: bool = True):
    nome = (nome or "").strip()
    whatsapp = (whatsapp or "").strip()
    if not nome:
        raise ValueError("Informe o nome da vendedora.")
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO vendedores_contatos (nome, whatsapp, ativo, atualizado_em)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(nome) DO UPDATE SET
                whatsapp=excluded.whatsapp,
                ativo=excluded.ativo,
                atualizado_em=excluded.atualizado_em
        """, (nome, whatsapp, 1 if ativo else 0, _now()))
        conn.commit()


def listar_vendedoras_contatos() -> List[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM vendedores_contatos ORDER BY nome").fetchall()
        return [dict(r) for r in rows]


def obter_whatsapp_vendedora(nome: str) -> str:
    if not nome:
        return ""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT whatsapp FROM vendedores_contatos WHERE nome=? AND ativo=1",
            (nome,),
        ).fetchone()
        return str(row["whatsapp"] or "") if row else ""


def registrar_mensagem_watidy(
    cliente_id: str,
    vendedor: str,
    destino_tipo: str,
    numero: str,
    mensagem: str,
    status: str,
    resposta: Any = None,
    erro: str = "",
):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO mensagens_watidy
                (cliente_id, vendedor, destino_tipo, numero, mensagem, status, resposta_json, erro, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            vendedor,
            destino_tipo,
            numero,
            mensagem,
            status,
            json.dumps(resposta or {}, ensure_ascii=False, default=str),
            erro,
            _now(),
        ))
        conn.commit()


def listar_mensagens_watidy(cliente_id: Optional[str] = None) -> List[dict]:
    with get_connection() as conn:
        if cliente_id:
            rows = conn.execute(
                "SELECT * FROM mensagens_watidy WHERE cliente_id=? ORDER BY criado_em DESC",
                (cliente_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM mensagens_watidy ORDER BY criado_em DESC").fetchall()
        return [dict(r) for r in rows]


def listar_historico_cliente(cliente_id: str) -> Dict[str, List[dict]]:
    with get_connection() as conn:
        return {
            "observacoes": [dict(r) for r in conn.execute("SELECT * FROM observacoes WHERE cliente_id=? ORDER BY criado_em DESC", (cliente_id,)).fetchall()],
            "agendamentos": [dict(r) for r in conn.execute("SELECT * FROM agendamentos WHERE cliente_id=? ORDER BY data_retorno ASC", (cliente_id,)).fetchall()],
            "contatos": [dict(r) for r in conn.execute("SELECT * FROM contatos WHERE cliente_id=? ORDER BY criado_em DESC", (cliente_id,)).fetchall()],
            "mensagens_watidy": [dict(r) for r in conn.execute("SELECT * FROM mensagens_watidy WHERE cliente_id=? ORDER BY criado_em DESC", (cliente_id,)).fetchall()],
            "orcamentos": [dict(r) for r in conn.execute("SELECT * FROM orcamentos WHERE cliente_id=? ORDER BY data DESC", (cliente_id,)).fetchall()],
            "vendas": [dict(r) for r in conn.execute("SELECT * FROM vendas WHERE cliente_id=? ORDER BY data DESC", (cliente_id,)).fetchall()],
        }


def contar_registros() -> Dict[str, int]:
    with get_connection() as conn:
        return {
            "clientes": conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
            "vendas": conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0],
            "orcamentos": conn.execute("SELECT COUNT(*) FROM orcamentos").fetchone()[0],
        }
