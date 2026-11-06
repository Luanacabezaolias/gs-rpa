"""AccessFlow - Automacao RPA: detectar -> registrar -> ACIONAR -> RESOLVER -> VERIFICAR."""
import argparse
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from . import regras
from .api_client import ApiClient, ApiIndisponivel
from .logger_setup import configurar_log
from .notificador import Notificador, NotificacaoFalhou, mascarar_email


def agora_utc():
    return datetime.now(timezone.utc)


class Automacao:
    def __init__(self, client, notificador, log, agora_fn=agora_utc):
        self.api, self.notif, self.log, self.agora = client, notificador, log, agora_fn

    @staticmethod
    def _resumo_vazio():
        return {"processadas": 0, "notificadas": 0, "duplicadas": 0, "escaladas": 0,
                "resolvidas": 0, "falhas": 0, "sem_responsavel": 0}

    # ---------- Etapa 1: ocorrencias novas ----------
    def processar_novas(self, resumo):
        todas = self.api.listar_ocorrencias()
        novas = sorted([o for o in todas if o["status"] == "nova"], key=lambda o: o["criada_em"])
        self.log.info(f"Etapa novas: {len(novas)} ocorrencia(s) para processar")
        for oc in novas:  # REPETICAO em lote
            resumo["processadas"] += 1
            try:
                self._tratar_nova(oc, todas, resumo)
            except NotificacaoFalhou as e:
                resumo["falhas"] += 1
                self.log.error(f"oc={oc['id']} notificacao falhou ({e}); segue 'nova' para nova tentativa")
            except ApiIndisponivel:
                raise
            except Exception as e:  # um item ruim nao derruba o lote
                resumo["falhas"] += 1
                self.log.error(f"oc={oc['id']} erro inesperado: {type(e).__name__}: {e}")

    def _tratar_nova(self, oc, todas, resumo):
        agora = self.agora()
        # DECISAO 1: duplicada?
        original = regras.encontrar_duplicada(oc, todas)
        if original:
            novo = self.api.atualizar_ocorrencia(oc["id"], {
                "status": "duplicada", "ocorrencia_origem_id": original["id"]})
            oc.update(novo)
            resumo["duplicadas"] += 1
            self.log.info(f"oc={oc['id']} DUPLICADA de oc={original['id']} (trecho={oc['trecho_id']})")
            return
        trecho = self.api.obter_trecho(oc["trecho_id"])
        resp = trecho.get("responsavel")
        # DECISAO 2: tem responsavel?
        if not resp or not resp.get("email"):
            resumo["sem_responsavel"] += 1
            self.log.warning(f"oc={oc['id']} trecho={trecho['id']} SEM RESPONSAVEL cadastrado; requer acao manual")
            return
        # DECISAO 3: prioridade
        prioridade = regras.definir_prioridade(oc, trecho, agora)
        self.notif.enviar(
            resp["email"],
            f"[AccessFlow] Obstrucao em '{trecho['nome']}' (prioridade {prioridade})",
            f"Objeto detectado: {oc['tipo_objeto']}.\nTrecho: {trecho['nome']}.\n"
            f"Prazo para resolver: {regras.PRAZO_MIN[prioridade]} min.")
        novo = self.api.atualizar_ocorrencia(oc["id"], {
            "status": "notificada", "prioridade": prioridade, "notificada_em": agora.isoformat()})
        oc.update(novo)
        resumo["notificadas"] += 1
        self.log.info(f"oc={oc['id']} NOTIFICADA prioridade={prioridade} para={mascarar_email(resp['email'])}")

    # ---------- Etapa 2: acompanhar notificadas ----------
    def processar_pendentes(self, resumo):
        todas = self.api.listar_ocorrencias()
        pend = [o for o in todas if o["status"] in ("notificada", "escalada")]
        self.log.info(f"Etapa pendentes: {len(pend)} ocorrencia(s) em acompanhamento")
        for oc in pend:  # REPETICAO
            try:
                agora = self.agora()
                # DECISAO 4: nova inspecao mostra trecho livre? -> fecha
                if regras.trecho_liberado_apos(oc, self.api.ultima_inspecao(oc["trecho_id"])):
                    self.api.atualizar_ocorrencia(oc["id"], {
                        "status": "resolvida", "resolvida_em": agora.isoformat()})
                    resumo["resolvidas"] += 1
                    self.log.info(f"oc={oc['id']} RESOLVIDA (inspecao confirmou trecho livre)")
                    continue
                # DECISAO 5: prazo vencido? -> reenvia e escala
                if regras.prazo_vencido(oc, agora):
                    self._escalar(oc, agora, resumo)
            except NotificacaoFalhou as e:
                resumo["falhas"] += 1
                self.log.error(f"oc={oc['id']} reenvio falhou ({e}); tentara na proxima rodada")
            except ApiIndisponivel:
                raise
            except Exception as e:
                resumo["falhas"] += 1
                self.log.error(f"oc={oc['id']} erro inesperado: {type(e).__name__}: {e}")

    def _escalar(self, oc, agora, resumo):
        trecho = self.api.obter_trecho(oc["trecho_id"])
        destinos = [d for d in (trecho.get("responsavel"), trecho.get("supervisor")) if d and d.get("email")]
        if not destinos:
            resumo["sem_responsavel"] += 1
            self.log.warning(f"oc={oc['id']} prazo vencido mas sem destinatario para escalar")
            return
        for d in destinos:
            self.notif.enviar(
                d["email"], f"[AccessFlow] URGENTE: prazo vencido em '{trecho['nome']}'",
                f"A obstrucao ({oc['tipo_objeto']}) segue sem resolucao alem do prazo.")
        self.api.atualizar_ocorrencia(oc["id"], {"status": "escalada", "escalada_em": agora.isoformat()})
        resumo["escaladas"] += 1
        self.log.info(f"oc={oc['id']} ESCALADA para {len(destinos)} destinatario(s)")

    # ---------- Execucao completa ----------
    def executar(self):
        resumo = self._resumo_vazio()
        self.log.info("=== Inicio da rodada ===")
        try:
            self.processar_novas(resumo)
            self.processar_pendentes(resumo)
        except ApiIndisponivel as e:
            resumo["erro_fatal"] = str(e)
            self.log.error(f"ABORTADO: {e}")
        self.log.info(f"=== Fim da rodada: {resumo} ===")
        return resumo


def main(argv=None):
    load_dotenv()
    p = argparse.ArgumentParser(description="AccessFlow RPA")
    p.add_argument("--loop", type=int, metavar="SEGUNDOS", help="repete a cada N segundos")
    args = p.parse_args(argv)
    log = configurar_log()
    robo = Automacao(ApiClient(log=log), Notificador(), log)
    if not args.loop:
        return 1 if "erro_fatal" in robo.executar() else 0
    while True:
        robo.executar()
        time.sleep(args.loop)


if __name__ == "__main__":
    sys.exit(main())
