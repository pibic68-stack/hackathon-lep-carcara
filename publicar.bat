@echo off
rem ============================================================
rem  PRISMA - liga o site e cria o link publico (trycloudflare.com)
rem  Basta dar dois cliques. A janela NUNCA fecha sozinha:
rem  se algo der errado, ela mostra o motivo e espera uma tecla.
rem ============================================================
setlocal EnableExtensions
title PRISMA - publicar
chcp 65001 >nul
cd /d "%~dp0"

rem --- 0. avisos de pasta errada (rodar de dentro do zip) ---
if not exist "backend\adaptador\api.py" (
  echo.
  echo  [ERRO] Nao achei a pasta "backend" ao lado deste arquivo.
  echo         Se voce abriu o .bat de dentro do .zip, extraia o zip inteiro
  echo         ^(clique direito, Extrair tudo^) e abra o publicar.bat da pasta extraida.
  goto :fim
)

rem --- 1. Python ---
set "PY="
python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY ( py -3 -c "import sys" >nul 2>nul && set "PY=py -3" )
if not defined PY (
  echo.
  echo  Python nao encontrado. Instalando sozinho pelo Windows ^(1 a 3 minutos, so uma vez^)...
  winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
  for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
)
if not defined PY (
  echo.
  echo  [ERRO] Nao consegui instalar o Python sozinho.
  echo         Instale em https://www.python.org/downloads/ e MARQUE a caixa
  echo         "Add python.exe to PATH" na primeira tela. Depois abra este arquivo de novo.
  goto :fim
)
echo  Python: %PY%

rem --- 2. bibliotecas (instala sozinho se faltar) ---
%PY% -c "import fastapi, uvicorn, multipart" >nul 2>nul
if errorlevel 1 (
  echo.
  echo  Instalando as bibliotecas do PRISMA ^(so na primeira vez, 1 a 3 minutos^)...
  %PY% -m pip install --disable-pip-version-check fastapi uvicorn python-multipart pymupdf python-pptx httpx
  if errorlevel 1 (
    echo.
    echo  [ERRO] A instalacao falhou. Confira a internet e tente de novo.
    goto :fim
  )
)

rem --- 2b. chave da IA (Gemini). Fica so em backend\.env, que nunca vai para o GitHub ---
set "TEM_CHAVE="
if exist "backend\.env" findstr /r /c:"^GEMINI_API_KEY=..*" "backend\.env" >nul 2>nul && set "TEM_CHAVE=1"
if not defined TEM_CHAVE (
  echo.
  echo  ------------------------------------------------------------
  echo   A IA ^(Leitura Facil, descricao de imagens, transcricao de video^)
  echo   precisa da chave gratuita do Gemini. So e pedida uma vez.
  echo   Pegue em https://aistudio.google.com/apikey  ^(botao "Create API key"^)
  echo   Cole aqui com o botao direito do mouse e aperte Enter.
  echo   Para seguir sem IA, so aperte Enter.
  echo  ------------------------------------------------------------
  set "CHAVE="
  set /p "CHAVE=  Chave do Gemini: "
)
if not defined TEM_CHAVE if defined CHAVE (
  if not exist "backend\.env" copy /y "backend\.env.exemplo" "backend\.env" >nul
  findstr /v /r /c:"^GEMINI_API_KEY=" "backend\.env" > "backend\.env.tmp"
  >>"backend\.env.tmp" echo GEMINI_API_KEY=%CHAVE%
  move /y "backend\.env.tmp" "backend\.env" >nul
  echo  Chave salva em backend\.env ^(so neste computador^).
)
if not defined TEM_CHAVE if not defined CHAVE echo  Seguindo sem IA. Para ligar depois, abra este arquivo de novo.

rem --- 3. cloudflared (baixa sozinho se faltar) ---
set "CF="
where cloudflared >nul 2>nul && set "CF=cloudflared"
if not defined CF if exist "%ProgramFiles(x86)%\cloudflared\cloudflared.exe" set "CF=%ProgramFiles(x86)%\cloudflared\cloudflared.exe"
if not defined CF if exist "%~dp0ferramentas\cloudflared.exe" set "CF=%~dp0ferramentas\cloudflared.exe"
if not defined CF (
  echo.
  echo  Baixando o cloudflared ^(cria o link publico, ~40 MB, so uma vez^)...
  if not exist "%~dp0ferramentas" mkdir "%~dp0ferramentas"
  curl.exe -L --fail -o "%~dp0ferramentas\cloudflared.exe" "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
  if exist "%~dp0ferramentas\cloudflared.exe" set "CF=%~dp0ferramentas\cloudflared.exe"
)

rem --- 4. servidor (janela propria, que fica aberta para mostrar erros) ---
echo.
echo  Ligando o servidor do PRISMA...
start "PRISMA servidor (nao feche)" /min cmd /k "cd /d "%~dp0backend" && %PY% -X utf8 -m adaptador.api"

set /a N=0
:espera
set /a N+=1
curl.exe -s -o nul http://127.0.0.1:8000/ && goto :no_ar
if %N% GEQ 40 (
  echo.
  echo  [ERRO] O servidor nao respondeu em 40 segundos.
  echo         Abra a janela "PRISMA servidor" na barra de tarefas: o motivo esta escrito nela.
  echo         ^(Porta 8000 ocupada? Feche outras janelas do PRISMA e tente de novo.^)
  goto :fim
)
timeout /t 1 /nobreak >nul
goto :espera

:no_ar
echo  Servidor no ar: http://127.0.0.1:8000
start "" http://127.0.0.1:8000/

if not defined CF (
  echo.
  echo  [AVISO] Nao consegui o cloudflared, entao NAO ha link publico.
  echo          O site funciona so neste computador, em http://127.0.0.1:8000
  goto :fim
)

echo.
echo  ------------------------------------------------------------
echo   Criando o link publico. Procure abaixo a linha com
echo      https://alguma-coisa.trycloudflare.com
echo   e mande esse endereco para quem vai testar.
echo   Para desligar: feche esta janela e a janela "PRISMA servidor".
echo  ------------------------------------------------------------
echo.
"%CF%" tunnel --no-autoupdate --protocol http2 --url http://127.0.0.1:8000

:fim
echo.
echo  Pressione qualquer tecla para fechar esta janela.
pause >nul
endlocal
