import os
import re
from typing import Dict
from urllib.parse import urljoin

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _config(name: str) -> str:
    try:
        if name in st.secrets and st.secrets[name]:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, "")


def normalizar_numero(numero: str) -> str:
    apenas_digitos = re.sub(r"\D+", "", numero or "")
    if apenas_digitos and not apenas_digitos.startswith("55") and len(apenas_digitos) in (10, 11):
        apenas_digitos = f"55{apenas_digitos}"
    return apenas_digitos


def _endpoint_envio() -> str:
    base_url = _config("WATIDY_API_URL").strip()
    endpoint = _config("WATIDY_SEND_PATH").strip()
    if not base_url:
        return ""
    if endpoint:
        return urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
    return base_url


def _headers() -> Dict[str, str]:
    token = _config("WATIDY_API_TOKEN")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def testar_conexao() -> Dict[str, str]:
    url = _endpoint_envio()
    token = _config("WATIDY_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure WATIDY_API_URL e WATIDY_API_TOKEN.")
    resp = requests.get(url, headers=_headers(), timeout=20)
    return {"status_code": str(resp.status_code), "resposta": resp.text[:300]}


def enviar_mensagem(numero: str, mensagem: str) -> Dict[str, str]:
    url = _endpoint_envio()
    token = _config("WATIDY_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure WATIDY_API_URL e WATIDY_API_TOKEN.")
    if not numero or not mensagem:
        raise ValueError("Número e mensagem são obrigatórios.")

    payload = {
        _config("WATIDY_NUMBER_FIELD") or "numero": normalizar_numero(numero),
        _config("WATIDY_MESSAGE_FIELD") or "mensagem": mensagem,
    }
    resp = requests.post(url, json=payload, headers=_headers(), timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Erro waTidy {resp.status_code}: {resp.text[:500]}")
    return resp.json() if resp.text else {"ok": "true"}
