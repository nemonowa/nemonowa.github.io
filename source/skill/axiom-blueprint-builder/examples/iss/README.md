# ISS（国際宇宙ステーション）1ブロック=1m
`python3 iss.py [出力ディレクトリ]` で `ISS_1m.bp`（本・看板のBE入り）、`ISS_1m_noBE.bp`、`iss_books_commands.txt` を生成し、最後に内部の密閉/接続検査を表示します。

- サイズ 109×45×81、8,894ブロック（実物: 幅109m・長さ80m・高さ45m）。
- 主軸 z（+z=前）、トラス x（左舷=+x）、天頂 +y。主軸は y=0。
- 使っている部品: `space_helpers`（tube/tube_lights/tube_racks/lattice_truss/solar_wing/radiator_panel）、`interior_helpers`（check_interior/lectern_with_book/wall_sign）。
- 歩ける: Zvezda・Zarya・Unity・Destiny・Harmony・Quest・Tranquility・Leonardo・Columbus・Kibo・ELM-PS・Cupola・Nauka（ハシゴ）・Poisk/Rassvet（縦穴）。外観のみ: Prichal・BEAM・Bishop・Soyuz・Dragon・Cygnus・HTV-X・Progress。
- 寸法は DLR "Data and modules"、配置は Wikipedia、HTV-X は JAXA/Wikipedia。来訪機は一例、PVRの向き等は近似。
- 手順と失敗談は `references/spacecraft.md`。
