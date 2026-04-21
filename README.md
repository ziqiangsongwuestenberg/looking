# Looking - Fashion News Monitor

自动搜索并收集 fashion 相关新闻的 Python 项目。

## 功能

- 每日定时搜索最新 fashion 相关新闻
- 支持多个关键词搜索
- 结果保存为 JSON 和 Markdown 格式
- 可配置定时任务

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制配置模板并填入你的设置：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml` 设置搜索关键词和定时任务。

## 运行

```bash
# 单次运行
python main.py

# 启动定时任务
python main.py --schedule
```

## 输出

搜索结果保存在 `output/` 目录：
- `news_YYYY-MM-DD.json` - JSON 格式
- `news_YYYY-MM-DD.md` - Markdown 格式

## License

MIT
