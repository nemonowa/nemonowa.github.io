:: The NEXUS Anchor - ���W�X�g���ɃJ�X�^��URL�X�L�[����o�^�i�����Ȃ��ŋN���j
@echo off
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ���s�F�Ǘ��Ҍ������K�v�ł��B
    pause
    exit /b
)

:: ���ϐ���ݒ�
set "NEXUS_PATH=C:\nexusource\source\source.exe"

:: ���W�X�g���L�[�̒ǉ�
reg add "HKEY_CLASSES_ROOT\nexus" /ve /d "URL:Nexus Protocol" /f
reg add "HKEY_CLASSES_ROOT\nexus" /v "URL Protocol" /d "" /f
reg add "HKEY_CLASSES_ROOT\nexus\shell" /f
reg add "HKEY_CLASSES_ROOT\nexus\shell\open" /f
reg add "HKEY_CLASSES_ROOT\nexus\shell\open\command" /ve /d "\"%NEXUS_PATH%\"" /f

:: �V���[�g�J�b�g�̔z�u
copy /Y "C:\nexusource\source\asset\url\nexusource.url" "%userprofile%\AppData\Roaming\.minecraft\versions\.Neo-Client"

copy /Y "C:\nexusource\source\asset\lnk\nexusource.lnk" "%USERPROFILE%\Desktop"

:: �g���q�̐ݒ�
assoc .neo=NeoFile
ftype NeoFile="C:\nexusource\source\source.exe" "%1"
reg add "HKEY_CLASSES_ROOT\NeoFile\DefaultIcon" /ve /t REG_SZ /d "C:\nexusource\source\asset\ico\neo.ico" /f

exit
