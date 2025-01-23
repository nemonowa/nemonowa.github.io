:: The NEXUS Anchor - レジストリにカスタムURLスキームを登録（引数なしで起動）
@echo off

:: 拡張子の設定
assoc .neo=NeoFile
ftype NeoFile="C:\nexusource\source\source.exe" "%1"
reg add "HKEY_CLASSES_ROOT\NeoFile\DefaultIcon" /ve /t REG_SZ /d "C:\nexusource\source\asset\ico\neo.ico" /f

pause
