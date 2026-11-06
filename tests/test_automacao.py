import logging
from datetime import datetime, timedelta, timezone

import pytest

from src.api_client import ApiIndisponivel
from src.automacao import Automacao
from src.notificador import NotificacaoFalhou, mascarar_email

AGORA = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


def iso(min_atras):
    return (AGORA - timedelta(minutes=min_atras)).isoformat()


class FakeClient:
    def __init__(self, ocorrencias, trechos, inspecoes=None, fora_do_ar=False):
        self.ocs = ocorrencias
        self.trechos, self.insp, self.fora = trechos, inspecoes or {}, fora_do_ar

    def _checa(self):
        if self.fora:
            raise ApiIndisponivel("fora do ar")

    def listar_ocorrencias(self, status=None):
        self._checa()
        return [dict(o) for o in self.ocs]

    def atualizar_ocorrencia(self, oc_id, campos):
        self._checa()
        for o in self.ocs:
            if o["id"] == oc_id:
                o.update(campos)
                return dict(o)

    def obter_trecho(self, tid):
        self._checa()
        return self.trechos[tid]

    def ultima_inspecao(self, tid):
        self._checa()
        return self.insp.get(tid)


class FakeNotif:
    def __init__(self, falha=False):
        self.enviados, self.falha = [], falha

    def enviar(self, dest, assunto, corpo):
        if self.falha:
            raise NotificacaoFalhou("smtp fora")
        self.enviados.append((dest, assunto))


TRECHOS = {
    "T1": {"id": "T1", "nome": "Entrada", "principal": True,
           "responsavel": {"email": "a@x.com"}, "supervisor": {"email": "s@x.com"}},
    "T2": {"id": "T2", "nome": "Rampa", "principal": False, "responsavel": None},
}


def oc(id, trecho="T1", tipo="caixa", status="nova", min_atras=5, **extra):
    return {"id": id, "trecho_id": trecho, "tipo_objeto": tipo, "status": status,
            "criada_em": iso(min_atras), **extra}


def robo(client, notif):
    return Automacao(client, notif, logging.getLogger("teste"), agora_fn=lambda: AGORA)


# ---------- SUCESSO ----------
def test_sucesso_nova_ocorrencia_e_notificada():
    c, n = FakeClient([oc(1)], TRECHOS), FakeNotif()
    r = robo(c, n).executar()
    assert r["notificadas"] == 1 and len(n.enviados) == 1
    assert c.ocs[0]["status"] == "notificada" and c.ocs[0]["prioridade"] == "alta"


# ---------- DECISAO ----------
def test_decisao_duplicada_nao_notifica_e_aponta_origem():
    c, n = FakeClient([oc(1, min_atras=10), oc(2, min_atras=5)], TRECHOS), FakeNotif()
    r = robo(c, n).executar()
    assert r["notificadas"] == 1 and r["duplicadas"] == 1
    assert c.ocs[1]["status"] == "duplicada" and c.ocs[1]["ocorrencia_origem_id"] == 1


def test_decisao_inspecao_livre_fecha_ocorrencia():
    c = FakeClient([oc(1, status="notificada", min_atras=40, prioridade="alta", notificada_em=iso(35))],
                   TRECHOS, inspecoes={"T1": {"livre": True, "em": iso(2)}})
    r = robo(c, FakeNotif()).executar()
    assert r["resolvidas"] == 1 and c.ocs[0]["status"] == "resolvida"


def test_decisao_prazo_vencido_escala_para_responsavel_e_supervisor():
    c, n = FakeClient([oc(1, status="notificada", min_atras=90, prioridade="alta", notificada_em=iso(45))],
                      TRECHOS), FakeNotif()
    r = robo(c, n).executar()
    assert r["escaladas"] == 1 and len(n.enviados) == 2 and c.ocs[0]["status"] == "escalada"


def test_decisao_prazo_nao_vencido_nao_faz_nada():
    c, n = FakeClient([oc(1, status="notificada", prioridade="alta", notificada_em=iso(5))], TRECHOS), FakeNotif()
    r = robo(c, n).executar()
    assert r["escaladas"] == 0 and n.enviados == [] and c.ocs[0]["status"] == "notificada"


# ---------- FALHA ----------
def test_falha_sem_responsavel_mantem_nova_e_registra():
    c, n = FakeClient([oc(1, trecho="T2")], TRECHOS), FakeNotif()
    r = robo(c, n).executar()
    assert r["sem_responsavel"] == 1 and c.ocs[0]["status"] == "nova" and n.enviados == []


def test_falha_notificacao_nao_muda_status_e_nao_derruba_lote():
    c, n = FakeClient([oc(1), oc(2, trecho="T2")], TRECHOS), FakeNotif(falha=True)
    r = robo(c, n).executar()
    assert r["falhas"] == 1 and r["sem_responsavel"] == 1
    assert c.ocs[0]["status"] == "nova"  # tentara de novo na proxima rodada


def test_falha_api_fora_do_ar_aborta_com_erro_registrado():
    r = robo(FakeClient([], TRECHOS, fora_do_ar=True), FakeNotif()).executar()
    assert "erro_fatal" in r


def test_idempotencia_segunda_rodada_nao_renotifica():
    c, n = FakeClient([oc(1)], TRECHOS), FakeNotif()
    a = robo(c, n)
    a.executar()
    a.executar()
    assert len(n.enviados) == 1


def test_mascara_de_email():
    assert mascarar_email("maria.teste@exemplo.com") == "m***@exemplo.com"
    assert mascarar_email("invalido") == "***"
