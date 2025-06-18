@echo off
echo ====================================================
echo SOLUCAO DEFINITIVA PARA LINE ENDINGS - GIT WINDOWS
echo ====================================================

echo.
echo 1. Configurando Git para tratar line endings...
git config core.autocrlf input
git config core.safecrlf false
git config core.eol lf

echo.
echo 2. Removendo todos os arquivos do indice...
git rm --cached -r .

echo.
echo 3. Reajustando working directory...
git reset --hard HEAD

echo.
echo 4. Adicionando arquivos com configuracao correta...
git add .

echo.
echo 5. Verificando status...
git status

echo.
echo ====================================================
echo CONCLUIDO! Agora git add . deve funcionar sem avisos
echo ====================================================
pause