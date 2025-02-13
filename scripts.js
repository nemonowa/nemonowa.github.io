// メニューの表示・非表示を切り替える関数
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
fetch('https://nemonowa.github.io/ui/ui.html')
  .then(response => response.text())
  .then(data => {
    document.getElementById('ui').innerHTML = data;
  })
  .catch(error => console.error('Error loading UI:', error));