# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的 /app 目录
COPY ./requirements.txt /app/

# 安装 requirements.txt 中指定的任何所需包
RUN pip install --no-cache-dir -r requirements.txt

# 将项目代码复制到工作目录
COPY . /app/

# 创建日志目录
RUN mkdir -p /app/logs

# 声明容器监听的端口
EXPOSE 8000

# 运行 main.py
CMD ["python", "main.py"] 