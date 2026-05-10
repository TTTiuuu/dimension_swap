# Dimension Swap Video Effect Tool

视频维度互换特效制作工具 - 将视频的时间轴与空间轴进行互换，产生高维降维切片的视觉效果。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.0+-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-yellow)

## 功能特点

- 🎬 **T-X 互换**: 将时间轴与宽度轴互换
- 🎬 **T-Y 互换**: 将时间轴与高度轴互换  
- 🖱️ **拖拽支持**: 直接拖拽视频文件到窗口
- 📊 **实时进度**: 显示转换进度和日志
- ✅ **智能裁剪**: 自动检测并提示最佳视频长度

## 效果说明

| 原视频 | 转换模式 | 输出分辨率 | 输出帧数 |
|--------|----------|-----------|----------|
| W×H, T帧 | T-X | W×T | H帧 |
| W×H, T帧 | T-Y | H×T | W帧 |

### 推荐格式

- **16:9 横屏输出**: 用 9:16 竖屏视频做 T-X 互换
- **9:16 竖屏输出**: 用 16:9 横屏视频做 T-Y 互换
- **4:3 输出**: 用 3:4 竖屏视频做 T-X 互换
- **3:4 输出**: 用 4:3 横屏视频做 T-Y 互换

## 安装依赖

```bash
conda create -n dimension_swap python=3.11 -y
conda activate dimension_swap
pip install opencv-python PySide6 numpy
```

## 运行

```bash
python dimension_swap.py
```

## 依赖环境

- Python 3.11+
- OpenCV (cv2)
- PySide6
- NumPy

## 项目结构

```
dimension_swap/
├── dimension_swap.py    # 主程序
├── .gitignore           # Git忽略文件
├── LICENSE              # MIT 许可证
├── README.md            # 本文件
└── output/              # 输出目录（不纳入版本控制）
```

## 许可

MIT License

## 作者

TTTiuuu
