@echo off
rem Gera o 3-audio-aula.wav e o 4-video-aula.mp4 com a voz em portugues do Windows.
rem Nao fecha sozinho: se algo der errado, a mensagem fica na tela.
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY ( py -3 -c "import sys" >nul 2>nul && set "PY=py -3" )
if not defined PY for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
if not defined PY (
  echo  [ERRO] Python nao encontrado. Abra antes o publicar.bat da pasta do PRISMA ^(ele instala o Python^).
  goto :fim
)
%PY% -X utf8 montar_audio_video.py
:fim
echo.
echo  Pressione qualquer tecla para fechar.
pause >nul
