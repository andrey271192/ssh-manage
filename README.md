# PCA SSH — Private Control Administration

SSH-клиент с карточным интерфейсом, AI-агентами и автосохранением сессий.

## Возможности

- **Карточный интерфейс** — группы с цветными индикаторами, красивые карточки подключений
- **AI-агент** — подсказки команд через Claude API, DeepSeek API или локальную базу
- **400+ команд** — для Linux (Ubuntu/Debian/CentOS) и Keenetic (NDMS CLI)
- **Группы сессий** — организация подключений по группам с drag & drop
- **Автосохранение** — все подключения сохраняются автоматически
- **Вкладки** — несколько SSH-сессий одновременно
- **Скрываемая панель команд** — больше места для AI-агента
- **Тёмная тема** — Catppuccin Mocha

## Установка

### Windows — быстрый запуск (без сборки)

```
1. Установи Python 3.10+ с https://python.org/downloads/
   (отметь "Add Python to PATH")
2. Скачай репозиторий
3. Запусти install.bat
```

### Windows — собрать .exe

```
1. Установи Python 3.10+
2. Запусти build.bat
3. Готовый файл: dist\PCA_SSH.exe
```

Или полная установка с иконкой и копированием на рабочий стол:
```
powershell -ExecutionPolicy Bypass -File full_install.ps1
```

### macOS — быстрый запуск

```bash
# Установи Python если нет
brew install python3

# Установи зависимости
pip3 install paramiko

# Запусти
python3 ssh_manager.py
```

### macOS — собрать .app

```bash
chmod +x build_mac.sh
./build_mac.sh
# Готовый файл: dist/PCA_SSH
```

## AI-агент

Встроенный агент помогает подобрать команды. Три режима:

| Провайдер | Описание | API-ключ |
|-----------|----------|----------|
| Локальный | База из 400+ команд, поиск по ключевым словам | Не нужен |
| Claude | Умный ассистент от Anthropic | [console.anthropic.com](https://console.anthropic.com) |
| DeepSeek | Альтернативный AI-провайдер | [platform.deepseek.com](https://platform.deepseek.com) |

Настройка: кнопка ⚙ в панели агента.

## Файлы

| Файл | Описание |
|------|----------|
| `sessions.json` | Сохранённые SSH-сессии (рядом с .exe) |
| `pca_config.json` | Настройки AI-агента и интерфейса |

## Ссылки

- [GitHub](https://github.com/nickolay-frolov)
- [Telegram](https://t.me/lot_andrey)
- [Boosty](https://boosty.to/lot_andrey)
