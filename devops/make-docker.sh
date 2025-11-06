#!/bin/bash

echo "🚀 Задание 3"

# Получаем username в lowercase
GITHUB_USER="mishele123"
REPO_NAME="devops" 

echo "👤 GitHub пользователь: $GITHUB_USER"
echo "📦 Репозиторий: $REPO_NAME"

# Проверяем переменную окружения
if [ -z "$CR_PAT" ]; then
    echo "🔐 Переменная CR_PAT не установлена"
    read -s -p "Введите ваш GitHub Personal Access Token: " CR_PAT
    export CR_PAT
    echo ""
fi

# 1. Сборка образа
echo "1. Собираем Docker образ..."
docker build -t my-static-site .

# 2. Локальная проверка
echo "2. Локальная проверка..."
docker rm -f static-site-test 2>/dev/null || true
docker run -d -p 8282:8282 --name static-site-test my-static-site
sleep 2

if curl -s -f http://localhost:8282 > /dev/null; then
    echo "✅ Локальная проверка пройдена"
else
    echo "❌ Локальная проверка не пройдена"
    docker logs static-site-test
    exit 1
fi
docker rm -f static-site-test

# 3. Аутентификация и отправка в registry
echo "3. Аутентификация в GitHub Container Registry..."
echo $CR_PAT | docker login ghcr.io -u $GITHUB_USER --password-stdin

if [ $? -ne 0 ]; then
    echo "❌ Ошибка аутентификации"
    exit 1
fi

echo "✅ Успешный логин"

# 4. Отправка образа
echo "4. Отправка образа в registry..."
REGISTRY_URL="ghcr.io/$GITHUB_USER/$REPO_NAME"

docker tag my-static-site $REGISTRY_URL:latest
docker tag my-static-site $REGISTRY_URL:task3

echo "📤 Отправляем образы..."
docker push $REGISTRY_URL:latest
docker push $REGISTRY_URL:task3

if [ $? -eq 0 ]; then
    echo "✅ Образы отправлены в GitHub Container Registry"
    echo "📦 Ссылки:"
    echo "   $REGISTRY_URL:latest"
    echo "   $REGISTRY_URL:task3"
else
    echo "❌ Ошибка отправки образов"
    exit 1
fi

# 5. Финальная проверка
echo "5. Финальная проверка..."
echo "🔍 Скачиваем образ из registry..."
docker pull $REGISTRY_URL:latest

if [ $? -eq 0 ]; then
    echo "✅ Образ успешно скачан"
    
    echo "🚀 Запускаем скачанный образ..."
    docker run -d -p 8283:8282 --name static-site-final $REGISTRY_URL:latest
    sleep 3
    
    if curl -s -f http://localhost:8283 > /dev/null; then
        echo "✅ Скачанный образ работает корректно"
    else
        echo "❌ Скачанный образ не работает"
        docker logs static-site-final
    fi
    
    docker rm -f static-site-final
else
    echo "❌ Ошибка скачивания образа"
    exit 1
fi

echo ""
echo "🎉 ЗАДАНИЕ 3 ВЫПОЛНЕНО!"
echo "======================="
echo "✅ Образ собран и проверен локально"
echo "✅ Образ отправлен в GitHub Container Registry"
echo "✅ Образ проверен на скачивание и запуск"
echo ""
echo "📊 Локальные образы:"
docker images | grep -E "(my-static-site|$REGISTRY_URL)"
echo ""
echo "🌐 Registry: https://github.com/$GITHUB_USER?tab=packages"
