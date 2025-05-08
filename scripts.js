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
let currentFileName = decodeURIComponent(location.pathname.split('/').pop() || 'empty.html');
currentFileName = currentFileName.replace(/\.[^/.]+$/, '');
document.title = currentFileName;
document.getElementById('file-name').textContent = currentFileName;

// og:image をファイル名に応じて動的に設定する処理（修正版）
const customImage = location.pathname.replace(/\.html$/, '.png');  // ★ 相対パスを明示
const defaultImage = '/icon.png';  // ★ 絶対パスに変更（ルートにあると仮定）

function setOgImage(path) {
  const metaTag = document.querySelector('meta[property="og:image"]');
  if (metaTag) {
    metaTag.setAttribute('content', path);
  } else {
    const newMeta = document.createElement('meta');
    newMeta.setAttribute('property', 'og:image');
    newMeta.setAttribute('content', path);
    document.head.appendChild(newMeta);
  }
}

fetch(customImage, { method: 'HEAD' })
  .then(response => {
    setOgImage(response.ok ? customImage : defaultImage);
  })
  .catch(() => {
    setOgImage(defaultImage);
  });