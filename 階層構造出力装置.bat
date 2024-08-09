@echo off
:: 出力ファイルのパスを設定
set OUTPUT_FILE="%USERPROFILE%\Desktop\tree_output.txt"

:: 出力ファイルが既に存在する場合は削除
if exist %OUTPUT_FILE% del %OUTPUT_FILE%

:: treeコマンドの結果を出力ファイルに書き込む
echo ディレクトリツリーの出力 >> %OUTPUT_FILE%
tree /F >> %OUTPUT_FILE%

:: 完了メッセージを表示
echo treeコマンドの結果がデスクトップに出力されました: %OUTPUT_FILE%
pause
