# 使用官方轻量级 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件到工作目录
COPY . .

# Hugging Face Spaces 强制要求暴露 7860 端口
EXPOSE 7860

# 使用 Gunicorn 启动 Flask 服务，绑定到 7860 端口
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]