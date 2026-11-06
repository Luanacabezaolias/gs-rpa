from datetime import datetime, timedelta, timezone

from src import regras

AGORA = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


def iso(min_atras):
    return (AGORA - timedelta(minutes=min_atras)).isoformat()


def oc(id, trecho="T1", tipo="caixa", status="nova", min_atras=0, **extra):
    return {"id": id, "trecho_id": trecho, "tipo_objeto": tipo, "status": status,
            "criada_em": iso(min_atras), **extra}


def test_duplicada_mesmo_trecho_tipo_dentro_da_janela():
    original, nova = oc(1, min_atras=10), oc(2, min_atras=5)
    assert regras.encontrar_duplicada(nova, [original, nova])["id"] == 1


def test_nao_duplicada_se_tipo_diferente():
    assert regras.encontrar_duplicada(oc(2, tipo="carrinho"), [oc(1, min_atras=5), oc(2)]) is None


def test_nao_duplicada_fora_da_janela():
    assert regras.encontrar_duplicada(oc(2), [oc(1, min_atras=120), oc(2)]) is None


def test_original_resolvida_nao_conta_como_duplicidade():
    assert regras.encontrar_duplicada(oc(2), [oc(1, status="resolvida", min_atras=5), oc(2)]) is None


def test_prioridade_trecho_principal_e_alta():
    assert regras.definir_prioridade(oc(1), {"principal": True}, AGORA) == "alta"


def test_prioridade_media_para_caixa_e_baixa_para_outros():
    assert regras.definir_prioridade(oc(1, tipo="caixa"), {"principal": False}, AGORA) == "media"
    assert regras.definir_prioridade(oc(1, tipo="vaso"), {"principal": False}, AGORA) == "baixa"


def test_prioridade_sobe_para_alta_com_idade():
    assert regras.definir_prioridade(oc(1, tipo="vaso", min_atras=45), {"principal": False}, AGORA) == "alta"


def test_prazo_vencido_e_nao_vencido():
    venc = oc(1, status="notificada", prioridade="alta", notificada_em=iso(31))
    ok = oc(2, status="notificada", prioridade="alta", notificada_em=iso(10))
    assert regras.prazo_vencido(venc, AGORA) is True
    assert regras.prazo_vencido(ok, AGORA) is False


def test_trecho_liberado_somente_com_inspecao_livre_posterior():
    o = oc(1, min_atras=30)
    assert regras.trecho_liberado_apos(o, {"livre": True, "em": iso(5)}) is True
    assert regras.trecho_liberado_apos(o, {"livre": True, "em": iso(60)}) is False  # inspecao antiga
    assert regras.trecho_liberado_apos(o, {"livre": False, "em": iso(5)}) is False
    assert regras.trecho_liberado_apos(o, None) is False
