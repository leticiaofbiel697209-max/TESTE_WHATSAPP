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


def endpoint_envio() -> str:
    base_url = _config("WATIDY_API_URL").strip()
    token = _config("WATIDY_API_TOKEN").strip()
    endpoint_config = _config("WATIDY_SEND_PATH").strip()
    if endpoint_config:
        endpoint = endpoint_config
    elif "/api/enviar-texto" in base_url:
        endpoint = "{token}"
    else:
        endpoint = "/api/enviar-texto/{token}"
    if not base_url:
        return ""
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        url = endpoint
    else:
        url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
    if "{token}" in url:
        return url.replace("{token}", token)
    token_no_caminho = _config("WATIDY_TOKEN_IN_PATH").lower() not in ("0", "false", "nao", "não", "no")
    if token_no_caminho and token and not url.rstrip("/").endswith(token):
        return f"{url.rstrip('/')}/{token}"
    return url


def _headers() -> Dict[str, str]:
    token = _config("WATIDY_API_TOKEN")
    auth_header = _config("WATIDY_AUTH_HEADER") or "Authorization"
    token_prefix = _config("WATIDY_TOKEN_PREFIX")
    if token_prefix == "":
        token_prefix = "Bearer"
    headers = {"Content-Type": "application/json"}
    token_no_caminho = _config("WATIDY_TOKEN_IN_PATH").lower() not in ("0", "false", "nao", "não", "no")
    if token and not token_no_caminho:
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
        "campo_numero": _config("WATIDY_NUMBER_FIELD") or "phone",
        "campo_mensagem": _config("WATIDY_MESSAGE_FIELD") or "message",
        "header_token": _config("WATIDY_AUTH_HEADER") or "Authorization",
        "prefixo_token": _config("WATIDY_TOKEN_PREFIX") or "Bearer",
        "token_no_caminho": _config("WATIDY_TOKEN_IN_PATH") or "1",
    }


def testar_conexao() -> Dict[str, str]:
    url = endpoint_envio()
    token = _config("WATIDY_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure WATIDY_API_URL e WATIDY_API_TOKEN.")
    return {"ok": "true", "mensagem": "Configuração carregada. Use o envio de teste para validar a entrega.", "url_de_envio_usada": url}


def enviar_mensagem(numero: str, mensagem: str) -> Dict[str, str]:
    url = endpoint_envio()
    token = _config("WATIDY_API_TOKEN")
    if not url or not token:
        raise RuntimeError("Configure WATIDY_API_URL e WATIDY_API_TOKEN.")
    if not numero or not mensagem:
        raise ValueError("Número e mensagem são obrigatórios.")

    numero_normalizado = normalizar_numero(numero)
    number_field = _config("WATIDY_NUMBER_FIELD") or "phone"
    message_field = _config("WATIDY_MESSAGE_FIELD") or "message"
    payload = {"phone": numero_normalizado, "message": mensagem}
    payload[number_field] = numero_normalizado
    payload[message_field] = mensagem
    resp = requests.post(url, json=payload, headers=_headers(), timeout=30)
    if not resp.ok:
        raise RuntimeError(_mensagem_erro(resp, url))
    try:
        return resp.json() if resp.text else {"ok": "true"}
    except ValueError:
        return {"ok": "true", "resposta": resp.text[:500]}
