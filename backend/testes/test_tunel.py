"""O link público só aparece quando funciona (cloudflared simulado por um script Python)."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptador import tunel


class TestTunel(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def falso(self, linhas):
        script = self.dir / "cf.py"
        script.write_text("import time\n" + "".join(f"print({l!r}, flush=True)\n" for l in linhas)
                          + "time.sleep(30)\n", encoding="utf-8")
        return [sys.executable, str(script)]

    def test_link_so_sai_depois_de_conectado_e_respondendo(self):
        cmd = self.falso(["INF Requesting new quick Tunnel on trycloudflare.com...",
                          "INF |  https://pato-azul-teste.trycloudflare.com  |",
                          "INF Registered tunnel connection connIndex=0"])
        with mock.patch.object(tunel, "responde", return_value=True):
            t = tunel.ligar("cloudflared", espera=10, comando=cmd)
        self.assertIsNotNone(t)
        self.assertEqual(t.url, "https://pato-azul-teste.trycloudflare.com")
        t.parar()

    def test_rede_bloqueada_nao_mostra_link(self):
        cmd = self.falso(["INF |  https://pato-azul-teste.trycloudflare.com  |",
                          "ERR Failed to dial a quic connection"])
        with mock.patch.object(tunel, "responde", return_value=True):
            self.assertIsNone(tunel.ligar("cloudflared", espera=1.5, comando=cmd))


if __name__ == "__main__":
    unittest.main()
