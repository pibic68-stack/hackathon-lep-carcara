@echo off
rem Passa os materiais de teste pela IA ANTES da apresentacao e guarda as respostas.
rem Na hora, o mesmo arquivo sai em segundos, mesmo com o Google ocupado. Pode levar ate 20 minutos.
setlocal
chcp 65001 >nul
cd /d "%~dp0..\backend"
set "PY="
python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY ( py -3 -c "import sys" >nul 2>nul && set "PY=py -3" )
if not defined PY for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
if not defined PY (
  echo  [ERRO] Python nao encontrado. Abra antes o publicar.bat da pasta do PRISMA ^(ele instala o Python^).
  goto :fim
)
%PY% -X utf8 -m adaptador.preparar_demo "%~dp0."
:fim
echo.
echo  Pressione qualquer tecla para fechar.
pause >nul
