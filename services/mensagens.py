from typing import Any, Dict


def nome_cliente(cliente: Dict[str, Any]) -> str:
    return (
        cliente.get("nome_fantasia")
        or cliente.get("nome")
        or cliente.get("razao_social")
        or "cliente"
    )


def telefone_cliente(cliente: Dict[str, Any]) -> str:
    return cliente.get("celular") or cliente.get("telefone") or ""


def mensagem_cliente_padrao(cliente: Dict[str, Any]) -> str:
    nome = nome_cliente(cliente)
    return (
        f"Olá, {nome}! Tudo bem? Aqui é da Novaprint. "
        "Passando para acompanhar sua necessidade de materiais gráficos e ver como podemos ajudar."
    )


def mensagem_vendedora_padrao(cliente: Dict[str, Any], mensagem_cliente: str = "") -> str:
    nome = nome_cliente(cliente)
    telefone = telefone_cliente(cliente) or "sem telefone cadastrado"
    vendedor = cliente.get("vendedor") or "time comercial"
    resumo = f"\n\nMensagem sugerida/enviada ao cliente:\n{mensagem_cliente}" if mensagem_cliente else ""
    return (
        f"{vendedor}, atenção ao cliente {nome}. "
        f"Telefone: {telefone}. Faça o acompanhamento comercial no CRM.{resumo}"
    )
