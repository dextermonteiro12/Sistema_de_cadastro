@echo off
REM Script de diagnóstico para verificar configuração de acesso externo

echo ============================================
echo   DIAGNOSTICO DE ACESSO EXTERNO
echo ============================================
echo.

echo [1] Verificando arquivo .env
echo ----------------------------------------
if exist "frontend-app\.env" (
    echo ✓ Arquivo .env encontrado
    type frontend-app\.env
) else (
    echo ✗ Arquivo .env NAO encontrado!
    echo   Crie o arquivo: frontend-app\.env
    goto :end
)
echo.

echo [2] Verificando processos rodando
echo ----------------------------------------
echo Frontend (porta 3000):
netstat -ano | findstr :3000
echo.
echo Backend (porta 5000):
netstat -ano | findstr :5000
echo.

echo [3] IP do servidor
echo ----------------------------------------
ipconfig | findstr "IPv4"
echo.

echo [4] Instrucoes para acesso externo
echo ----------------------------------------
echo 1. Confirme que o IP no .env esta correto
echo 2. Reinicie o sistema: npm run stop:all && npm run start:all
echo 3. Limpe o cache do navegador (Ctrl+Shift+Delete)
echo 4. Acesse de outra maquina: http://IP_SERVIDOR:3000
echo.
echo [5] Firewall - Execute como ADMINISTRADOR:
echo ----------------------------------------
echo New-NetFirewallRule -DisplayName "PLD Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
echo New-NetFirewallRule -DisplayName "PLD Backend" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
echo.

:end
echo ============================================
echo Pressione qualquer tecla para sair...
pause >nul
