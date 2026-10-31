@echo off
rem Liga o PRISMA e cria um link publico (https://...trycloudflare.com) para outras pessoas abrirem.
rem O link muda a cada vez e so funciona enquanto esta janela e o computador estiverem ligados.
rem Para desligar: feche esta janela e a janela "PRISMA servidor".
chcp 65001 >nul
cd /d "%~dp0backend"

set PY=python
where python >nul 2>nul || set PY=py
where cloudflared >nul 2>nul && (set CF=cloudflared) || (set CF="C:\Program Files (x86)\cloudflared\cloudflared.exe")

echo.
echo  1/2  Ligando o servidor do PRISMA (http://127.0.0.1:8000)...
start "PRISMA servidor" /min %PY% -m adaptador.api
timeout /t 5 >nul

echo  2/2  Criando o link publico. Procure abaixo a linha com  https://....trycloudflare.com
echo       e mande esse endereco para quem vai testar.
echo.
rem --protocol http2: funciona em redes que bloqueiam UDP/QUIC (comum em escola e universidade)
%CF% tunnel --no-autoupdate --protocol http2 --url http://127.0.0.1:8000
