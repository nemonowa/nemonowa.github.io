:: The NEXUS Anchor - レジストリにカスタムURLスキームを登録（引数なしで起動）
@echo off
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 失敗：管理者権限が必要です。
    pause
    exit /b
)

:: 環境変数を設定
set "NEXUS_PATH=C:\nexusource\source\source.exe"

:: レジストリキーの追加
reg add "HKEY_CLASSES_ROOT\nexus" /ve /d "URL:Nexus Protocol" /f
reg add "HKEY_CLASSES_ROOT\nexus" /v "URL Protocol" /d "" /f
reg add "HKEY_CLASSES_ROOT\nexus\shell" /f
reg add "HKEY_CLASSES_ROOT\nexus\shell\open" /f
reg add "HKEY_CLASSES_ROOT\nexus\shell\open\command" /ve /d "\"%NEXUS_PATH%\"" /f

:: ショートカットの配置
copy /Y "C:\nexusource\source\asset\url\nexusource.url" "%userprofile%\AppData\Roaming\.minecraft\versions\.Neo-Client"

copy /Y "C:\nexusource\source\asset\lnk\nexusource.lnk" "%USERPROFILE%\Desktop"

:: 拡張子の設定
assoc .neo=NeoFile
ftype NeoFile="C:\nexusource\source\source.exe" "%1"
reg add "HKEY_CLASSES_ROOT\NeoFile\DefaultIcon" /ve /t REG_SZ /d "C:\nexusource\source\asset\ico\neo.ico" /f

exit
