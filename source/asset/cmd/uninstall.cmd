:: The NEXUS Anchor - ���W�X�g���ɃJ�X�^��URL�X�L�[����o�^�i�����Ȃ��ŋN���j
@echo off
setlocal
color 0a

echo [=== UN-INSTALL PROTOCOL ===]
echo [Final confirmation] byebye-reserch:

choice /m "Are you sure you want to release the memory of this program? (Y/N)" /c YN
if %errorlevel% neq 1 (
    echo ���삪�L�����Z������܂����B
    exit /b
)

:: �t�H���_�̍폜
rd /s /q "C:\nexusource"
rd /s /q "%userprofile%\AppData\Roaming\.minecraft\versions\.Neo-Client"

echo See you NEXT time!
pause

