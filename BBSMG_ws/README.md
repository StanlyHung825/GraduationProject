# B-BSMG 離線筆畫模擬

這個目錄把 waypoint 與毛筆控制參數轉成灰階筆畫圖，不依賴 ROS 2 runtime。
所有命令都在 `bbsmg_phase1` Docker container 的 `/BBSMG_ws` 執行。

## 進入 container

在 host 執行：

```bash
docker exec -it bbsmg_phase1 bash
cd /BBSMG_ws
```

若要重新安裝 Python 依賴：

```bash
python3 -m pip install -r requirements.txt
```

## 產生單點筆畫

```bash
python3 -m bbsmg.single_point \
  --input samples/single_point.json \
  --out-dir out/single_point
```

輸出為 `single_point.png` 與包含幾何資料的
`single_point_debug.json`。

## 產生完整字形

```bash
python3 -m bbsmg.character_simulation \
  --input samples/waypoint_path/path_example.json \
  --out-dir out/character
```

若 reference image 是「黑底白字」且尺寸相同，可加上：

```bash
--target path/to/reference.png
```

stdout 會顯示 `pixel_difference`（越低越好）與 `pixel_score`（越高越好）。

## 疊圖比較

目前 ideal sample 是白底黑字；用下列命令產生彩色差異圖：

```bash
python3 -m bbsmg.visualize_comparison \
  --simulated out/character/character_simulation.png \
  --ideal samples/ideal_char/27704-black.png \
  --output out/character/overlay.png
```

## SVG 轉 PNG

這是一次性資料準備工具，需要 container 內有 Google Chrome 或 Chromium：

```bash
python3 svg_png_converter/svg_to_png.py \
  svg_png_converter/27704-black.svg \
  samples/ideal_char/27704-black.png
```

## 測試

```bash
python3 -m unittest discover -s tests -v
```

`out/` 與 `__pycache__/` 都是可重建的執行產物，不應提交到 Git。

## 輸入格式

- 單點：`x`、`y`、`brush`，可選 `render`。
- 完整字形：`waypoints`、預設 `brush`，可選 `render`。
- `brush` 包含 `h`、`alpha`、`beta`；角度使用 degree。
- waypoint 的 `type` 為 `write` 或 `travel`；`travel` 不會渲染。
- 完整字形固定使用 1024×1024 畫布，waypoint `(0, 0)` 是左上角，`x/y` 直接視為像素座標。
- `render.samples_per_curve` 可設定每個筆觸輪廓的取樣數；單點工具另外支援 `width`、`height` 與 `scale`。
