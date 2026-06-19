import os
import re
from typing import Dict, Optional
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


def endpoint_envio() -> str:
    base_url = _config("WATIDY_API_URL").strip()
    endpoint = _config("WATIDY_SEND_PATH").strip()
    if not base_url:
        return ""
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    if endpoint:
        return urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
    return base_url


def _headers() -> Dict[str, str]:
    token = _config("WATIDY_API_TOKEN")
    auth_header = _config("WATIDY_AUTH_HEADER") or "Authorization"
    token_prefix = _config("WATIDY_TOKEN_PREFIX")
    if token_prefix == "":
        token_prefix = "Bearer"
    headers = {"Content-Type": "application/json"}
    if token:
        headers[auth_header] = f"{token_prefix} {token}".strip()
    return headers


def _resposta_curta(resp: requests.Response) -> str:
    content_type = resp.headers.get("Content-Type", "")
    texto = resp.text[:500]
    if "text/html" in content_type or texto.lstrip().startswith("<!DOCTYPE html>") or texto.lstrip().startswith("<html"):
        match = re.search(r"<pre>(.*?)</pre>", texto, re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
        return "O servidor retornou HTML em vez de JSON. Normalmente isso indica rota/endpoint incorreto."
    return texto


def _mensagem_erro(resp: requests.Response, url: str) -> str:
    detalhe = _resposta_curta(resp)
    if resp.status_code == 404 and "Cannot POST" in detalhe:
        return (
            f"Watidy respondeu 404: o endpoint de envio não existe ({detalhe}). "
            f"O app tentou enviar para: {url}. "
            "Confira em Configurações se WATIDY_API_URL é a URL base correta e se WATIDY_SEND_PATH é a rota exata de envio fornecida pelo Watidy."
        )
    return f"Erro Watidy {resp.status_code} ao enviar para {url}: {detalhe}"


def diagnostico_configuracao() -> Dict[str, str]:
    return {
        "url_de_envio_usada": endpoint_envio(),
        "campo_numero": _config("WATIDY_NUMBER_FIELD") or "numero",
        "campo_mensagem": _config("WATIDY_MESSAGE_FIELD") or "mensagem",
        "header_token": _config("WATIDY_AUTH_HEADER") or "Authorization",
        "prefixo_token": _config("WATIDY_TOKEN_PREFIX") or "Bearer",
    }


def testar_conexao() -> Dict[str, str]:
    url = endpoint_envio()
    token = _config("WATIDY_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure WATIDY_API_URL e WATIDY_API_TOKEN.")
    resp = requests.get(url, headers=_headers(), timeout=20)
    return {"status_code": str(resp.status_code), "resposta": resp.text[:300]}


def enviar_mensagem(numero: str, mensagem: str) -> Dict[str, str]:
    url = endpoint_envio()
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
        raise RuntimeError(_mensagem_erro(resp, url))
    try:
        return resp.json() if resp.text else {"ok": "true"}
    except ValueError:
        return {"ok": "true", "resposta": resp.text[:500]}
