import json
from collections import Counter
from datetime import date, datetime
from statistics import mean
from typing import Dict, List, Optional


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(str(value)[:19], fmt).date()
        except ValueError:
            continue
    return None


def calcular_ticket_medio(vendas: List[dict]) -> float:
    valores = [float(v.get("valor_total") or 0) for v in vendas if float(v.get("valor_total") or 0) > 0]
    return round(mean(valores), 2) if valores else 0.0


def calcular_ultima_compra(vendas: List[dict]) -> Optional[date]:
    datas = [_parse_date(v.get("data")) for v in vendas]
    datas = [d for d in datas if d]
    return max(datas) if datas else None


def calcular_dias_sem_comprar(ultima_compra) -> Optional[int]:
    if not ultima_compra:
        return None
    return (date.today() - ultima_compra).days


def calcular_frequencia_compra(vendas: List[dict]) -> Optional[float]:
    datas = sorted([_parse_date(v.get("data")) for v in vendas if _parse_date(v.get("data"))])
    if len(datas) < 2:
        return None
    intervalos = [(datas[i] - datas[i - 1]).days for i in range(1, len(datas)) if (datas[i] - datas[i - 1]).days >= 0]
    return round(mean(intervalos), 1) if intervalos else None


def _produtos(vendas: List[dict]) -> List[str]:
    nomes = []
    for venda in vendas:
        raw = venda.get("produtos_json") or "[]"
        try:
            produtos = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            produtos = []
        for item in produtos or []:
            if isinstance(item, dict):
                nome = item.get("nome") or item.get("descricao") or item.get("produto") or item.get("titulo")
                if nome:
                    nomes.append(str(nome))
    return nomes


def produtos_mais_comprados(vendas: List[dict]) -> List[Dict[str, int]]:
    return [{"produto": p, "quantidade": q} for p, q in Counter(_produtos(vendas)).most_common(10)]


def sugerir_recompra_regra(vendas: List[dict]) -> Dict[str, str]:
    if len(vendas) < 2:
        return {
            "produto_sugerido": None,
            "motivo": "Histórico insuficiente para sugerir recompra com segurança.",
        }
    ultima = calcular_ultima_compra(vendas)
    dias = calcular_dias_sem_comprar(ultima)
    freq = calcular_frequencia_compra(vendas)
    ticket = calcular_ticket_medio(vendas)
    mais = produtos_mais_comprados(vendas)
    produto_mais_comprado = mais[0]["produto"] if mais else None
    vendas_ordenadas = sorted(vendas, key=lambda v: _parse_date(v.get("data")) or date.min, reverse=True)
    produto_recente = None
    if vendas_ordenadas:
        recentes = _produtos([vendas_ordenadas[0]])
        produto_recente = recentes[0] if recentes else None
    produto = produto_mais_comprado or produto_recente
    if not produto or freq is None or dias is None:
        return {
            "produto_sugerido": None,
            "motivo": "Histórico insuficiente para sugerir recompra com segurança.",
        }
    atraso = dias - freq
    status = "dentro do ciclo" if atraso < 0 else f"aproximadamente {round(atraso)} dias acima do ciclo médio"
    return {
        "produto_sugerido": produto,
        "motivo": f"Produto mais comprado/recente: {produto}. Intervalo médio: {freq} dias. Dias desde a última compra: {dias}. Ticket médio: R$ {ticket:,.2f}. Cliente está {status}.",
    }
