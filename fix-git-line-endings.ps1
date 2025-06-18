# Script para corrigir problemas de line endings no Git
# Execute este script no PowerShell para resolver os avisos do Git

Write-Host "🔧 Corrigindo configurações de line endings do Git..." -ForegroundColor Yellow

# Configurar Git para tratar line endings automaticamente
Write-Host "1. Configurando autocrlf para input..." -ForegroundColor Cyan
git config core.autocrlf input

# Configurar safecrlf para avisar sobre problemas
Write-Host "2. Configurando safecrlf..." -ForegroundColor Cyan
git config core.safecrlf warn

# Remover arquivos do índice e readdicioná-los
Write-Host "3. Removendo arquivos do índice..." -ForegroundColor Cyan
git rm --cached -r .

# Reaplicar gitattributes
Write-Host "4. Reaplicando .gitattributes..." -ForegroundColor Cyan
git reset --hard

# Adicionar arquivos novamente
Write-Host "5. Adicionando arquivos com configurações corretas..." -ForegroundColor Cyan
git add .

Write-Host "✅ Configurações de line endings corrigidas!" -ForegroundColor Green
Write-Host "💡 Os avisos de CRLF/LF não devem mais aparecer." -ForegroundColor Blue

# Mostrar configurações atuais
Write-Host "`n📋 Configurações atuais do Git:" -ForegroundColor Magenta
git config --list | Select-String "core.autocrlf|core.safecrlf"