:: The NEXUS Anchor - ���W�X�g���ɃJ�X�^��URL�X�L�[����o�^�i�����Ȃ��ŋN���j
@echo off

:: �g���q�̐ݒ�
assoc .neo=NeoFile
ftype NeoFile="C:\nexusource\source\source.exe" "%1"
reg add "HKEY_CLASSES_ROOT\NeoFile\DefaultIcon" /ve /t REG_SZ /d "C:\nexusource\source\asset\ico\neo.ico" /f

pause
