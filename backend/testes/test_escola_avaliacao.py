"""Escolas, avaliação dos alunos, feedbacks do professor e materiais tirados do painel pela família."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_api import Base, TestClient  # noqa: E402

try:
    from adaptador import api
except ImportError:  # pragma: no cover
    api = None


PLANO = {"plano": "escola", "periodo": "anual", "pagamento": "pix"}


@unittest.skipIf(TestClient is None, "fastapi/httpx não instalados")
class TestEscola(Base):
    def test_cadastro_pede_plano_e_mostra_assinatura_no_painel(self):
        c = self.cliente()
        r = c.post("/api/contas/escola", json={"nome": "Escola Y", "email": "y@e.br", "senha": "senha-da-escola",
                                                "codigo": "CODIGO-Y-2026"})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json()["detail"]["campo"], "plano")
        r = c.post("/api/contas/escola", json={"nome": "Escola Y", "email": "y@e.br", "senha": "senha-da-escola",
                                                "codigo": "CODIGO-Y-2026", "plano": "essencial", "periodo": "semestral",
                                                "pagamento": "cartao"})
        self.assertEqual(r.status_code, 201, r.text)
        a = c.get("/api/escola").json()["assinatura"]
        self.assertEqual((a["plano_nome"], a["valor"], a["pagamento_nome"]), ("Essencial", 4950, "Cartão de crédito"))

    def escola(self, codigo="CODIGO-PROF-2026", email="coord@escola.br"):
        c = self.cliente()
        r = c.post("/api/contas/escola", json={"nome": "Escola Municipal Teste", "email": email,
                                                "senha": "senha-da-escola", "codigo": codigo, **PLANO})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["destino"], "painel/escola.html")
        self.assertEqual(r.json()["assinatura"]["valor"], 21000)
        return c

    def test_professor_entra_com_codigo_da_escola_cadastrada(self):
        self.escola()
        c = self.cliente()
        r = c.post("/api/contas/professor", json={"nome": "Ana", "email": "ana@escola.br", "senha": "12345678",
                                                 "codigo_escola": "codigo prof 2026"})   # aceita espaço e minúscula
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(c.get("/api/eu").json()["escola"], "Escola Municipal Teste")

    def test_codigo_e_senha_separados_e_unicos(self):
        c = self.cliente()
        r = c.post("/api/contas/escola", json={"nome": "Escola X", "email": "x@e.br", "senha": "mesmo1234", "codigo": "mesmo1234", **PLANO})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["detail"]["campo"], "escola_codigo")
        self.escola()
        r = self.cliente().post("/api/contas/escola", json={"nome": "Outra", "email": "o@e.br", "senha": "senha-boa-1", "codigo": "CODIGO-PROF-2026", **PLANO})
        self.assertEqual(r.status_code, 409)

    def test_escola_entra_e_so_le(self):
        e = self.escola()
        prof = self.cliente()
        prof.post("/api/contas/professor", json={"nome": "Ana", "email": "ana@escola.br", "senha": "12345678", "codigo_escola": "CODIGO-PROF-2026"})
        t, _ = self.turma_com_aluno(prof)
        self.assertEqual(self.enviar_aula(prof, t["id"]).status_code, 201)
        # outro professor (código do .env) não aparece para a escola
        self.professor("outro@escola.br")
        dados = e.get("/api/escola").json()
        self.assertEqual([p["nome"] for p in dados["professores"]], ["Ana"])
        self.assertEqual(dados["professores"][0]["turmas"][0]["alunos"], ["Aluno A"])
        self.assertEqual(len(dados["materiais"]), 1)
        # entrar de novo com e-mail e senha
        c = self.cliente()
        r = c.post("/api/entrar", json={"perfil": "escola", "email": "coord@escola.br", "senha": "senha-da-escola"})
        self.assertEqual(r.status_code, 200, r.text)
        # a escola não cria turma nem envia material
        self.assertEqual(c.post("/api/turmas", json={"nome": "Nova"}).status_code, 403)
        self.assertEqual(c.get("/api/materiais").status_code, 403)


@unittest.skipIf(TestClient is None, "fastapi/httpx não instalados")
class TestAvaliacao(Base):
    def preparar(self):
        prof = self.professor()
        t, a = self.turma_com_aluno(prof)
        m = self.enviar_aula(prof, t["id"]).json()
        prof.post(f"/api/materiais/{m['id']}/aprovar")
        aluno = self.cliente()
        r = aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"], "figuras": a["figuras"]})
        self.assertEqual(r.status_code, 200, r.text)
        familia = self.cliente()
        familia.post("/api/entrar", json={"perfil": "familia", "codigo": a["codigo_familia"]})
        return prof, aluno, familia, m["id"]

    def test_aluno_avalia_e_professor_le(self):
        prof, aluno, _, mid = self.preparar()
        r = aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={"estrelas": 4, "sugestao": "Gostei do áudio."})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(aluno.get("/api/biblioteca").json()[0]["avaliacao"]["estrelas"], 4)
        f = prof.get("/api/feedbacks").json()[0]
        self.assertEqual((f["media"], f["total"]), (4.0, 1))
        self.assertEqual(f["avaliacoes"][0]["aluno"], "Aluno A")
        self.assertEqual(f["avaliacoes"][0]["sugestao"], "Gostei do áudio.")

    def test_so_sugestao_so_estrelas_ou_pular(self):
        _, aluno, _, mid = self.preparar()
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={"sugestao": "Mais exemplos."}).status_code, 200)
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={"estrelas": 5}).status_code, 200)
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={"pular": True}).status_code, 200)
        self.assertTrue(aluno.get("/api/biblioteca").json()[0]["avaliacao"]["pulou"])
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={}).status_code, 400)

    def test_limites(self):
        _, aluno, familia, mid = self.preparar()
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={"estrelas": 6}).status_code, 400)
        longa = " ".join(["palavra"] * 151)
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={"sugestao": longa}).status_code, 400)
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/avaliacao", json={"sugestao": " ".join(["palavra"] * 150)}).status_code, 200)
        # família não avalia
        self.assertEqual(familia.post(f"/api/biblioteca/{mid}/avaliacao", json={"estrelas": 3}).status_code, 403)

    def test_familia_tira_do_painel_so_do_proprio_aluno(self):
        prof, aluno, familia, mid = self.preparar()
        self.assertEqual(familia.post(f"/api/biblioteca/{mid}/ocultar", json={"ocultar": True}).status_code, 200)
        self.assertEqual(aluno.get("/api/biblioteca").json(), [])
        self.assertTrue(familia.get("/api/biblioteca").json()[0]["oculto"])
        # o material continua existindo para o professor e para a turma
        self.assertEqual(len(prof.get("/api/materiais").json()), 1)
        familia.post(f"/api/biblioteca/{mid}/ocultar", json={"ocultar": False})
        self.assertEqual(len(aluno.get("/api/biblioteca").json()), 1)
        # aluno não pode ocultar
        self.assertEqual(aluno.post(f"/api/biblioteca/{mid}/ocultar", json={}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
