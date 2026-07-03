# 安装和使用指南

## 系统要求

- **操作系统**：Windows 10/11
- **Python**：3.8 或更高版本
- **显卡**：NVIDIA GPU (可选，用于加速)
- **分辨率**：1920x1080 (推荐)

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/lujun177/tft-auto-chess.git
cd tft-auto-chess
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境

复制 `.env.example` 并编辑 `.env`：

```bash
cp .env.example .env
```

编辑 `config/settings.py` 中的配置项。

### 5. 下载模型 (可选)

YOLOv8 模型会在首次使用时自动下载。如需手动下载：

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
```

## 快速开始

### 运行 Demo

```bash
python main.py
```

### 使用推荐引擎

```python
from main import TFTAutoChess

# 初始化系统
system = TFTAutoChess()

# 获取推荐
recommendations = system.get_recommendations(
    current_cards=['ahri', 'akali'],
    level=5,
    top_n=5
)

print("推荐卡牌:")
for champion, score in recommendations:
    print(f"  {champion}: {score:.2%}")
```

### 分析阵容

```python
# 分析当前阵容的羁绊
synergies = system.analyze_synergies(['ahri', 'akali'])
print(f"活跃羁绊: {synergies['active_synergies']}")
print(f"即将完成: {synergies['near_completion']}")
```

## 数据源

系统从以下来源获取数据：

1. **Tacticians.gg** - 主要的云顶之弈数据源
2. **TFTactics.gg** - 备选数据源
3. **官方 Riot API** - 卡牌信息 (需要 API Key)

## 配置说明

### config/settings.py

**卡牌识别**：
- `CONFIDENCE_THRESHOLD` - 置信度阈值 (0-1)
- `MODEL_PATH` - YOLOv8 模型路径

**推荐引擎**：
- `WEIGHT_WINRATE` - 胜率权重
- `WEIGHT_SYNERGY` - 羁绊权重
- `WEIGHT_PLACEMENT` - 名次权重
- `TOP_N_RECOMMENDATIONS` - 推荐数量

**自动化**：
- `AUTO_CLICK_ENABLED` - 启用自动点击
- `ENABLE_AUTO_RECOMMENDATION` - 启用自动推荐

## 常见问题

### Q: 模型下载很慢怎么办？

A: 可以手动下载 YOLOv8m 模型：
```bash
python -c "from ultralytics import YOLO; model = YOLO('yolov8m.pt')"
```

### Q: 如何使用 GPU？

A: 在 `config/settings.py` 中设置：
```python
USE_GPU = True
GPU_DEVICE = 0  # CUDA 设备 ID
```

### Q: 推荐不准确怎么办？

A: 
1. 检查 `MIN_SAMPLE_SIZE` - 确保有足够的样本数据
2. 调整权重值 (WEIGHT_WINRATE, WEIGHT_SYNERGY, etc.)
3. 确保数据源是最新的

### Q: 如何禁用自动点击？

A: 在配置中设置：
```python
AUTO_CLICK_ENABLED = False
```

## 数据更新

系统会自动缓存数据。更新间隔由 `WINRATE_UPDATE_FREQUENCY` 设置（默认24小时）。

手动更新缓存：

```python
from data.winrate_fetcher import WinrateFetcher

fetcher = WinrateFetcher()
data = fetcher.fetch_and_cache('tacticians', force_refresh=True)
```

## API 参考

### CardDetector

```python
from models.card_detector import CardDetector

detector = CardDetector()

# 检测卡牌
detections = detector.detect(image)
# 返回: [
#   {
#     'name': 'ahri',
#     'confidence': 0.95,
#     'bbox': (100, 100, 200, 200),
#     'center': (150, 150)
#   },
#   ...
# ]

# 过滤检测结果
filtered = detector.filter_detections(
    detections,
    class_filter=['ahri', 'lux'],
    min_confidence=0.7
)
```

### RecommendationEngine

```python
from models.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()
engine.load_winrate_data(winrate_data)

# 获取推荐
recommendations = engine.recommend(
    current_cards=['ahri'],
    level=5,
    num_recommendations=5
)

# 分析羁绊
analysis = engine.get_synergy_analysis(['ahri', 'akali'])

# 获取分级推荐
tiers = engine.get_tier_recommendations()
```

### WinrateFetcher

```python
from data.winrate_fetcher import WinrateFetcher

fetcher = WinrateFetcher()

# 获取并缓存数据
data = fetcher.fetch_and_cache('tacticians')

# 只获取缓存数据
cached = fetcher.get_cached_data('tacticians')

# 清除缓存
fetcher.clear_cache('tacticians')
```

## 故障排除

### 导入错误

如果遇到导入错误，确保：
1. 虚拟环境已激活
2. 所有依赖已安装：`pip install -r requirements.txt`
3. 项目根目录正确

### 模型加载失败

```bash
# 重新下载模型
rm -rf ~/.yolo
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
```

### 数据获取失败

检查网络连接和 API 源是否可用：

```python
import requests
response = requests.get('https://tacticians.gg/api/data/current-set', timeout=10)
print(response.status_code)
```

## 许可证

MIT License

## 支持

如有问题或建议，请提交 Issue 或 Pull Request！