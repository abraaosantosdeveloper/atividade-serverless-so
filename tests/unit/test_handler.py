import json
from hello_world import app


def _evento(body):
    return {"body": json.dumps(body) if body is not None else None}


def test_gera_guia():
    resp = app.lambda_handler(_evento({"requisicaoId": "R-001", "hospital": "H-Recife",
                                       "bolsas": ["O-NEG-0142"]}), None)
    assert resp["statusCode"] == 201
    corpo = json.loads(resp["body"])
    assert corpo["guia"] == "G-R-001"
    assert corpo["bolsas"] == ["O-NEG-0142"]


def test_sem_requisicao_id_retorna_400():
    resp = app.lambda_handler(_evento({"hospital": "H-Recife"}), None)
    assert resp["statusCode"] == 400


def test_contador_cresce_no_mesmo_processo():
    a = json.loads(app.lambda_handler(_evento({"requisicaoId": "A"}), None)["body"])
    b = json.loads(app.lambda_handler(_evento({"requisicaoId": "B"}), None)["body"])
    assert b["invocacaoNesteAmbiente"] == a["invocacaoNesteAmbiente"] + 1


def test_aceita_body_em_base64():
    import base64
    body = base64.b64encode(json.dumps({"requisicaoId": "R-9"}).encode()).decode()
    resp = app.lambda_handler({"body": body, "isBase64Encoded": True}, None)
    assert json.loads(resp["body"])["guia"] == "G-R-9"
