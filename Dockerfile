FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 默认运行全量搜索
CMD ["python", "main.py", "--all"]

# 可选启动方式：
# python main.py --fashion   仅 fashion 新闻
# python main.py --monitor   网站监控（需先配 config_monitor.yaml）
# python main.py --gay       Gay 新闻
# python main.py --schedule  定时任务