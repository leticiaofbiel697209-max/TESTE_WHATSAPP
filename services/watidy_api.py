import os
from typing import Dict

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


def testar_conexao() -> Dict[str, str]:
    url = _config("WATIDY_API_URL")
    token = _config("WATIDY_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure WATIDY_API_URL e WATIDY_API_TOKEN.")
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    return {"status_code": str(resp.status_code), "resposta": resp.text[:300]}


def enviar_mensagem(numero: str, mensagem: str) -> Dict[str, str]:
    url = _config("WATIDY_API_URL")
    token = _config("WATIDY_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure WATIDY_API_URL e WATIDY_API_TOKEN.")
    if not numero or not mensagem:
        raise ValueError("Número e mensagem são obrigatórios.")
    payload = {"numero": numero, "mensagem": mensagem}
    resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Erro waTidy {resp.status_code}: {resp.text[:500]}")
    return resp.json() if resp.text else {"ok": "true"}
