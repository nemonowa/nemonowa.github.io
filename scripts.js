// 名称：NeoScripts ("C:\nexusource\admin\project-neo\nexusource.github.io\scripts.js")
// 説明：メニューの表示・非表示を切り替える関数。
// 著作：Creat by nemo. Copyright © SoraFlete. All Rights Reserved.

function toggleMenu(menuId) {
  const menus = document.querySelectorAll(".menu");
  menus.forEach((menu) => {
    if (menu.id === menuId) {
      menu.style.display = menu.style.display === "block" ? "none" : "block";
    } else {
      menu.style.display = "none";
    }
  });
}

// header.html をルート直下から読み込む
fetch("/header.html")
  .then((response) => response.text())
  .then((data) => {
    document.getElementById("header").innerHTML = data;
  })
  .catch((error) => console.error("Error loading header:", error));

// footer.html をルート直下から読み込む
fetch("/footer.html")
  .then((response) => response.text())
  .then((data) => {
    document.getElementById("footer").innerHTML = data;
  })
  .catch((error) => console.error("Error loading footer:", error));

// ui.html をルート直下から読み込む
fetch("/ui.html")
  .then((response) => response.text())
  .then((data) => {
    document.getElementById("ui").innerHTML = data;
  })
  .catch((error) => console.error("Error loading UI:", error));

// HTMLのタイトルをファイル名に同期させる
let currentFileName = decodeURIComponent(
  location.pathname.split("/").pop() || "empty.html"
);
currentFileName = currentFileName.replace(/\.[^/.]+$/, "");
document.title = currentFileName;
const fileNameSpan = document.getElementById("file-name");
if (fileNameSpan) {
  fileNameSpan.textContent = currentFileName;
}

// og:image をファイル名に応じて動的に設定する
const customImage = location.pathname.replace(/\.html$/, ".png"); // ★ ルート直下想定
const defaultImage = "/icon.png"; // ★ ルート直下

function setOgImage(path) {
  const metaTag = document.querySelector('meta[property="og:image"]');
  if (metaTag) {
    metaTag.setAttribute("content", path);
  } else {
    const newMeta = document.createElement("meta");
    newMeta.setAttribute("property", "og:image");
    newMeta.setAttribute("content", path);
    document.head.appendChild(newMeta);
  }
}

fetch(customImage, { method: "HEAD" })
  .then((response) => setOgImage(response.ok ? customImage : defaultImage))
  .catch(() => setOgImage(defaultImage));
