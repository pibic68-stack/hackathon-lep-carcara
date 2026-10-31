"""Testes da API (precisam de fastapi e httpx: pip install -r requirements.txt)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from fastapi.testclient import TestClient
    from adaptador import api, cache
except ImportError:  # pragma: no cover
    TestClient = None
try:
    import pymupdf
except ImportError:
    pymupdf = None

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"


@unittest.skipIf(TestClient is None, "fastapi/httpx não instalados")
class TestAPI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self._antigos = (api.SAIDA, api.ENVIOS, cache.PASTA)
        api.SAIDA, api.ENVIOS, cache.PASTA = base / "saida", base / "envios", base / "cache"
        self.c = TestClient(api.app)

    def tearDown(self):
        api.SAIDA, api.ENVIOS, cache.PASTA = self._antigos
        self.tmp.cleanup()

    def _enviar_aula(self, perfil=None):
        dados = {"perfil": json.dumps(perfil)} if perfil else {}
        with open(EXEMPLOS / "aula-ciclo-da-agua.txt", "rb") as f:
            return self.c.post("/api/adaptar", files={"arquivo": ("aula.txt", f, "text/plain")}, data=dados)

    def test_saude(self):
        r = self.c.get("/api/saude").json()
        self.assertTrue(r["ok"])
        self.assertIn(".pdf", r["formatos"])

    def test_ciclo_completo_rascunho_aprova_biblioteca(self):
        r = self._enviar_aula({"aluno": "Aluno Fictício A", "necessidades": ["baixa_visao"]})
        self.assertEqual(r.status_code, 201, r.text)
        m = r.json()
        self.assertEqual(m["estado"], "rascunho")
        self.assertTrue(m["pode_publicar"])
        self.assertEqual(m["versoes"]["ampliada"]["status"], "gerada")
        id_ = m["id"]

        # rascunho: professor vê, aluno não
        self.assertEqual(self.c.get(m["versoes"]["universal"]["url"]).status_code, 200)
        self.assertEqual(self.c.get("/api/biblioteca").json(), [])
        self.assertEqual(self.c.get(f"/api/biblioteca/{id_}/universal.html").status_code, 404)

        # aprovação publica
        self.assertEqual(self.c.post(f"/api/materiais/{id_}/aprovar").json()["estado"], "publicado")
        lib = self.c.get("/api/biblioteca").json()
        self.assertEqual([i["id"] for i in lib], [id_])
        pagina = self.c.get(lib[0]["versoes"]["universal"]["url"])
        self.assertEqual(pagina.status_code, 200)
        self.assertIn("azul (■)", pagina.text)

    def test_formato_invalido_e_perfil_invalido(self):
        r = self.c.post("/api/adaptar", files={"arquivo": ("x.exe", b"MZ", "application/octet-stream")})
        self.assertEqual(r.status_code, 415)
        with open(EXEMPLOS / "aula-ciclo-da-agua.txt", "rb") as f:
            r = self.c.post("/api/adaptar", files={"arquivo": ("a.txt", f)}, data={"perfil": "[1,2]"})
        self.assertEqual(r.status_code, 422)

    def test_arquivo_corrompido_da_erro_amigavel(self):
        r = self.c.post("/api/adaptar", files={"arquivo": ("quebrado.pdf", b"isto nao e um pdf", "application/pdf")})
        self.assertIn(r.status_code, (422, 501))
        self.assertEqual(list((api.SAIDA).glob("*")) if api.SAIDA.exists() else [], [])

    def test_nao_vaza_arquivos_internos_nem_sai_da_pasta(self):
        id_ = self._enviar_aula().json()["id"]
        for caminho in ("estado.json", "revisao.json", "..%2f..%2fenvios", "%2e%2e/%2e%2e/estado.json"):
            self.assertEqual(self.c.get(f"/api/previa/{id_}/{caminho}").status_code, 404, caminho)
        self.assertEqual(self.c.get("/api/materiais/../../etc").status_code, 404)
        self.assertEqual(self.c.get("/api/materiais/naoexiste123").status_code, 404)

    @unittest.skipIf(pymupdf is None, "pymupdf não instalado")
    def test_imagem_sem_descricao_bloqueia_ate_professor_descrever(self):
        pdf = pymupdf.open()
        pg = pdf.new_page()
        pg.insert_text((72, 80), "Aula com figura", fontsize=24)
        pg.insert_textbox(pymupdf.Rect(72, 120, 520, 200), "O sol aquece a água do mar.", fontsize=11)
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 90), False)
        pix.clear_with(200)
        pg.insert_image(pymupdf.Rect(72, 220, 192, 310), stream=pix.tobytes("png"))
        corpo = pdf.tobytes()

        m = self.c.post("/api/adaptar", files={"arquivo": ("figura.pdf", corpo, "application/pdf")}).json()
        id_ = m["id"]
        self.assertFalse(m["pode_publicar"])
        self.assertEqual(m["imagens_sem_descricao"], ["imagens/img-001.png"])
        r = self.c.post(f"/api/materiais/{id_}/aprovar")
        self.assertEqual(r.status_code, 409)

        m = self.c.post(f"/api/materiais/{id_}/descricoes",
                        json={"imagens": {"imagens/img-001.png": "Sol sobre o mar"}}).json()
        self.assertTrue(m["pode_publicar"])
        self.assertEqual(m["imagens_sem_descricao"], [])
        self.assertEqual(self.c.post(f"/api/materiais/{id_}/aprovar").status_code, 200)
        img = self.c.get(f"/api/biblioteca/{id_}/imagens/img-001.png")
        self.assertEqual(img.status_code, 200)
        html = self.c.get(f"/api/biblioteca/{id_}/universal.html").text
        self.assertIn('alt="Sol sobre o mar"', html)

        # depois de publicado, não dá para mexer
        r = self.c.post(f"/api/materiais/{id_}/descricoes", json={"imagens": {"imagens/img-001.png": "Outro"}})
        self.assertEqual(r.status_code, 409)


if __name__ == "__main__":
    unittest.main()
