@echo off
rem Corre los métodos de costeo vigentes para un periodo (sin programar). Deja un Excel con los resultados.
cd /d "%~dp0.."
set PY=
where py >nul 2>nul && set PY=py -3
if "%PY%"=="" set PY=python
set /p PER=Periodo (AAAA-MM): 
set /p EMP=Empresa: 
set /p PUB=¿Dejar los resultados en la bandeja para «Procesar carga»? (S/N): 
set OP=
if /I "%PUB%"=="S" set OP=--publicar
%PY% -m metodos.correr_metodos Sistema_Costos.xlsx %PER% %EMP% %OP%
if exist "Resultados_Metodos_%PER%_%EMP%.xlsx" start "" "Resultados_Metodos_%PER%_%EMP%.xlsx"
pause
