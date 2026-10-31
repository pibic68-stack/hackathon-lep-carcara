"""Símbolos nas imagens coloridas (P1.1), transcrição pela IA e o botão "Gerar as versões de novo"."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptador import cache, leitores, renderizador
from adaptador.modelo import Bloco, Documento
from adaptador.simbolos_imagem import marcar_cores

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    Image = None

try:
    from test_api import Base
except Exception:  # pragma: no cover
    Base = None


def figura(caminho: Path) -> None:
    """Fundo cinza claro, um retângulo verde grande, um sol amarelo pequeno e uma faixa vermelha fina na borda."""
    im = Image.new("RGB", (600, 400), (235, 235, 240))
    d = ImageDraw.Draw(im)
    d.rectangle([60, 150, 400, 360], fill=(40, 170, 50))
    d.ellipse([470, 40, 540, 110], fill=(250, 220, 20))
    d.rectangle([0, 0, 600, 3], fill=(220, 30, 30))             # enfeite de borda
    d.rectangle([420, 250, 560, 300], fill=(255, 255, 255))     # caixa de texto branca
    im.save(caminho)


@unittest.skipIf(Image is None, "Pillow não instalado")
class TestSimbolosNaImagem(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_marca_regioes_grandes_e_pequenas_e_ignora_borda(self):
        figura(self.dir / "f.png")
        cores = marcar_cores(self.dir / "f.png", self.dir / "f-cores.png")
        self.assertEqual(cores, ["verde", "amarelo"])           # maior área primeiro; a faixa vermelha fica de fora
        self.assertTrue((self.dir / "f-cores.png").exists())
        im = Image.open(self.dir / "f-cores.png").convert("RGB")
        b = im.tobytes()
        pretos = sum(1 for i in range(0, len(b), 3) if b[i:i + 3] == b"\x00\x00\x00")
        self.assertGreater(pretos, 300)                          # os símbolos foram desenhados

    def test_imagem_sem_cor_nao_gera_copia(self):
        Image.new("RGB", (300, 200), (200, 200, 200)).save(self.dir / "cinza.png")
        self.assertEqual(marcar_cores(self.dir / "cinza.png", self.dir / "x.png"), [])
        self.assertFalse((self.dir / "x.png").exists())

    def test_versao_mostra_imagem_com_simbolos_legenda_e_original(self):
        figura(self.dir / "f.png")
        marcar_cores(self.dir / "f.png", self.dir / "f-cores.png")
        doc = Documento("Teste", [Bloco("imagem", arquivo="f.png", alt="Árvore e sol.", colorida=True,
                                        arquivo_cores="f-cores.png", cores_imagem=["verde", "amarelo"])])
        partes = self._render(doc)
        self.assertIn('src="f-cores.png"', partes)
        self.assertIn("● verde", partes.replace('<span class="simbolo" aria-hidden="true">', "").replace("</span>", ""))
        self.assertIn("Ver a imagem sem os símbolos", partes)
        self.assertIn("círculo sobre o verde", partes)          # a versão Ouvir explica os símbolos

    def _render(self, doc):
        return renderizador.para_html(doc, "padrao", pasta_imagens=self.dir, pasta_saida=self.dir / "out", audio=True)


class Falso:
    nome = "falso"

    def __init__(self, resposta):
        self.resposta, self.chamadas = resposta, []

    def gerar(self, sistema, usuario, imagem=None):
        self.chamadas.append(imagem)
        return self.resposta


class TestTranscricaoPelaIA(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self._antigo = cache.PASTA
        cache.PASTA = self.dir / "cache"
        (self.dir / "aula.mp3").write_bytes(b"ID3 audio de mentira")
        # finge que o faster-whisper não está instalado
        self._sem_whisper = mock.patch.dict(sys.modules, {"faster_whisper": None})
        self._sem_whisper.start()

    def tearDown(self):
        self._sem_whisper.stop()
        cache.PASTA = self._antigo
        self.tmp.cleanup()

    def test_sem_whisper_a_ia_transcreve(self):
        ia = Falso(json.dumps({"paragrafos": ["A água evapora.", "Depois vira chuva."], "na_tela": []}))
        doc = leitores.ler(self.dir / "aula.mp3", self.dir, ia=ia)
        self.assertEqual([b.texto for b in doc.blocos], ["A água evapora.", "Depois vira chuva."])
        dados, mime = ia.chamadas[0]
        self.assertEqual(mime, "audio/mp3")
        self.assertIn("transcrição feita pela IA", doc.pendencias[0])

    def test_video_traz_o_que_aparece_na_tela(self):
        (self.dir / "aula.mp4").write_bytes(b"video de mentira")
        ia = Falso(json.dumps({"paragrafos": ["Olá, turma."], "na_tela": ["Slide: Ciclo da água"]}))
        doc = leitores.ler(self.dir / "aula.mp4", self.dir, ia=ia)
        self.assertEqual(doc.blocos[1].texto, "O que aparece na tela")
        self.assertEqual(doc.blocos[2].itens, ["Slide: Ciclo da água"])

    def test_sem_whisper_e_sem_ia_explica_o_que_fazer(self):
        with self.assertRaises(RuntimeError) as erro:
            leitores.ler(self.dir / "aula.mp3", self.dir)
        self.assertIn("chave do Gemini", str(erro.exception))

    def test_sem_fala(self):
        with self.assertRaises(RuntimeError):
            leitores.ler(self.dir / "aula.mp3", self.dir, ia=Falso('{"paragrafos": [], "na_tela": []}'))


@unittest.skipIf(Base is None, "fastapi/httpx não instalados")
class TestRefazer(Base if Base else unittest.TestCase):
    def test_refazer_gera_de_novo_quando_a_ia_liga(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c, necessidades=("leitura_facil",))
        m = self.enviar_aula(c, t["id"]).json()
        pendentes = [k for k, v in m["versoes"].items() if v["status"] == "pendente_ia"]
        self.assertTrue(pendentes)
        r = c.post(f"/api/materiais/{m['id']}/refazer")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["id"], m["id"])

    def test_refazer_nao_mexe_em_publicado(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        m = self.enviar_aula(c, t["id"]).json()
        c.post(f"/api/materiais/{m['id']}/aprovar")
        self.assertEqual(c.post(f"/api/materiais/{m['id']}/refazer").status_code, 409)


if __name__ == "__main__":
    unittest.main()
