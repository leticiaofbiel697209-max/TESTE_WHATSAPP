import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

from services.db import salvar_cliente, salvar_orcamento, salvar_venda

load_dotenv()
BASE_URL = "https://api.gestaoclick.com"


def _config(name: str) -> str:
    try:
        if name in st.secrets and st.secrets[name]:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, "")


def _headers() -> Dict[str, str]:
    access = _config("GESTAOCLICK_ACCESS_TOKEN")
    secret = _config("GESTAOCLICK_SECRET_TOKEN")
    if not access or not secret:
        raise RuntimeError("Configure GESTAOCLICK_ACCESS_TOKEN e GESTAOCLICK_SECRET_TOKEN.")
    return {
        "access-token": access,
        "secret-access-token": secret,
        "Content-Type": "application/json",
    }


def _get(path: str, params: Optional[dict] = None) -> Any:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Erro GestãoClick {resp.status_code}: {resp.text[:500]}")
    return resp.json()


def _extract_items(payload: Any) -> List[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "dados", "items", "result", "clientes", "vendas", "orcamentos"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = _extract_items(value)
                if nested:
                    return nested
    return []


def testar_conexao() -> Dict[str, Any]:
    payload = _get("/clientes", params={"limit": 1})
    return {"ok": True, "mensagem": "Conexão com GestãoClick realizada.", "amostra": payload}


def listar_clientes() -> List[dict]:
    return _extract_items(_get("/clientes"))


def buscar_cliente_por_nome_ou_cnpj(termo: str) -> List[dict]:
    termo = (termo or "").strip()
    if not termo:
        return []
    try:
        return _extract_items(_get("/clientes", params={"search": termo}))
    except Exception:
        clientes = listar_clientes()
        termo_lower = termo.lower()
        return [c for c in clientes if termo_lower in str(c.get("nome") or c.get("razao_social") or "").lower()
                or termo_lower in str(c.get("nome_fantasia") or c.get("fantasia") or "").lower()
                or termo_lower in str(c.get("cnpj") or c.get("cpf") or "").lower()]


def buscar_cliente_por_id(cliente_id: str) -> Optional[dict]:
    payload = _get(f"/clientes/{cliente_id}")
    if isinstance(payload, dict):
        return payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return None


def listar_vendas_cliente(cliente_id: str) -> List[dict]:
    return _extract_items(_get("/vendas", params={"cliente_id": cliente_id}))


def listar_orcamentos_cliente(cliente_id: str) -> List[dict]:
    return _extract_items(_get("/orcamentos", params={"cliente_id": cliente_id}))


def listar_vendas_periodo(data_inicio: str) -> List[dict]:
    return _extract_items(_get("/vendas", params={"data_inicio": data_inicio}))


def listar_orcamentos_periodo(data_inicio: str) -> List[dict]:
    return _extract_items(_get("/orcamentos", params={"data_inicio": data_inicio}))


def sincronizar_dados() -> Dict[str, int]:
    clientes = listar_clientes()
    vendas_total = 0
    orcamentos_total = 0
    for cliente in clientes:
        salvar_cliente(cliente)
        cliente_id = str(cliente.get("id") or cliente.get("codigo") or cliente.get("cliente_id") or "")
        if not cliente_id:
            continue
        vendas = listar_vendas_cliente(cliente_id)
        for venda in vendas:
            venda.setdefault("cliente_id", cliente_id)
            salvar_venda(venda)
            vendas_total += 1
        orcamentos = listar_orcamentos_cliente(cliente_id)
        for orcamento in orcamentos:
            orcamento.setdefault("cliente_id", cliente_id)
            salvar_orcamento(orcamento)
            orcamentos_total += 1
    return {"clientes": len(clientes), "vendas": vendas_total, "orcamentos": orcamentos_total}
