// 名称：NeoScripts ("C:\nexusource\admin\project-neo\nexusource.github.io\scripts.js")
// 説明：メニューの表示・非表示を切り替える関数。
// 著作：Creat by nemo. Copyright © SoraFlete. All Rights Resarved.

function toggleMenu(menuId) {
    const menus = document.querySelectorAll('.menu');
    menus.forEach(menu => {
        if (menu.id === menuId) {
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        } else {
            menu.style.display = 'none';
        }
    });
}

// header.html を読み込む
fetch('https://nemonowa.github.io/header.html')
  .then(response => response.text())
  .then(data => {
    document.getElementById('header').innerHTML = data;
  })
  .catch(error => console.error('Error loading header:', error));

// footer.html を読み込む
fetch('https://nemonowa.github.io/footer.html')
  .then(response => response.text())
  .then(data => {
    document.getElementById('footer').innerHTML = data;
  })
  .catch(error => console.error('Error loading footer:', error));

// ui.html を読み込む
fetch('https://nemonowa.github.io/ui.html')
  .then(response => response.text())
  .then(data => {
    document.getElementById('ui').innerHTML = data;
  })
  .catch(error => console.error('Error loading UI:', error));

// HTMLのタイトルをファイル名に同期させる：<span id="file-name"></span>で利用可能。
let currentFileName = decodeURIComponent(location.pathname.split('/').pop() || 'empty.html');// 現在のパスからファイル名を取得してデコード
currentFileName = currentFileName.replace(/\.[^/.]+$/, ''); // 拡張子を除去（最後のドット以降を削除）
document.title = currentFileName;
document.getElementById('file-name').textContent = currentFileName;