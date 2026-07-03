# TFT Auto Chess - 云顶之弈自动识别和推荐系统

一个基于 AI 和胜率数据的云顶之弈卡牌自动识别、推荐和选择系统。

## 功能特性

- 🎯 **实时卡牌识别** - 使用 YOLOv8 检测游戏画面中的卡牌
- 📊 **胜率数据推荐** - 基于最新的云顶之弈胜率数据推荐最优卡牌
- 🤖 **自动选择** - 自动点击推荐的卡牌
- 📈 **阵容优化** - 分析当前阵容并给出优化建议
- 🎮 **实时监控** - 持续监控游戏状态

## 项目结构

```
tft-auto-chess/
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py              # 配置文件
├── models/
│   ├── __init__.py
│   ├── card_detector.py         # 卡牌检测模型
│   └── recommendation_engine.py # 推荐引擎
├── data/
│   ├── __init__.py
│   ├── winrate_fetcher.py       # 胜率数据获取
│   └── card_database.py         # 卡牌数据库
├── game/
│   ├── __init__.py
│   ├── screen_capture.py        # 游戏截图
│   ├── game_state.py            # 游戏状态分析
│   └── auto_click.py            # 自动点击
├── utils/
│   ├── __init__.py
│   ├── logger.py                # 日志
│   └── helpers.py               # 辅助函数
├── main.py                      # 主程序
└── tests/
    ├── __init__.py
    └── test_detector.py
```

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/lujun177/tft-auto-chess.git
cd tft-auto-chess
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 下载模型
```bash
python scripts/download_models.py
```

### 4. 运行程序
```bash
python main.py
```

## 配置

编辑 `config/settings.py` 进行配置：

```python
# 游戏窗口设置
GAME_WINDOW_NAME = "League of Legends"
SCREENSHOT_INTERVAL = 1  # 秒

# 卡牌识别设置
CONFIDENCE_THRESHOLD = 0.5
MODEL_PATH = "models/yolov8_tft.pt"

# 推荐设置
USE_WINRATE_DATA = True
MIN_SAMPLE_SIZE = 100  # 最小样本数
```

## 系统要求

- Python 3.8+
- CUDA 11.8+ (推荐，用于 GPU 加速)
- 英雄联盟云顶之弈客户端
- 1920x1080 或以上分辨率

## API 参考

### 卡牌识别
```python
from models.card_detector import CardDetector

detector = CardDetector(model_path="models/yolov8_tft.pt")
image = cv2.imread("screenshot.png")
detections = detector.detect(image)
# 返回: [(card_name, confidence, bbox), ...]
```

### 推荐引擎
```python
from models.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()
recommendations = engine.recommend(
    current_cards=["Ahri", "Akali"],
    level=5,
    gold=20,
    top_n=5
)
# 返回: [("Ezreal", 0.85), ("Lux", 0.82), ...]
```

## 数据源

- 胜率数据来源：Tacticians.gg / TFTactics / FF15.gg
- 卡牌信息：官方 Riot API
- 模型训练数据：自标注

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 免责声明

该工具仅用于学习研究目的。使用本工具的用户需自行承担所有责任。