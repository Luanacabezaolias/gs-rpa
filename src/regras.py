"""Regras de negocio puras (sem rede, sem I/O) - faceis de testar."""
from datetime import datetime, timedelta, timezone

JANELA_DUPLICIDADE_MIN = 60
PRAZO_MIN = {"alta": 30, "media": 120, "baixa": 480}
ABERTOS = {"nova", "notificada", "escalada"}
IDADE_ELEVA_PRIORIDADE_MIN = 30


def parse_dt(valor: str) -> datetime:
    dt = datetime.fromisoformat(valor)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def encontrar_duplicada(oc: dict, ocorrencias: list, janela_min: int = JANELA_DUPLICIDADE_MIN):
    """Retorna a ocorrencia ORIGINAL se `oc` for duplicada, senao None.

    Duplicada = mesmo trecho + mesmo tipo de objeto, original aberta e criada
    antes dela, dentro da janela de tempo.
    """
    criada = parse_dt(oc["criada_em"])
    for o in sorted(ocorrencias, key=lambda x: x["criada_em"]):
        if o["id"] == oc["id"] or o["status"] not in ABERTOS:
            continue
        if o["trecho_id"] != oc["trecho_id"] or o["tipo_objeto"] != oc["tipo_objeto"]:
            continue
        inicio = parse_dt(o["criada_em"])
        if inicio >= criada:
            continue
        if criada - inicio <= timedelta(minutes=janela_min):
            return o
    return None


def definir_prioridade(oc: dict, trecho: dict, agora: datetime) -> str:
    if trecho.get("principal"):
        return "alta"
    idade_min = (agora - parse_dt(oc["criada_em"])).total_seconds() / 60
    if idade_min >= IDADE_ELEVA_PRIORIDADE_MIN:
        return "alta"
    if oc["tipo_objeto"] in {"caixa", "carrinho"}:
        return "media"
    return "baixa"


def prazo_vencido(oc: dict, agora: datetime) -> bool:
    ref = oc.get("escalada_em") or oc.get("notificada_em")
    if not ref:
        return False
    prazo = PRAZO_MIN.get(oc.get("prioridade") or "baixa", PRAZO_MIN["baixa"])
    return agora - parse_dt(ref) >= timedelta(minutes=prazo)


def trecho_liberado_apos(oc: dict, inspecao) -> bool:
    """True se existe inspecao 'livre' feita DEPOIS da criacao da ocorrencia."""
    if not inspecao or not inspecao.get("livre"):
        return False
    return parse_dt(inspecao["em"]) > parse_dt(oc["criada_em"])
