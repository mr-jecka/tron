FROM python:3.11

# Установка рабочей директории
WORKDIR /src

# Установка часового пояса
RUN apt-get update && apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && \
    echo "Europe/Moscow" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata

# Копирование всех файлов приложения
COPY ./src /src/src
COPY ./main.py /src/
COPY ./src/requirements.txt /src/

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel && \
    pip install --no-cache-dir --upgrade -r /src/requirements.txt

# Указание команды для запуска
CMD ["python3", "/src/main.py"]