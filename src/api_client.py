import os
import time
import requests


class ApiIndisponivel(Exception):
    """API fora do ar depois de todas as tentativas."""


class ApiClient:
    def __init__(self, base_url=None, token=None, tentativas=3, espera_s=1.0, log=None):
        self.base = (base_url or os.getenv("ACCESSFLOW_API_URL", "http://localhost:5000")).rstrip("/")
        self.s = requests.Session()
        token = token or os.getenv("ACCESSFLOW_API_TOKEN", "")
        if token:
            self.s.headers["Authorization"] = f"Bearer {token}"
        self.tentativas, self.espera_s, self.log = tentativas, espera_s, log

    def _req(self, metodo, caminho, **kw):
        ultimo = None
        for i in range(1, self.tentativas + 1):
            try:
                r = self.s.request(metodo, self.base + caminho, timeout=10, **kw)
                if r.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {r.status_code}")
                return r
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
                ultimo = e
                if self.log:
                    self.log.warning(f"API tentativa {i}/{self.tentativas} falhou: {type(e).__name__}")
                if i < self.tentativas:
                    time.sleep(self.espera_s * i)
        raise ApiIndisponivel(f"API indisponivel apos {self.tentativas} tentativas") from ultimo

    def listar_ocorrencias(self, status=None):
        params = {"status": status} if status else None
        r = self._req("GET", "/ocorrencias", params=params)
        r.raise_for_status()
        return r.json()

    def atualizar_ocorrencia(self, oc_id, campos):
        r = self._req("PATCH", f"/ocorrencias/{oc_id}", json=campos)
        r.raise_for_status()
        return r.json()

    def obter_trecho(self, trecho_id):
        r = self._req("GET", f"/trechos/{trecho_id}")
        r.raise_for_status()
        return r.json()

    def ultima_inspecao(self, trecho_id):
        r = self._req("GET", "/inspecoes/ultima", params={"trecho_id": trecho_id})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
