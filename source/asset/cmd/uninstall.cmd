:: The NEXUS Anchor - レジストリにカスタムURLスキームを登録（引数なしで起動）
@echo off
setlocal
color 0a

echo [=== UN-INSTALL PROTOCOL ===]
echo [Final confirmation] byebye-reserch:

choice /m "Are you sure you want to release the memory of this program? (Y/N)" /c YN
if %errorlevel% neq 1 (
    echo 操作がキャンセルされました。
    exit /b
)

:: フォルダの削除
rd /s /q "C:\nexusource"
rd /s /q "%userprofile%\AppData\Roaming\.minecraft\versions\.Neo-Client"

echo See you NEXT time!
pause

