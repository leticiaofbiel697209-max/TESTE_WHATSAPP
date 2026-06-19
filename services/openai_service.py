import os
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _config(name: str) -> str:
    try:
        if name in st.secrets and st.secrets[name]:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, "")


def _client():
    api_key = _config("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Configure OPENAI_API_KEY.")
    return OpenAI(api_key=api_key)


def testar_conexao():
    client = _client()
    client.models.list()
    return {"ok": True, "mensagem": "Conexão com OpenAI realizada."}


def _historico_suficiente(dados_cliente: Dict[str, Any]) -> bool:
    return len(dados_cliente.get("vendas") or []) >= 2


def _chat(prompt: str) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um analista comercial B2B da Novaprint. Use apenas os dados recebidos. Não invente histórico."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def analisar_cliente_com_ia(dados_cliente: Dict[str, Any]) -> str:
    if not _historico_suficiente(dados_cliente):
        return "Histórico insuficiente para sugerir recompra com segurança."
    return _chat(f"Analise este cliente com base somente nos dados reais abaixo:\n{dados_cliente}")


def sugerir_produto_recompra(dados_cliente: Dict[str, Any]) -> str:
    if not _historico_suficiente(dados_cliente):
        return "Histórico insuficiente para sugerir recompra com segurança."
    return _chat(f"Sugira recompra com produto, motivo e prioridade usando somente estes dados reais:\n{dados_cliente}")


def gerar_mensagem_whatsapp(cliente: Dict[str, Any], contexto: Dict[str, Any]) -> str:
    if len(contexto.get("vendas") or []) < 2:
        return "Histórico insuficiente para sugerir recompra com segurança."
    return _chat(f"Gere uma mensagem curta de WhatsApp para este cliente, sem inventar dados. Cliente: {cliente}. Contexto real: {contexto}")
