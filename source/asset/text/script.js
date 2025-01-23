document.addEventListener('DOMContentLoaded', function() {
  var overlay = document.getElementById('overlay');
  var diveButton = document.getElementById('diveButton');
  var bubbleContainer = document.getElementById('bubbleContainer');

  diveButton.addEventListener('click', function() {
    // フェードインのアニメーションを追加
    overlay.style.opacity = '0';
    overlay.style.display = 'block';
    setTimeout(function() {
      overlay.style.transition = 'opacity 1s';
      overlay.style.opacity = '1';
    }, 100); // 0.1秒後にフェードインを開始

    // 深海に潜る演出（setTimeoutを使って2秒後に実行）
    setTimeout(function() {
      window.location.href = "deep-sea.html"; // 深海ページにリダイレクト（別途作成する必要があります）
    }, 2000); // 2秒後に深海ページに遷移
  });

  // 気泡を生成する関数
  function createBubble() {
    var bubble = document.createElement('div');
    bubble.className = 'bubble';
    var size = Math.random() * 20 + 6; // ランダムなサイズ
    bubble.style.width = size + 'px';
    bubble.style.height = size + 'px';

    // ランダムなX座標とY座標を設定
    var startX = Math.random() * window.innerWidth;
    var startY = Math.random() * window.innerHeight;
    bubble.style.left = startX + 'px';
    bubble.style.top = startY + 'px';

    bubbleContainer.appendChild(bubble);

    // アニメーション終了後に要素を削除
    bubble.addEventListener('animationend', function() {
      bubble.remove();
    });

    // 一定時間後に気泡を削除する
    setTimeout(function() {
      bubble.remove();
    }, 10000); // 10秒後に気泡を削除
  }

  // 定期的に気泡を生成
  setInterval(createBubble, 100); // 0.1秒ごとに気泡を生成
});
