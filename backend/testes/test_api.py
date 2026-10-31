"""Testes da API com contas (precisam de fastapi e httpx: pip install -r requirements.txt)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from fastapi.testclient import TestClient
    from adaptador import api, cache, contas
except ImportError:  # pragma: no cover
    TestClient = None
try:
    import pymupdf
except ImportError:
    pymupdf = None

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"
CODIGO = "ESCOLA-TESTE-123"


@unittest.skipIf(TestClient is None, "fastapi/httpx não instalados")
class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self._antigos = (api.SAIDA, api.ENVIOS, cache.PASTA, contas.BANCO)
        api.SAIDA, api.ENVIOS, cache.PASTA, contas.BANCO = base / "saida", base / "envios", base / "cache", base / "t.db"
        api._envios_recentes.clear()
        # os testes nunca usam a IA de verdade nem o .env de quem roda
        self._patches = [mock.patch.object(api.ia, "obter_provedor", return_value=None),
                         mock.patch.dict(os.environ, {"PRISMA_CODIGO_ESCOLA": CODIGO})]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        api.SAIDA, api.ENVIOS, cache.PASTA, contas.BANCO = self._antigos
        self.tmp.cleanup()

    def cliente(self):
        return TestClient(api.app, headers={"X-Prisma": "1"})

    def professor(self, email="prof@escola.br"):
        c = self.cliente()
        r = c.post("/api/contas/professor", json={"nome": "Prof. Teste", "email": email,
                                                 "senha": "senha-forte-1", "codigo_escola": CODIGO})
        self.assertEqual(r.status_code, 201, r.text)
        return c

    def turma_com_aluno(self, c, necessidades=("baixa_visao",)):
        t = c.post("/api/turmas", json={"nome": "5º ano A"}).json()
        a = c.post(f"/api/turmas/{t['id']}/alunos",
                   json={"apelido": "Aluno A", "necessidades": list(necessidades), "preferencias": ["audio"]}).json()
        return t, a

    def enviar_aula(self, c, turma_id):
        with open(EXEMPLOS / "aula-ciclo-da-agua.txt", "rb") as f:
            return c.post("/api/adaptar", files={"arquivo": ("aula.txt", f, "text/plain")}, data={"turma_id": str(turma_id)})


class TestContas(Base):
    def test_cadastro_exige_codigo_da_escola(self):
        c = self.cliente()
        r = c.post("/api/contas/professor", json={"nome": "Xis", "email": "x@e.br", "senha": "12345678", "codigo_escola": "errado"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["detail"]["campo"], "codigo_escola")

    def test_cadastro_fechado_sem_codigo_configurado(self):
        with mock.patch.dict(os.environ, {"PRISMA_CODIGO_ESCOLA": ""}), mock.patch.object(api.ia, "_env", return_value={}):
            r = self.cliente().post("/api/contas/professor",
                                    json={"nome": "Xis", "email": "x@e.br", "senha": "12345678", "codigo_escola": "x"})
        self.assertEqual(r.status_code, 403)
        self.assertIn("fechado", r.json()["detail"]["erro"])

    def test_cadastro_login_e_sair(self):
        c = self.professor()
        self.assertEqual(c.get("/api/eu").json()["perfil"], "professor")
        self.assertEqual(c.post("/api/contas/professor", json={"nome": "Ypsilon", "email": "prof@escola.br", "senha": "outra-senha",
                                                               "codigo_escola": CODIGO}).status_code, 409)
        c.post("/api/sair")
        self.assertIsNone(c.get("/api/eu").json())          # saiu: ninguém logado
        r = c.post("/api/entrar", json={"perfil": "professor", "email": "PROF@escola.br", "senha": "senha-forte-1"})
        self.assertEqual(r.json()["destino"], "painel/professor.html")
        self.assertEqual(c.get("/api/eu").json()["nome"], "Prof. Teste")

    def test_senha_curta_e_email_invalido(self):
        c = self.cliente()
        r = c.post("/api/contas/professor", json={"nome": "Xis", "email": "x@e.br", "senha": "123", "codigo_escola": CODIGO})
        self.assertEqual(r.json()["detail"]["campo"], "senha_nova")
        r = c.post("/api/contas/professor", json={"nome": "Xis", "email": "nao-e-email", "senha": "12345678", "codigo_escola": CODIGO})
        self.assertEqual(r.json()["detail"]["campo"], "email_novo")

    def test_senha_errada_e_limite_de_tentativas(self):
        self.professor()
        c = self.cliente()
        for _ in range(contas.MAX_FALHAS):
            r = c.post("/api/entrar", json={"perfil": "professor", "email": "prof@escola.br", "senha": "errada"})
            self.assertEqual(r.status_code, 401)
        r = c.post("/api/entrar", json={"perfil": "professor", "email": "prof@escola.br", "senha": "senha-forte-1"})
        self.assertEqual(r.status_code, 429)    # bloqueado mesmo com a senha certa

    def test_pedido_sem_cabecalho_e_recusado(self):
        c = TestClient(api.app)
        r = c.post("/api/entrar", json={"perfil": "professor", "email": "a@b.c", "senha": "x"})
        self.assertEqual(r.status_code, 403)

    def test_senha_guardada_com_hash(self):
        self.professor()
        with contas.conexao() as con:
            guardada = con.execute("SELECT senha FROM professores").fetchone()[0]
        self.assertNotIn("senha-forte-1", guardada)


class TestTurmas(Base):
    def test_aluno_e_familia_entram_com_os_codigos(self):
        c = self.professor()
        t, a = self.turma_com_aluno(c)
        self.assertEqual(len(a["figuras"]), 3)
        aluno = self.cliente()
        r = aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"].lower(), "figuras": a["figuras"]})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(aluno.get("/api/eu").json()["nome"], "Aluno A")
        familia = self.cliente()
        r = familia.post("/api/entrar", json={"perfil": "familia", "codigo": a["codigo_familia"].replace("-", " ")})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(familia.get("/api/eu").json()["perfil"], "familia")

    def test_figurinhas_erradas_e_forca_bruta(self):
        c = self.professor()
        t, a = self.turma_com_aluno(c)
        erradas = [f for f in contas.FIGURAS if f not in a["figuras"]][:3]
        aluno = self.cliente()
        for _ in range(contas.MAX_FALHAS):
            self.assertEqual(aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"], "figuras": erradas}).status_code, 401)
        r = aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"], "figuras": a["figuras"]})
        self.assertEqual(r.status_code, 429)

    def test_necessidade_fora_da_lista_e_recusada(self):
        c = self.professor()
        t = c.post("/api/turmas", json={"nome": "5º B"}).json()
        r = c.post(f"/api/turmas/{t['id']}/alunos", json={"apelido": "Aluno B", "necessidades": ["autismo"]})
        self.assertEqual(r.status_code, 400)    # P10.2: nada de diagnóstico

    def test_professor_nao_mexe_na_turma_do_outro(self):
        c1 = self.professor("a@escola.br")
        t, a = self.turma_com_aluno(c1)
        c2 = self.professor("b@escola.br")
        self.assertEqual(c2.get("/api/turmas").json(), [])
        self.assertEqual(c2.post(f"/api/turmas/{t['id']}/alunos", json={"apelido": "Intruso"}).status_code, 404)
        self.assertEqual(c2.delete(f"/api/alunos/{a['id']}").status_code, 404)

    def test_aluno_nao_acessa_area_do_professor(self):
        c = self.professor()
        t, a = self.turma_com_aluno(c)
        aluno = self.cliente()
        aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"], "figuras": a["figuras"]})
        self.assertEqual(aluno.get("/api/turmas").status_code, 403)
        self.assertEqual(aluno.get("/api/materiais").status_code, 403)

    def test_remover_aluno_derruba_a_sessao_dele(self):
        c = self.professor()
        t, a = self.turma_com_aluno(c)
        aluno = self.cliente()
        aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"], "figuras": a["figuras"]})
        c.delete(f"/api/alunos/{a['id']}")
        self.assertIsNone(aluno.get("/api/eu").json())


class TestMateriais(Base):
    def test_sem_login_nada_funciona(self):
        c = self.cliente()
        self.assertEqual(c.get("/api/materiais").status_code, 401)
        self.assertEqual(c.get("/api/biblioteca").status_code, 401)
        self.assertEqual(self.enviar_aula(c, 1).status_code, 401)

    def test_ciclo_completo_com_turma(self):
        c = self.professor()
        t, a = self.turma_com_aluno(c)
        r = self.enviar_aula(c, t["id"])
        self.assertEqual(r.status_code, 201, r.text)
        m = r.json()
        self.assertEqual(m["estado"], "rascunho")
        self.assertEqual(m["turma"], "5º ano A")
        # versões saem pelas necessidades da turma: baixa visão -> ampliada; áudio -> ouvir
        self.assertEqual(m["versoes"]["ampliada"]["status"], "gerada")
        self.assertEqual(m["versoes"]["audio"]["status"], "gerada")
        self.assertEqual(c.get(m["versoes"]["universal"]["url"]).status_code, 200)

        aluno = self.cliente()
        aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"], "figuras": a["figuras"]})
        self.assertEqual(aluno.get("/api/biblioteca").json(), [])
        self.assertEqual(aluno.get(f"/api/biblioteca/{m['id']}/universal.html").status_code, 404)
        self.assertEqual(aluno.get(m["versoes"]["universal"]["url"]).status_code, 403)   # prévia é do professor

        self.assertEqual(c.post(f"/api/materiais/{m['id']}/aprovar").json()["estado"], "publicado")
        lib = aluno.get("/api/biblioteca").json()
        self.assertEqual([i["id"] for i in lib], [m["id"]])
        self.assertTrue(lib[0]["versoes"]["ampliada"]["recomendada"])
        self.assertFalse(lib[0]["versoes"]["universal"]["recomendada"])
        pagina = aluno.get(lib[0]["versoes"]["universal"]["url"])
        self.assertEqual(pagina.status_code, 200)
        self.assertNotIn("(■)", pagina.text)          # palavra de cor sem cor de verdade não ganha legenda

    def test_outra_turma_e_outro_professor_nao_veem(self):
        c = self.professor("a@escola.br")
        t, a = self.turma_com_aluno(c)
        m = self.enviar_aula(c, t["id"]).json()
        c.post(f"/api/materiais/{m['id']}/aprovar")

        t2, a2 = self.turma_com_aluno(c)          # outra turma do mesmo professor
        outro = self.cliente()
        outro.post("/api/entrar", json={"perfil": "aluno", "turma": t2["codigo"], "figuras": a2["figuras"]})
        self.assertEqual(outro.get("/api/biblioteca").json(), [])
        self.assertEqual(outro.get(f"/api/biblioteca/{m['id']}/universal.html").status_code, 404)

        c2 = self.professor("b@escola.br")
        self.assertEqual(c2.get("/api/materiais").json(), [])
        self.assertEqual(c2.get(f"/api/materiais/{m['id']}").status_code, 404)
        self.assertEqual(c2.post(f"/api/materiais/{m['id']}/aprovar").status_code, 404)
        self.assertEqual(c2.get(f"/api/previa/{m['id']}/universal.html").status_code, 404)

    def test_formato_invalido_e_turma_alheia(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        r = c.post("/api/adaptar", files={"arquivo": ("x.exe", b"MZ")}, data={"turma_id": str(t["id"])})
        self.assertEqual(r.status_code, 415)
        self.assertEqual(self.enviar_aula(c, 9999).status_code, 404)

    def test_arquivo_corrompido_nao_deixa_lixo(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        r = c.post("/api/adaptar", files={"arquivo": ("quebrado.pdf", b"isto nao e um pdf", "application/pdf")},
                   data={"turma_id": str(t["id"])})
        self.assertIn(r.status_code, (422, 501))
        self.assertEqual(c.get("/api/materiais").json(), [])

    def test_limite_de_envios_por_hora(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        with mock.patch.object(api, "ENVIOS_POR_HORA", 2):
            self.assertEqual(self.enviar_aula(c, t["id"]).status_code, 201)
            self.assertEqual(self.enviar_aula(c, t["id"]).status_code, 201)
            self.assertEqual(self.enviar_aula(c, t["id"]).status_code, 429)

    def test_nao_vaza_arquivos_internos(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        id_ = self.enviar_aula(c, t["id"]).json()["id"]
        for caminho in ("estado.json", "revisao.json", "..%2f..%2fenvios", "%2e%2e/%2e%2e/estado.json"):
            self.assertEqual(c.get(f"/api/previa/{id_}/{caminho}").status_code, 404, caminho)

    def test_apagar_material(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        id_ = self.enviar_aula(c, t["id"]).json()["id"]
        self.assertEqual(c.delete(f"/api/materiais/{id_}").status_code, 200)
        self.assertEqual(c.get(f"/api/materiais/{id_}").status_code, 404)

    @unittest.skipIf(pymupdf is None, "pymupdf não instalado")
    def test_imagem_sem_descricao_bloqueia_ate_professor_descrever(self):
        pdf = pymupdf.open()
        pg = pdf.new_page()
        pg.insert_text((72, 80), "Aula com figura", fontsize=24)
        pg.insert_textbox(pymupdf.Rect(72, 120, 520, 200), "O sol aquece a água do mar.", fontsize=11)
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 90), False)
        pix.clear_with(200)
        pg.insert_image(pymupdf.Rect(72, 220, 192, 310), stream=pix.tobytes("png"))

        c = self.professor()
        t, a = self.turma_com_aluno(c)
        m = c.post("/api/adaptar", files={"arquivo": ("figura.pdf", pdf.tobytes(), "application/pdf")},
                   data={"turma_id": str(t["id"])}).json()
        self.assertFalse(m["pode_publicar"])
        self.assertEqual(m["imagens_sem_descricao"], ["imagens/img-001.png"])
        self.assertEqual(c.post(f"/api/materiais/{m['id']}/aprovar").status_code, 409)

        m = c.post(f"/api/materiais/{m['id']}/descricoes", json={"imagens": {"imagens/img-001.png": "Sol sobre o mar"}}).json()
        self.assertTrue(m["pode_publicar"])
        self.assertEqual(c.post(f"/api/materiais/{m['id']}/aprovar").status_code, 200)

        aluno = self.cliente()
        aluno.post("/api/entrar", json={"perfil": "aluno", "turma": t["codigo"], "figuras": a["figuras"]})
        self.assertEqual(aluno.get(f"/api/biblioteca/{m['id']}/imagens/img-001.png").status_code, 200)
        self.assertIn('alt="Sol sobre o mar"', aluno.get(f"/api/biblioteca/{m['id']}/universal.html").text)
        r = c.post(f"/api/materiais/{m['id']}/descricoes", json={"imagens": {"imagens/img-001.png": "Outro"}})
        self.assertEqual(r.status_code, 409)


if __name__ == "__main__":
    unittest.main()
