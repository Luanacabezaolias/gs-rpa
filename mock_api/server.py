"""API SIMULADA do AccessFlow - so para desenvolver/testar a automacao.
Troque pela API real mudando ACCESSFLOW_API_URL no .env."""
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)
DB = {}


def iso(minutos_atras):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutos_atras)).isoformat()


def seed():
    DB["trechos"] = {
        "T1": {"id": "T1", "nome": "Entrada principal", "principal": True,
               "responsavel": {"nome": "Maria Teste", "email": "maria.teste@exemplo.com"},
               "supervisor": {"nome": "Sup Teste", "email": "supervisor.teste@exemplo.com"}},
        "T2": {"id": "T2", "nome": "Corredor da recepcao", "principal": False,
               "responsavel": {"nome": "Joao Teste", "email": "joao.teste@exemplo.com"},
               "supervisor": {"nome": "Sup Teste", "email": "supervisor.teste@exemplo.com"}},
        "T3": {"id": "T3", "nome": "Rampa lateral", "principal": False, "responsavel": None},
        "T4": {"id": "T4", "nome": "Sala 2", "principal": False,
               "responsavel": {"nome": "Ana Teste", "email": "ana-sem-arroba"}},
        "T5": {"id": "T5", "nome": "Hall do elevador", "principal": False,
               "responsavel": {"nome": "Rui Teste", "email": "rui.teste@exemplo.com"}},
    }
    DB["ocorrencias"] = [
        {"id": 1, "trecho_id": "T1", "tipo_objeto": "caixa", "origem": "visao", "status": "nova", "criada_em": iso(10)},
        {"id": 2, "trecho_id": "T1", "tipo_objeto": "caixa", "origem": "robo", "status": "nova", "criada_em": iso(5)},
        {"id": 3, "trecho_id": "T2", "tipo_objeto": "carrinho", "origem": "visao", "status": "nova", "criada_em": iso(3)},
        {"id": 4, "trecho_id": "T3", "tipo_objeto": "caixa", "origem": "visao", "status": "nova", "criada_em": iso(2)},
        {"id": 5, "trecho_id": "T4", "tipo_objeto": "caixa", "origem": "robo", "status": "nova", "criada_em": iso(1)},
        {"id": 6, "trecho_id": "T2", "tipo_objeto": "cadeira", "origem": "visao", "status": "notificada",
         "prioridade": "media", "criada_em": iso(250), "notificada_em": iso(200)},
        {"id": 7, "trecho_id": "T5", "tipo_objeto": "caixa", "origem": "visao", "status": "notificada",
         "prioridade": "media", "criada_em": iso(40), "notificada_em": iso(35)},
    ]
    DB["inspecoes"] = {"T5": {"trecho_id": "T5", "livre": True, "em": iso(5)}}


seed()


@app.get("/ocorrencias")
def listar():
    st = request.args.get("status")
    return jsonify([o for o in DB["ocorrencias"] if not st or o["status"] == st])


@app.post("/ocorrencias")
def criar():
    o = request.get_json()
    o.setdefault("id", max([x["id"] for x in DB["ocorrencias"]] + [0]) + 1)
    o.setdefault("status", "nova")
    o.setdefault("criada_em", iso(0))
    DB["ocorrencias"].append(o)
    return jsonify(o), 201


@app.patch("/ocorrencias/<int:oc_id>")
def atualizar(oc_id):
    for o in DB["ocorrencias"]:
        if o["id"] == oc_id:
            o.update(request.get_json())
            return jsonify(o)
    return jsonify({"erro": "nao encontrada"}), 404


@app.get("/trechos/<tid>")
def trecho(tid):
    t = DB["trechos"].get(tid)
    return (jsonify(t), 200) if t else (jsonify({"erro": "nao encontrado"}), 404)


@app.get("/inspecoes/ultima")
def inspecao():
    i = DB["inspecoes"].get(request.args.get("trecho_id"))
    return (jsonify(i), 200) if i else (jsonify({"erro": "sem inspecao"}), 404)


@app.post("/inspecoes")
def registrar_inspecao():
    i = request.get_json()
    i.setdefault("em", iso(0))
    DB["inspecoes"][i["trecho_id"]] = i
    return jsonify(i), 201


@app.post("/reset")
def reset():
    seed()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(port=5000)
