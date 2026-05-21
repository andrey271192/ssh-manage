"""
PCA SSH — Private Control Administration
SSH client with card-based UI, AI agents (Claude/DeepSeek), and auto-save sessions.
Tkinter GUI + paramiko SSH + JSON session store.
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont, simpledialog, filedialog
import paramiko
import threading
import json
import os
import sys
import re
import base64
import socket
import urllib.request
import urllib.error
import ssl
from datetime import datetime
from pathlib import Path
import stat

APP_NAME = "PCA SSH"
APP_SUBTITLE = "Private Control Administration"
VERSION = "2.0"

# ── Card Colors (Catppuccin) ──────────────────────────────────

CARD_COLORS = [
    "#89b4fa",  # blue
    "#a6e3a1",  # green
    "#cba6f7",  # purple
    "#fab387",  # orange
    "#f38ba8",  # red
    "#94e2d5",  # teal
    "#f9e2af",  # yellow
    "#89dceb",  # sky
]

# ── Quick Commands ─────────────────────────────────────────────

COMMANDS = {
    "Ubuntu / Linux": {
        "Система": [
            ("uname -a", "Ядро и архитектура"),
            ("cat /etc/os-release", "Версия ОС"),
            ("uptime -p", "Аптайм"),
            ("hostnamectl", "Имя хоста и ОС"),
            ("timedatectl", "Время и часовой пояс"),
            ("last reboot | head -5", "Последние перезагрузки"),
            ("who", "Кто залогинен"),
            ("w", "Активные сессии и нагрузка"),
        ],
        "Ресурсы": [
            ("htop", "Мониторинг процессов (интерактивный)"),
            ("top -bn1 | head -20", "Топ процессов (снимок)"),
            ("free -h", "Оперативная память"),
            ("df -hT", "Диски и файловые системы"),
            ("du -sh /* 2>/dev/null | sort -rh | head -10", "Топ-10 тяжёлых директорий"),
            ("lsblk", "Блочные устройства"),
            ("iostat -x 1 3", "Нагрузка на диски"),
            ("vmstat 1 5", "CPU/память/swap за 5 сек"),
            ("cat /proc/cpuinfo | grep 'model name' | head -1", "Модель процессора"),
            ("nproc", "Количество ядер CPU"),
        ],
        "Сеть": [
            ("ip addr", "IP-адреса интерфейсов"),
            ("ip route", "Таблица маршрутов"),
            ("ss -tulpn", "Открытые порты и процессы"),
            ("netstat -tulpn", "Порты (классический)"),
            ("curl -s ifconfig.me", "Внешний IP"),
            ("ping -c 4 8.8.8.8", "Пинг Google DNS"),
            ("ping -c 4 1.1.1.1", "Пинг Cloudflare"),
            ("traceroute 8.8.8.8", "Трассировка до Google"),
            ("dig google.com +short", "DNS-запрос"),
            ("nslookup google.com", "DNS (nslookup)"),
            ("iptables -L -n --line-numbers", "Правила файрвола"),
            ("ufw status verbose", "Статус UFW"),
            ("cat /etc/resolv.conf", "DNS-серверы"),
            ("arp -a", "ARP-таблица"),
            ("ethtool eth0", "Состояние сетевого адаптера"),
        ],
        "Сервисы": [
            ("systemctl list-units --type=service --state=running", "Запущенные сервисы"),
            ("systemctl status", "Общий статус systemd"),
            ("systemctl --failed", "Упавшие сервисы"),
            ("journalctl -xe --no-pager | tail -50", "Последние логи"),
            ("journalctl -u nginx --since '1 hour ago'", "Логи nginx за час"),
            ("crontab -l", "Задачи cron"),
            ("systemctl list-timers", "Systemd-таймеры"),
        ],
        "Docker": [
            ("docker ps", "Запущенные контейнеры"),
            ("docker ps -a", "Все контейнеры"),
            ("docker images", "Образы"),
            ("docker stats --no-stream", "Ресурсы контейнеров"),
            ("docker logs --tail 50 $(docker ps -q | head -1)", "Логи последнего контейнера"),
            ("docker system df", "Занятое место Docker"),
            ("docker system prune -f", "Очистка мусора Docker"),
            ("docker-compose ps", "Compose-сервисы"),
        ],
        "Безопасность": [
            ("last -10", "Последние 10 логинов"),
            ("lastb -10 2>/dev/null", "Неудачные логины"),
            ("cat /var/log/auth.log | tail -20", "Лог авторизации"),
            ("find / -perm -4000 -type f 2>/dev/null", "SUID-файлы"),
            ("cat /etc/passwd | grep -v nologin | grep -v false", "Пользователи с шеллом"),
            ("ss -tulpn | grep LISTEN", "Слушающие порты"),
            ("fail2ban-client status 2>/dev/null", "Статус Fail2Ban"),
            ("openssl x509 -in /etc/ssl/certs/*.pem -noout -dates 2>/dev/null | head -4", "Сроки SSL-сертов"),
        ],
        "Пользователи и пароли": [
            ("cat /etc/passwd", "Все пользователи системы"),
            ("cat /etc/passwd | grep -v nologin | grep -v false", "Пользователи с шеллом"),
            ("getent passwd | awk -F: '$3 >= 1000 {print $1}'", "Обычные пользователи (UID >= 1000)"),
            ("groups", "Группы текущего пользователя"),
            ("id", "UID/GID текущего пользователя"),
            ("id username", "Инфо о пользователе username"),
            ("passwd", "Сменить свой пароль"),
            ("passwd username", "Сменить пароль пользователю"),
            ("chage -l username", "Срок действия пароля"),
            ("chage -M 90 username", "Пароль истекает через 90 дней"),
            ("useradd -m -s /bin/bash username", "Создать пользователя с домашней папкой"),
            ("useradd -m -s /bin/bash -G sudo username", "Создать пользователя с sudo"),
            ("useradd -r -s /usr/sbin/nologin svcname", "Создать сервисного пользователя"),
            ("userdel username", "Удалить пользователя (без домашней)"),
            ("userdel -r username", "Удалить пользователя + домашнюю папку"),
            ("usermod -aG sudo username", "Добавить в группу sudo"),
            ("usermod -aG docker username", "Добавить в группу docker"),
            ("usermod -L username", "Заблокировать пользователя"),
            ("usermod -U username", "Разблокировать пользователя"),
            ("usermod -s /usr/sbin/nologin username", "Запретить логин"),
            ("usermod -s /bin/bash username", "Разрешить логин"),
            ("groupadd groupname", "Создать группу"),
            ("groupdel groupname", "Удалить группу"),
            ("gpasswd -d username groupname", "Убрать из группы"),
            ("cat /etc/shadow | grep username", "Хеш пароля (root)"),
            ("passwd -S username", "Статус пароля"),
            ("echo 'username:newpassword' | chpasswd", "Задать пароль одной командой"),
        ],
        "SSH-ключи": [
            ("ssh-keygen -t ed25519 -C 'comment'", "Генерировать SSH-ключ ed25519"),
            ("ssh-keygen -t rsa -b 4096", "Генерировать SSH-ключ RSA 4096"),
            ("cat ~/.ssh/id_ed25519.pub", "Показать публичный ключ"),
            ("cat ~/.ssh/authorized_keys", "Авторизованные ключи"),
            ("ssh-copy-id user@host", "Скопировать ключ на сервер"),
            ("chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys", "Права на SSH-директорию"),
        ],
        "Файлы и пакеты": [
            ("ls -lahS / | head -20", "Большие файлы в корне"),
            ("find /var/log -name '*.log' -mtime -1", "Свежие логи"),
            ("apt list --upgradable 2>/dev/null", "Доступные обновления (apt)"),
            ("yum check-update 2>/dev/null", "Доступные обновления (yum)"),
            ("dpkg -l | wc -l", "Количество пакетов"),
            ("tail -f /var/log/syslog", "Сислог в реальном времени"),
        ],
    },
    "Keenetic (NDMS CLI)": {
        "Информация": [
            ("show version", "Прошивка и модель"),
            ("show system", "Загрузка CPU/RAM"),
            ("show clock", "Время роутера"),
            ("show uptime", "Аптайм"),
            ("show log", "Системный лог"),
            ("show running-config", "Текущая конфигурация"),
            ("show startup-config", "Стартовая конфигурация"),
            ("show components", "Установленные компоненты"),
        ],
        "Сеть": [
            ("show interface", "Все интерфейсы"),
            ("show interface WifiMaster0", "Wi-Fi 2.4 ГГц"),
            ("show interface WifiMaster1", "Wi-Fi 5 ГГц"),
            ("show interface PPPoE0", "PPPoE-подключение"),
            ("show ip route", "Таблица маршрутов"),
            ("show ip arp", "ARP-таблица"),
            ("show ip dhcp bindings", "DHCP-аренды"),
            ("show ip dhcp pool", "DHCP-пулы"),
            ("show ip hotspot", "Подключённые устройства"),
            ("show ip hotspot host", "Список хостов"),
            ("show ndns", "Статус KeenDNS"),
            ("show internet status", "Статус интернета"),
        ],
        "VPN": [
            ("show crypto ipsec sa", "IPsec-туннели"),
            ("show vpn-server", "VPN-сервер"),
            ("show interface Wireguard0", "WireGuard статус"),
            ("show interface OpenVPN0", "OpenVPN статус"),
            ("show interface PPTP0", "PPTP статус"),
            ("show interface L2TP0", "L2TP статус"),
            ("show interface SSTP0", "SSTP статус"),
        ],
        "Wi-Fi": [
            ("show associations", "Подключённые клиенты Wi-Fi"),
            ("show interface WifiMaster0 wps", "WPS статус 2.4"),
            ("show interface WifiMaster1 wps", "WPS статус 5"),
            ("interface WifiMaster0 down", "Выключить Wi-Fi 2.4"),
            ("interface WifiMaster0 up", "Включить Wi-Fi 2.4"),
            ("interface WifiMaster1 down", "Выключить Wi-Fi 5"),
            ("interface WifiMaster1 up", "Включить Wi-Fi 5"),
        ],
        "USB и накопители": [
            ("show usb", "USB-устройства"),
            ("show media", "Накопители"),
            ("show printer", "USB-принтер"),
            ("show interface UsbModem0", "USB-модем"),
        ],
        "Диагностика": [
            ("tools ping 8.8.8.8", "Пинг Google DNS"),
            ("tools ping 1.1.1.1", "Пинг Cloudflare"),
            ("tools traceroute 8.8.8.8", "Трассировка"),
            ("tools dns-lookup google.com", "DNS-запрос"),
            ("tools ntp-sync", "Синхронизация времени"),
            ("show speed-test", "Speedtest (если доступен)"),
        ],
        "Пользователи и пароли": [
            ("show user", "Список пользователей роутера"),
            ("user admin", "Войти в настройки пользователя admin"),
            ("user admin password newpass", "Сменить пароль admin"),
            ("user add username", "Создать пользователя"),
            ("user username password newpass", "Задать пароль пользователю"),
            ("user username tag http", "Разрешить доступ к web-интерфейсу"),
            ("user username tag cli", "Разрешить доступ к CLI"),
            ("user username tag http,cli,ftp", "Доступ: web + CLI + FTP"),
            ("no user username", "Удалить пользователя"),
            ("user username permit http 192.168.1.0/24", "Доступ только из подсети"),
            ("ip http security-level private", "Web-интерфейс только из LAN"),
            ("ip http security-level public", "Web-интерфейс из WAN (осторожно!)"),
            ("ip telnet security-level private", "Telnet только из LAN"),
            ("ip ssh security-level private", "SSH только из LAN"),
        ],
        "Управление": [
            ("system configuration save", "Сохранить конфигурацию"),
            ("system reboot", "Перезагрузка роутера"),
            ("system log clear", "Очистить лог"),
            ("tools firmware check", "Проверить обновления прошивки"),
            ("tools firmware upgrade", "Обновить прошивку"),
            ("copy running-config startup-config", "Применить конфигурацию"),
        ],
    },
    "Быстрые скрипты": {
        "Мониторинг": [
            ("watch -n 2 'free -h && echo --- && df -h /'", "Память+диск каждые 2 сек"),
            ("while true; do date; ss -s; sleep 5; done", "Счётчик соединений каждые 5 сек"),
            ("tail -f /var/log/syslog | grep -i error", "Ошибки в сислоге (live)"),
            ("sar -u 1 10", "CPU-нагрузка 10 замеров"),
        ],
        "Сеть (скрипты)": [
            ("for h in 8.8.8.8 1.1.1.1 ya.ru; do echo -n \"$h: \"; ping -c1 -W2 $h | grep time= || echo FAIL; done", "Пинг 3 хостов"),
            ("curl -so /dev/null -w '%{time_total}s' https://google.com && echo", "Время ответа Google"),
            ("ss -s", "Сводка по соединениям"),
        ],
        "Очистка": [
            ("apt autoremove -y && apt clean", "Очистка apt (Debian/Ubuntu)"),
            ("journalctl --vacuum-size=100M", "Обрезать логи до 100MB"),
            ("find /tmp -mtime +7 -delete", "Удалить файлы /tmp старше 7 дней"),
            ("find /var/log -name '*.gz' -delete", "Удалить сжатые логи"),
        ],
    },
}

# ── Command Agent Knowledge Base ───────────────────────────────

AGENT_KB = [
    (["обновить", "update", "upgrade", "обновление", "апдейт"],
     "linux", [
        ("sudo apt update && sudo apt upgrade -y", "Обновить все пакеты (Debian/Ubuntu)"),
        ("sudo apt dist-upgrade -y", "Полное обновление с зависимостями"),
        ("sudo yum update -y", "Обновить все пакеты (CentOS/RHEL)"),
        ("sudo dnf upgrade -y", "Обновить все пакеты (Fedora)"),
        ("sudo apt list --upgradable", "Показать доступные обновления"),
    ]),
    (["перезагрузить", "reboot", "restart", "рестарт", "ребут"],
     "linux", [
        ("sudo reboot", "Перезагрузить сервер"),
        ("sudo shutdown -r +1 'Reboot in 1 min'", "Перезагрузка через 1 минуту"),
        ("sudo systemctl restart nginx", "Перестартовать nginx"),
        ("sudo systemctl restart sshd", "Перестартовать SSH"),
    ]),
    (["перезагрузить", "reboot", "restart"],
     "keenetic", [
        ("system reboot", "Перезагрузить роутер"),
    ]),
    (["место", "disk", "диск", "свободно", "занято", "очистить диск", "нет места"],
     "linux", [
        ("df -hT", "Показать свободное место"),
        ("du -sh /* 2>/dev/null | sort -rh | head -10", "Топ-10 тяжёлых папок"),
        ("sudo apt autoremove -y && sudo apt clean", "Очистить кэш apt"),
        ("sudo journalctl --vacuum-size=100M", "Обрезать логи до 100MB"),
        ("find /var/log -name '*.gz' -delete", "Удалить сжатые логи"),
        ("docker system prune -af", "Очистить Docker (образы, контейнеры)"),
    ]),
    (["память", "ram", "memory", "swap", "oom"],
     "linux", [
        ("free -h", "Показать RAM и swap"),
        ("top -bn1 | head -20", "Топ процессов по CPU/RAM"),
        ("ps aux --sort=-%mem | head -15", "Процессы по потреблению RAM"),
        ("sudo swapon --show", "Активные swap-разделы"),
        ("sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches", "Очистить кэш памяти"),
    ]),
    (["пользователь", "user", "юзер", "создать пользователя", "добавить пользователя"],
     "linux", [
        ("sudo useradd -m -s /bin/bash username", "Создать пользователя"),
        ("sudo useradd -m -s /bin/bash -G sudo username", "Создать с sudo"),
        ("sudo passwd username", "Задать пароль"),
        ("sudo userdel -r username", "Удалить пользователя"),
        ("cat /etc/passwd | grep -v nologin", "Пользователи с шеллом"),
    ]),
    (["пользователь", "user", "юзер", "пароль"],
     "keenetic", [
        ("show user", "Список пользователей роутера"),
        ("user add username", "Создать пользователя"),
        ("user admin password newpass", "Сменить пароль admin"),
        ("no user username", "Удалить пользователя"),
    ]),
    (["пароль", "password", "сменить пароль"],
     "linux", [
        ("passwd", "Сменить свой пароль"),
        ("sudo passwd username", "Сменить пароль другому"),
        ("sudo chage -l username", "Срок действия пароля"),
        ("echo 'user:pass' | sudo chpasswd", "Задать пароль одной командой"),
    ]),
    (["порт", "port", "слушает", "listen", "открытые порты"],
     "linux", [
        ("ss -tulpn", "Все слушающие порты"),
        ("ss -tulpn | grep :80", "Кто слушает порт 80"),
        ("sudo lsof -i :443", "Процесс на порту 443"),
        ("sudo ufw allow 8080/tcp", "Открыть порт 8080"),
        ("sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT", "Открыть порт iptables"),
    ]),
    (["файрвол", "firewall", "ufw", "iptables", "заблокировать"],
     "linux", [
        ("sudo ufw status verbose", "Статус UFW"),
        ("sudo ufw enable", "Включить UFW"),
        ("sudo ufw allow ssh", "Разрешить SSH"),
        ("sudo ufw allow 80,443/tcp", "Разрешить HTTP/HTTPS"),
        ("sudo ufw deny from 1.2.3.4", "Заблокировать IP"),
        ("sudo iptables -L -n --line-numbers", "Правила iptables"),
    ]),
    (["сервис", "service", "демон", "systemctl", "запустить", "остановить"],
     "linux", [
        ("sudo systemctl status servicename", "Статус сервиса"),
        ("sudo systemctl start servicename", "Запустить"),
        ("sudo systemctl stop servicename", "Остановить"),
        ("sudo systemctl restart servicename", "Перезапустить"),
        ("sudo systemctl enable servicename", "Автозапуск"),
        ("sudo systemctl disable servicename", "Убрать из автозапуска"),
        ("journalctl -u servicename -f", "Логи сервиса (live)"),
    ]),
    (["лог", "log", "логи", "журнал", "ошибки"],
     "linux", [
        ("journalctl -xe --no-pager | tail -50", "Последние системные логи"),
        ("tail -f /var/log/syslog", "Сислог (live)"),
        ("tail -f /var/log/auth.log", "Логи авторизации (live)"),
        ("journalctl --since '1 hour ago'", "Логи за последний час"),
        ("dmesg | tail -30", "Сообщения ядра"),
        ("grep -i error /var/log/syslog | tail -20", "Ошибки в сислоге"),
    ]),
    (["лог", "log"],
     "keenetic", [
        ("show log", "Системный лог роутера"),
        ("system log clear", "Очистить лог"),
    ]),
    (["ssh", "ключ", "key", "ssh-ключ", "авторизация"],
     "linux", [
        ("ssh-keygen -t ed25519 -C 'my key'", "Генерировать ключ ed25519"),
        ("cat ~/.ssh/id_ed25519.pub", "Показать публичный ключ"),
        ("ssh-copy-id user@host", "Скопировать ключ на сервер"),
        ("chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys", "Права SSH"),
    ]),
    (["docker", "контейнер", "container"],
     "linux", [
        ("docker ps", "Запущенные контейнеры"),
        ("docker ps -a", "Все контейнеры"),
        ("docker logs --tail 50 container_name", "Логи контейнера"),
        ("docker restart container_name", "Перезапустить контейнер"),
        ("docker system prune -f", "Очистить мусор"),
        ("docker stats --no-stream", "Ресурсы контейнеров"),
    ]),
    (["ip", "адрес", "сеть", "network", "интерфейс"],
     "linux", [
        ("ip addr", "IP-адреса"),
        ("ip route", "Маршруты"),
        ("curl -s ifconfig.me", "Внешний IP"),
        ("cat /etc/resolv.conf", "DNS-серверы"),
        ("ping -c 4 8.8.8.8", "Пинг Google"),
    ]),
    (["ip", "адрес", "сеть", "интерфейс"],
     "keenetic", [
        ("show interface", "Все интерфейсы"),
        ("show ip route", "Маршруты"),
        ("show ip hotspot", "Подключённые устройства"),
        ("show internet status", "Статус интернета"),
    ]),
    (["vpn", "wireguard", "openvpn", "туннель"],
     "keenetic", [
        ("show interface Wireguard0", "WireGuard статус"),
        ("show interface OpenVPN0", "OpenVPN статус"),
        ("show vpn-server", "VPN-сервер"),
        ("show crypto ipsec sa", "IPsec-туннели"),
    ]),
    (["wifi", "wi-fi", "вайфай", "беспроводн"],
     "keenetic", [
        ("show associations", "Клиенты Wi-Fi"),
        ("show interface WifiMaster0", "Wi-Fi 2.4 ГГц"),
        ("show interface WifiMaster1", "Wi-Fi 5 ГГц"),
        ("interface WifiMaster0 down", "Выключить 2.4"),
        ("interface WifiMaster0 up", "Включить 2.4"),
    ]),
    (["dhcp", "аренда", "lease"],
     "keenetic", [
        ("show ip dhcp bindings", "DHCP-аренды"),
        ("show ip dhcp pool", "DHCP-пулы"),
    ]),
    (["dns", "днс", "resolve"],
     "linux", [
        ("dig google.com +short", "DNS-запрос"),
        ("nslookup google.com", "nslookup"),
        ("cat /etc/resolv.conf", "DNS-серверы"),
        ("systemd-resolve --status | head -20", "systemd-resolved статус"),
    ]),
    (["прошивка", "firmware", "обновить роутер"],
     "keenetic", [
        ("show version", "Текущая прошивка"),
        ("tools firmware check", "Проверить обновления"),
        ("tools firmware upgrade", "Обновить прошивку"),
        ("show components", "Компоненты"),
    ]),
    (["сохранить", "save", "конфиг", "config"],
     "keenetic", [
        ("system configuration save", "Сохранить конфигурацию"),
        ("show running-config", "Текущая конфигурация"),
        ("copy running-config startup-config", "Применить конфиг"),
    ]),
    (["cron", "расписание", "schedule", "автоматически"],
     "linux", [
        ("crontab -l", "Показать задачи cron"),
        ("crontab -e", "Редактировать cron"),
        ("systemctl list-timers", "Systemd-таймеры"),
        ("echo '0 3 * * * /path/script.sh' | crontab -", "Запуск каждый день в 3:00"),
    ]),
    (["nginx", "веб-сервер", "apache", "сайт"],
     "linux", [
        ("sudo systemctl status nginx", "Статус nginx"),
        ("sudo nginx -t", "Проверить конфиг nginx"),
        ("sudo systemctl reload nginx", "Перечитать конфиг"),
        ("tail -f /var/log/nginx/error.log", "Ошибки nginx (live)"),
        ("tail -f /var/log/nginx/access.log", "Доступ nginx (live)"),
    ]),
    (["ssl", "сертификат", "certbot", "https", "let's encrypt"],
     "linux", [
        ("sudo certbot --nginx -d domain.com", "Получить SSL (nginx)"),
        ("sudo certbot renew --dry-run", "Тест обновления сертов"),
        ("sudo certbot certificates", "Список сертификатов"),
        ("openssl x509 -in cert.pem -noout -dates", "Срок действия серта"),
    ]),
    (["процесс", "process", "kill", "убить", "завис"],
     "linux", [
        ("ps aux | grep process_name", "Найти процесс"),
        ("kill -9 PID", "Убить по PID"),
        ("pkill -f process_name", "Убить по имени"),
        ("top -bn1 | head -20", "Топ процессов"),
        ("htop", "Интерактивный мониторинг"),
    ]),
]

AI_SYSTEM_PROMPT = """Ты — SSH-ассистент в программе PCA SSH. Помогай пользователю командами для Linux (Ubuntu/Debian/CentOS) и Keenetic роутеров (NDMS CLI).

Правила:
1. Отвечай ТОЛЬКО командами с кратким описанием
2. Формат ответа — каждая команда на новой строке: КОМАНДА — описание
3. Максимум 8 команд в ответе
4. Указывай платформу: [linux] или [keenetic]
5. Если вопрос про роутер/кинетик — давай команды NDMS CLI
6. Если вопрос про сервер/линукс — давай bash-команды
7. Отвечай по-русски
8. Не добавляй лишних пояснений, только команды"""


def agent_search(query):
    query_lower = query.lower()
    results = []
    seen = set()
    for keywords, platform, cmds in AGENT_KB:
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            for cmd, desc in cmds:
                if cmd not in seen:
                    results.append((score, platform, cmd, desc))
                    seen.add(cmd)
    results.sort(key=lambda x: -x[0])
    return results[:12]


def setup_entry_clipboard(entry):
    """Fix clipboard on macOS (Tk 8.6 maps <<Paste>> to Mod1 not Command)
    and add right-click context menu."""

    def _paste(e=None):
        try:
            text = entry.clipboard_get()
            if entry.selection_present():
                entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            entry.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return "break"

    def _copy(e=None):
        if entry.selection_present():
            entry.clipboard_clear()
            entry.clipboard_append(entry.selection_get())
        return "break"

    def _cut(e=None):
        _copy()
        if entry.selection_present():
            entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
        return "break"

    def _select_all(e=None):
        entry.select_range(0, tk.END)
        entry.icursor(tk.END)
        return "break"

    def _context_menu(event):
        menu = tk.Menu(entry, tearoff=0, bg="#313244", fg="#cdd6f4",
                       activebackground="#45475a")
        menu.add_command(label="Вырезать", command=_cut)
        menu.add_command(label="Копировать", command=_copy)
        menu.add_command(label="Вставить", command=_paste)
        menu.add_separator()
        menu.add_command(label="Выделить всё", command=_select_all)
        menu.tk_popup(event.x_root, event.y_root)

    if sys.platform == "darwin":
        # macOS Tk 8.6 bug: <<Paste>> bound to Mod1 (Option) not Command
        # Manually bind Command+key for clipboard operations
        entry.bind("<Command-v>", _paste)
        entry.bind("<Command-c>", _copy)
        entry.bind("<Command-x>", _cut)
        entry.bind("<Command-a>", _select_all)
        # Right-click
        entry.bind("<Button-2>", _context_menu)
        entry.bind("<Control-Button-1>", _context_menu)

    entry.bind("<Button-3>", _context_menu)


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


SESSIONS_FILE = app_dir() / "sessions.json"
CONFIG_FILE = app_dir() / "pca_config.json"


# ── Config Store ──────────────────────────────────────────────

class ConfigStore:
    def __init__(self, path=CONFIG_FILE):
        self.path = Path(path)
        self.data = {
            "ai_provider": "local",
            "claude_api_key": "",
            "deepseek_api_key": "",
            "commands_visible": True,
        }
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text("utf-8")))
            except Exception:
                pass

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), "utf-8")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()


# ── Session Store ──────────────────────────────────────────────

class SessionStore:
    def __init__(self, path=SESSIONS_FILE):
        self.path = Path(path)
        self.data = {"groups": [], "sessions": []}
        self.load()

    @property
    def sessions(self):
        return self.data["sessions"]

    @property
    def groups(self):
        return self.data["groups"]

    def load(self):
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text("utf-8"))
                if isinstance(raw, list):
                    self.data = {"groups": ["Без группы"], "sessions": []}
                    for s in raw:
                        s.setdefault("group", "Без группы")
                        self.data["sessions"].append(s)
                    self.save()
                else:
                    self.data = raw
                    self.data.setdefault("groups", [])
                    self.data.setdefault("sessions", [])
            except Exception:
                self.data = {"groups": [], "sessions": []}

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), "utf-8")

    def add_group(self, name):
        if name and name not in self.groups:
            self.groups.append(name)
            self.save()

    def rename_group(self, old_name, new_name):
        if old_name in self.groups and new_name:
            idx = self.groups.index(old_name)
            self.groups[idx] = new_name
            for s in self.sessions:
                if s.get("group") == old_name:
                    s["group"] = new_name
            self.save()

    def remove_group(self, name):
        if name in self.groups:
            self.groups.remove(name)
            for s in self.sessions:
                if s.get("group") == name:
                    s["group"] = ""
            self.save()

    def add(self, host, port, user, password, name=None, group=""):
        for s in self.sessions:
            if s["host"] == host and s["port"] == port and s["user"] == user:
                s["password"] = self._encode(password)
                s["last_used"] = datetime.now().isoformat()
                if name:
                    s["name"] = name
                if group:
                    s["group"] = group
                self.save()
                return s
        entry = {
            "name": name or f"{user}@{host}",
            "host": host,
            "port": port,
            "user": user,
            "password": self._encode(password),
            "group": group,
            "created": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
        }
        self.sessions.append(entry)
        if group and group not in self.groups:
            self.groups.append(group)
        self.save()
        return entry

    def remove(self, index):
        if 0 <= index < len(self.sessions):
            self.sessions.pop(index)
            self.save()

    def update(self, index, **kwargs):
        if 0 <= index < len(self.sessions):
            if "password" in kwargs:
                kwargs["password"] = self._encode(kwargs["password"])
            self.sessions[index].update(kwargs)
            self.save()

    def move_to_group(self, index, group):
        if 0 <= index < len(self.sessions):
            self.sessions[index]["group"] = group
            self.save()

    def get_password(self, session):
        return self._decode(session.get("password", ""))

    @staticmethod
    def _encode(pw):
        if not pw:
            return ""
        return base64.b64encode(pw.encode()).decode()

    @staticmethod
    def _decode(encoded):
        if not encoded:
            return ""
        try:
            return base64.b64decode(encoded.encode()).decode()
        except Exception:
            return encoded


# ── ANSI Parser ────────────────────────────────────────────────

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]|\x1b\[[\?]?[0-9;]*[hlmJKHfGr]")


def strip_ansi(text):
    return ANSI_RE.sub("", text)


# ── SSH Terminal Widget ────────────────────────────────────────

class TerminalWidget(tk.Frame):
    def __init__(self, master, on_close=None, **kw):
        super().__init__(master, **kw)
        self.on_close = on_close
        self.channel = None
        self.ssh = None
        self.read_thread = None
        self.running = False

        self.text = tk.Text(
            self,
            bg="#1e1e2e",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            selectbackground="#45475a",
            font=("Consolas", 11),
            wrap=tk.CHAR,
            padx=6,
            pady=6,
            borderwidth=0,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(fill=tk.BOTH, expand=True)

        self.text.bind("<Key>", self._on_key)
        self.text.bind("<Return>", lambda e: self._send("\r"))
        self.text.bind("<BackSpace>", lambda e: self._send("\x7f"))
        self.text.bind("<Tab>", lambda e: self._send("\t"))
        self.text.bind("<Up>", lambda e: self._send("\x1b[A"))
        self.text.bind("<Down>", lambda e: self._send("\x1b[B"))
        self.text.bind("<Right>", lambda e: self._send("\x1b[C"))
        self.text.bind("<Left>", lambda e: self._send("\x1b[D"))
        self.text.bind("<Home>", lambda e: self._send("\x1b[H"))
        self.text.bind("<End>", lambda e: self._send("\x1b[F"))
        self.text.bind("<Delete>", lambda e: self._send("\x1b[3~"))
        self.text.bind("<Control-c>", lambda e: self._send("\x03"))
        self.text.bind("<Control-d>", lambda e: self._send("\x04"))
        self.text.bind("<Control-l>", lambda e: self._send("\x0c"))
        self.text.bind("<Control-z>", lambda e: self._send("\x1a"))
        # Paste/Copy in terminal: send clipboard to SSH / copy selection
        if sys.platform == "darwin":
            self.text.bind("<Command-v>", self._term_paste)
            self.text.bind("<Command-c>", self._term_copy)
        else:
            # Windows/Linux: Ctrl+V paste, Ctrl+Shift+C copy
            self.text.bind("<Control-v>", self._term_paste)
            self.text.bind("<Control-Shift-C>", self._term_copy)

        self.text.tag_configure("error", foreground="#f38ba8")
        self.text.tag_configure("info", foreground="#89b4fa")

    def connect(self, host, port, user, password):
        self.running = True
        self._write(f"Подключение к {user}@{host}:{port}...\n", "info")
        t = threading.Thread(target=self._connect_thread, args=(host, port, user, password), daemon=True)
        t.start()

    def _connect_thread(self, host, port, user, password):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                host, port=port, username=user, password=password,
                timeout=10, look_for_keys=False, allow_agent=False,
            )
            cols = max(80, self.text.winfo_width() // 8)
            rows = max(24, self.text.winfo_height() // 16)
            self.channel = self.ssh.invoke_shell(
                term="xterm-256color", width=cols, height=rows
            )
            self.channel.settimeout(0.1)
            self._write("Подключено!\n", "info")
            self._read_loop()
        except Exception as ex:
            self._write(f"\nОшибка: {ex}\n", "error")
            self.running = False
            if self.on_close:
                self.after(100, self.on_close)

    def _read_loop(self):
        while self.running and self.channel and not self.channel.closed:
            try:
                data = self.channel.recv(4096)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace")
                clean = strip_ansi(text)
                # Remove control chars except \n \t \x08 \x7f (handled by _write)
                clean = "".join(
                    ch for ch in clean
                    if ch in "\n\t\x08\x7f" or ord(ch) >= 32
                )
                self._write(clean)
            except socket.timeout:
                continue
            except Exception:
                break
        self._write("\n--- Сессия завершена ---\n", "error")
        self.running = False
        if self.on_close:
            self.after(100, self.on_close)

    def _write(self, text, tag=None):
        # Strip \r before closure (SSH sends \r\n)
        clean = text.replace("\r", "") if not tag else text

        def _do():
            self.text.configure(state=tk.NORMAL)
            if tag:
                self.text.insert(tk.END, clean, tag)
            elif "\x08" not in clean and "\x7f" not in clean:
                # Fast path: no backspace chars
                self.text.insert(tk.END, clean)
            else:
                # Handle backspace/DEL char by char
                buf = []
                for ch in clean:
                    if ch == "\x08" or ch == "\x7f":
                        if buf:
                            self.text.insert(tk.END, "".join(buf))
                            buf.clear()
                        pos = self.text.index(tk.END + "-2c")
                        if self.text.compare(pos, ">", "1.0"):
                            self.text.delete(pos)
                    else:
                        buf.append(ch)
                if buf:
                    self.text.insert(tk.END, "".join(buf))
            self.text.see(tk.END)
        self.after(0, _do)

    def _send(self, data):
        if self.channel and not self.channel.closed:
            try:
                self.channel.send(data.encode() if isinstance(data, str) else data)
            except Exception:
                pass
        return "break"

    def _term_paste(self, event=None):
        """Paste clipboard into SSH terminal (send text to remote)."""
        try:
            text = self.text.clipboard_get()
            if text:
                self._send(text)
        except tk.TclError:
            pass
        return "break"

    def _term_copy(self, event=None):
        """Copy selected text from terminal."""
        try:
            if self.text.tag_ranges(tk.SEL):
                self.text.clipboard_clear()
                self.text.clipboard_append(self.text.get(tk.SEL_FIRST, tk.SEL_LAST))
        except tk.TclError:
            pass
        return "break"

    def _on_key(self, event):
        if event.state & 4:  # Ctrl
            return
        if event.state & 8:  # Mod1 / Command on macOS — let bindings handle it
            return
        if event.char and ord(event.char) >= 32:
            self._send(event.char)
            return "break"
        return "break"

    def disconnect(self):
        self.running = False
        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass
        if self.ssh:
            try:
                self.ssh.close()
            except Exception:
                pass


# ── Session Edit Dialog ────────────────────────────────────────

class SessionDialog(tk.Toplevel):
    def __init__(self, parent, title="Сессия", session=None, groups=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.grab_set()

        frame = tk.Frame(self, bg="#1e1e2e", padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("Название:", "name", session.get("name", "") if session else ""),
            ("Описание:", "description", session.get("description", "") if session else ""),
            ("Хост:", "host", session.get("host", "") if session else ""),
            ("Порт:", "port", str(session.get("port", 22)) if session else "22"),
            ("Пользователь:", "user", session.get("user", "") if session else "root"),
            ("Пароль:", "password", ""),
        ]

        self.entries = {}
        for i, (label, key, default) in enumerate(fields):
            tk.Label(frame, text=label, bg="#1e1e2e", fg="#cdd6f4",
                     font=("Consolas", 10)).grid(row=i, column=0, sticky="w", pady=3)
            entry = tk.Entry(frame, width=35, bg="#313244", fg="#cdd6f4",
                             insertbackground="#cdd6f4", relief=tk.FLAT,
                             font=("Consolas", 10))
            if key == "password":
                entry.configure(show="*")
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky="ew", pady=3, padx=(8, 0))
            setup_entry_clipboard(entry)
            self.entries[key] = entry

        row_group = len(fields)
        tk.Label(frame, text="Группа:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Consolas", 10)).grid(row=row_group, column=0, sticky="w", pady=3)
        group_frame = tk.Frame(frame, bg="#1e1e2e")
        group_frame.grid(row=row_group, column=1, sticky="ew", pady=3, padx=(8, 0))

        group_values = groups or []
        current_group = session.get("group", "") if session else ""
        self.group_var = tk.StringVar(value=current_group)
        self.group_combo = ttk.Combobox(group_frame, textvariable=self.group_var,
                                         values=group_values, width=20)
        self.group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_frame = tk.Frame(frame, bg="#1e1e2e")
        btn_frame.grid(row=row_group + 1, column=0, columnspan=2, pady=(12, 0))

        ok_btn = tk.Button(btn_frame, text="OK", bg="#45475a", fg="#cdd6f4",
                           activebackground="#585b70", relief=tk.FLAT,
                           font=("Consolas", 10), padx=20, pady=4, command=self._ok)
        ok_btn.pack(side=tk.LEFT, padx=4)
        cancel_btn = tk.Button(btn_frame, text="Отмена", bg="#45475a", fg="#cdd6f4",
                               activebackground="#585b70", relief=tk.FLAT,
                               font=("Consolas", 10), padx=20, pady=4, command=self.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=4)

        self.entries["host"].focus_set()
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_window()

    def _ok(self):
        host = self.entries["host"].get().strip()
        if not host:
            messagebox.showwarning("Ошибка", "Хост обязателен", parent=self)
            return
        try:
            port = int(self.entries["port"].get().strip() or "22")
        except ValueError:
            messagebox.showwarning("Ошибка", "Порт — число", parent=self)
            return
        self.result = {
            "name": self.entries["name"].get().strip() or f"{self.entries['user'].get()}@{host}",
            "description": self.entries["description"].get().strip(),
            "host": host,
            "port": port,
            "user": self.entries["user"].get().strip() or "root",
            "password": self.entries["password"].get(),
            "group": self.group_var.get().strip(),
        }
        self.destroy()


# ── AI Agent Settings Dialog ──────────────────────────────────

class AISettingsDialog(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.title("Настройки AI-агента")
        self.config = config
        self.result = None
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.grab_set()

        frame = tk.Frame(self, bg="#1e1e2e", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="AI-провайдер", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Consolas", 12, "bold")).pack(anchor="w", pady=(0, 10))

        self.provider_var = tk.StringVar(value=config.get("ai_provider", "local"))

        providers = [
            ("local", "Локальная база (без API)"),
            ("claude", "Claude API (Anthropic)"),
            ("deepseek", "DeepSeek API"),
        ]
        for val, label in providers:
            rb = tk.Radiobutton(
                frame, text=label, variable=self.provider_var, value=val,
                bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244",
                activebackground="#1e1e2e", activeforeground="#cdd6f4",
                font=("Consolas", 10),
            )
            rb.pack(anchor="w", pady=2)

        tk.Frame(frame, bg="#45475a", height=1).pack(fill=tk.X, pady=10)

        tk.Label(frame, text="Claude API Key:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Consolas", 10)).pack(anchor="w")
        self.claude_key = tk.Entry(frame, width=50, bg="#313244", fg="#cdd6f4",
                                   insertbackground="#cdd6f4", relief=tk.FLAT,
                                   font=("Consolas", 9), show="*")
        self.claude_key.insert(0, config.get("claude_api_key", ""))
        self.claude_key.pack(fill=tk.X, pady=(2, 8))
        setup_entry_clipboard(self.claude_key)

        tk.Label(frame, text="DeepSeek API Key:", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Consolas", 10)).pack(anchor="w")
        self.deepseek_key = tk.Entry(frame, width=50, bg="#313244", fg="#cdd6f4",
                                      insertbackground="#cdd6f4", relief=tk.FLAT,
                                      font=("Consolas", 9), show="*")
        self.deepseek_key.insert(0, config.get("deepseek_api_key", ""))
        self.deepseek_key.pack(fill=tk.X, pady=(2, 12))
        setup_entry_clipboard(self.deepseek_key)

        btn_frame = tk.Frame(frame, bg="#1e1e2e")
        btn_frame.pack()
        tk.Button(btn_frame, text="Сохранить", bg="#89b4fa", fg="#1e1e2e",
                  activebackground="#6c8fff", relief=tk.FLAT,
                  font=("Consolas", 10, "bold"), padx=20, pady=4,
                  command=self._save).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Отмена", bg="#45475a", fg="#cdd6f4",
                  activebackground="#585b70", relief=tk.FLAT,
                  font=("Consolas", 10), padx=20, pady=4,
                  command=self.destroy).pack(side=tk.LEFT, padx=4)

        self.wait_window()

    def _save(self):
        self.result = {
            "ai_provider": self.provider_var.get(),
            "claude_api_key": self.claude_key.get().strip(),
            "deepseek_api_key": self.deepseek_key.get().strip(),
        }
        self.destroy()


# ── AI API Caller ─────────────────────────────────────────────

def _ssl_context():
    """Create SSL context — skip verify on Windows/frozen (often missing certs)."""
    if sys.platform == "win32" or getattr(sys, "frozen", False):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None  # use default on macOS/Linux


def call_claude_api(api_key, query):
    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "system": AI_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": query}],
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")

    ctx = _ssl_context()
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    data = json.loads(resp.read().decode("utf-8"))
    text = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            text += block["text"]
    return text


def call_deepseek_api(api_key, query):
    url = "https://api.deepseek.com/v1/chat/completions"
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        "max_tokens": 1024,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    ctx = _ssl_context()
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    data = json.loads(resp.read().decode("utf-8"))
    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


# ── SFTP File Manager Widget ──────────────────────────────────

class FileManagerWidget(tk.Frame):
    """SFTP file browser with upload/download, context menu, and clipboard."""

    def __init__(self, master, ssh_client, on_send_cmd=None, **kw):
        super().__init__(master, bg="#1e1e2e", **kw)
        self.ssh = ssh_client
        self.sftp = None
        self.cwd = "/"
        self._clipboard = None  # (mode, path) where mode = "copy" or "cut"
        self._on_send_cmd = on_send_cmd  # callback to send command to terminal

        self._build_ui()
        self._connect_sftp()

    def _build_ui(self):
        bg, fg = "#1e1e2e", "#cdd6f4"

        # Toolbar
        toolbar = tk.Frame(self, bg="#181825")
        toolbar.pack(fill=tk.X)

        btn_s = {"bg": "#313244", "fg": "#89b4fa", "activebackground": "#45475a",
                 "relief": tk.FLAT, "font": ("Consolas", 9), "padx": 4, "pady": 2}

        tk.Button(toolbar, text="⬆ Вверх", command=self._go_up, **btn_s).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="⟳ Обновить", command=self._refresh, **btn_s).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="📁 Создать папку", command=self._mkdir, **btn_s).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="⬆ Загрузить", command=self._upload, **btn_s).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="⬇ Скачать", command=self._download, **btn_s).pack(side=tk.LEFT, padx=2, pady=2)

        # Path bar
        path_frame = tk.Frame(self, bg=bg)
        path_frame.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(path_frame, text="Путь:", bg=bg, fg="#6c7086",
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value="/")
        self.path_entry = tk.Entry(path_frame, textvariable=self.path_var,
                                    bg="#313244", fg=fg, insertbackground=fg,
                                    relief=tk.FLAT, font=("Consolas", 9))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.path_entry.bind("<Return>", lambda e: self._navigate(self.path_var.get()))
        setup_entry_clipboard(self.path_entry)

        tk.Button(path_frame, text="→", command=lambda: self._navigate(self.path_var.get()),
                  **btn_s).pack(side=tk.RIGHT)

        # File tree
        tree_frame = tk.Frame(self, bg=bg)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        cols = ("size", "modified", "perms")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings",
                                  selectmode="browse")
        self.tree.heading("#0", text="Имя")
        self.tree.heading("size", text="Размер")
        self.tree.heading("modified", text="Изменён")
        self.tree.heading("perms", text="Права")
        self.tree.column("#0", width=250, minwidth=150)
        self.tree.column("size", width=80, minwidth=60)
        self.tree.column("modified", width=140, minwidth=100)
        self.tree.column("perms", width=80, minwidth=60)

        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._context_menu)
        if sys.platform == "darwin":
            self.tree.bind("<Button-2>", self._context_menu)
            self.tree.bind("<Control-Button-1>", self._context_menu)

        # Status bar
        self.status_var = tk.StringVar(value="Подключение...")
        tk.Label(self, textvariable=self.status_var, bg="#181825", fg="#6c7086",
                 font=("Consolas", 8), anchor=tk.W).pack(fill=tk.X, padx=4)

        # Close button
        close_frame = tk.Frame(self, bg=bg)
        close_frame.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(close_frame, text="✕ Закрыть вкладку",
                  bg="#313244", fg="#cdd6f4", activebackground="#45475a",
                  relief=tk.FLAT, font=("Consolas", 9), padx=6, pady=2,
                  command=self._close).pack(side=tk.RIGHT, padx=4, pady=2)

    def _connect_sftp(self):
        def _do():
            try:
                self.sftp = self.ssh.open_sftp()
                self.cwd = self.sftp.normalize(".")
                self.after(0, self._refresh)
                self.after(0, lambda: self.status_var.set(f"SFTP подключён: {self.cwd}"))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка SFTP: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _refresh(self):
        if not self.sftp:
            return
        self.tree.delete(*self.tree.get_children())
        self.path_var.set(self.cwd)

        def _load():
            try:
                items = self.sftp.listdir_attr(self.cwd)
                # Sort: dirs first, then by name
                dirs = sorted([f for f in items if stat.S_ISDIR(f.st_mode)],
                              key=lambda f: f.filename.lower())
                files = sorted([f for f in items if not stat.S_ISDIR(f.st_mode)],
                               key=lambda f: f.filename.lower())
                self.after(0, lambda: self._populate(dirs + files))
                self.after(0, lambda: self.status_var.set(
                    f"{self.cwd} — {len(dirs)} папок, {len(files)} файлов"))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))

        threading.Thread(target=_load, daemon=True).start()

    def _populate(self, items):
        for f in items:
            is_dir = stat.S_ISDIR(f.st_mode)
            icon = "📁" if is_dir else "📄"
            name = f"{icon} {f.filename}"
            size = "" if is_dir else self._human_size(f.st_size)
            mtime = datetime.fromtimestamp(f.st_mtime).strftime("%Y-%m-%d %H:%M")
            perms = stat.filemode(f.st_mode)
            self.tree.insert("", tk.END, text=name, values=(size, mtime, perms),
                             tags=("dir" if is_dir else "file",))

        self.tree.tag_configure("dir", foreground="#89b4fa")
        self.tree.tag_configure("file", foreground="#cdd6f4")

    @staticmethod
    def _human_size(n):
        for unit in ("Б", "КБ", "МБ", "ГБ"):
            if n < 1024:
                return f"{n:.0f} {unit}" if n == int(n) else f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} ТБ"

    def _get_selected_name(self):
        sel = self.tree.selection()
        if not sel:
            return None
        text = self.tree.item(sel[0], "text")
        # Remove icon prefix
        return text.split(" ", 1)[1] if " " in text else text

    def _get_selected_path(self):
        name = self._get_selected_name()
        if not name:
            return None
        return self.cwd.rstrip("/") + "/" + name

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        tags = self.tree.item(sel[0], "tags")
        if "dir" in tags:
            name = self._get_selected_name()
            self._navigate(self.cwd.rstrip("/") + "/" + name)

    def _navigate(self, path):
        def _do():
            try:
                resolved = self.sftp.normalize(path)
                self.sftp.listdir(resolved)  # test access
                self.cwd = resolved
                self.after(0, self._refresh)
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _go_up(self):
        parent = "/".join(self.cwd.rstrip("/").split("/")[:-1]) or "/"
        self._navigate(parent)

    def _mkdir(self):
        name = simpledialog.askstring("Новая папка", "Имя:", parent=self)
        if name and name.strip():
            def _do():
                try:
                    self.sftp.mkdir(self.cwd.rstrip("/") + "/" + name.strip())
                    self.after(0, self._refresh)
                except Exception as e:
                    self.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))
            threading.Thread(target=_do, daemon=True).start()

    def _upload(self):
        local_path = filedialog.askopenfilename(parent=self, title="Выбрать файл для загрузки")
        if not local_path:
            return
        fname = os.path.basename(local_path)
        remote_path = self.cwd.rstrip("/") + "/" + fname
        self.status_var.set(f"Загрузка {fname}...")

        def _do():
            try:
                self.sftp.put(local_path, remote_path)
                self.after(0, self._refresh)
                self.after(0, lambda: self.status_var.set(f"Загружен: {fname}"))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка загрузки: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _download(self):
        remote = self._get_selected_path()
        if not remote:
            return
        fname = os.path.basename(remote)
        local = filedialog.asksaveasfilename(parent=self, title="Сохранить как",
                                              initialfile=fname)
        if not local:
            return
        self.status_var.set(f"Скачивание {fname}...")

        def _do():
            try:
                self.sftp.get(remote, local)
                self.after(0, lambda: self.status_var.set(f"Скачан: {local}"))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка скачивания: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _delete_selected(self):
        path = self._get_selected_path()
        if not path:
            return
        sel = self.tree.selection()
        tags = self.tree.item(sel[0], "tags") if sel else ()
        name = self._get_selected_name()
        if not messagebox.askyesno("Удалить?", f"Удалить «{name}»?", parent=self):
            return

        def _do():
            try:
                if "dir" in tags:
                    self.sftp.rmdir(path)
                else:
                    self.sftp.remove(path)
                self.after(0, self._refresh)
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка удаления: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _copy_path(self):
        path = self._get_selected_path()
        if path:
            self.clipboard_clear()
            self.clipboard_append(path)
            self.status_var.set(f"Скопирован путь: {path}")

    def _copy_file(self):
        path = self._get_selected_path()
        if path:
            self._clipboard = ("copy", path)
            self.status_var.set(f"Копировать: {path}")

    def _cut_file(self):
        path = self._get_selected_path()
        if path:
            self._clipboard = ("cut", path)
            self.status_var.set(f"Вырезать: {path}")

    def _paste_file(self):
        if not self._clipboard:
            return
        mode, src = self._clipboard
        fname = os.path.basename(src)
        dst = self.cwd.rstrip("/") + "/" + fname
        self.status_var.set(f"{'Перемещение' if mode == 'cut' else 'Копирование'} {fname}...")

        def _do():
            try:
                if mode == "cut":
                    self.sftp.rename(src, dst)
                else:
                    # Copy via SSH cp command
                    transport = self.ssh.get_transport()
                    chan = transport.open_session()
                    chan.exec_command(f'cp -r "{src}" "{dst}"')
                    chan.recv_exit_status()
                    chan.close()
                self._clipboard = None
                self.after(0, self._refresh)
                self.after(0, lambda: self.status_var.set(f"Готово: {dst}"))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _rename_selected(self):
        path = self._get_selected_path()
        name = self._get_selected_name()
        if not path:
            return
        new_name = simpledialog.askstring("Переименовать", "Новое имя:", parent=self,
                                           initialvalue=name)
        if new_name and new_name.strip() and new_name != name:
            dst = self.cwd.rstrip("/") + "/" + new_name.strip()
            def _do():
                try:
                    self.sftp.rename(path, dst)
                    self.after(0, self._refresh)
                except Exception as e:
                    self.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))
            threading.Thread(target=_do, daemon=True).start()

    def _send_to_terminal(self):
        """Send selected file path to terminal for AI/command use."""
        path = self._get_selected_path()
        if path and self._on_send_cmd:
            self._on_send_cmd(path)

    def _context_menu(self, event):
        sel = self.tree.identify_row(event.y)
        if sel:
            self.tree.selection_set(sel)

        menu = tk.Menu(self, tearoff=0, bg="#313244", fg="#cdd6f4",
                       activebackground="#45475a")
        if sel:
            tags = self.tree.item(sel, "tags")
            if "dir" in tags:
                menu.add_command(label="📂 Открыть", command=lambda: self._on_double_click(None))
            else:
                menu.add_command(label="⬇ Скачать", command=self._download)
            menu.add_separator()
            menu.add_command(label="📋 Копировать путь", command=self._copy_path)
            menu.add_command(label="📄 Копировать", command=self._copy_file)
            menu.add_command(label="✂ Вырезать", command=self._cut_file)
            menu.add_command(label="✏ Переименовать", command=self._rename_selected)
            menu.add_command(label="🗑 Удалить", command=self._delete_selected)
            menu.add_separator()
            menu.add_command(label="➜ В терминал", command=self._send_to_terminal)
        if self._clipboard:
            menu.add_command(label="📋 Вставить", command=self._paste_file)
        menu.add_separator()
        menu.add_command(label="📁 Создать папку", command=self._mkdir)
        menu.add_command(label="⬆ Загрузить файл", command=self._upload)
        menu.tk_popup(event.x_root, event.y_root)

    def download_file(self, remote_path, local_path=None):
        """API method for AI agent to download a file."""
        if not local_path:
            fname = os.path.basename(remote_path)
            desktop = str(Path.home() / "Desktop")
            local_path = os.path.join(desktop, fname)
        self.status_var.set(f"AI: скачивание {remote_path}...")

        def _do():
            try:
                self.sftp.get(remote_path, local_path)
                self.after(0, lambda: self.status_var.set(f"AI: скачан → {local_path}"))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _close(self):
        if self.sftp:
            try:
                self.sftp.close()
            except Exception:
                pass
        # Find parent notebook and remove this tab
        parent = self.master
        if isinstance(parent, ttk.Notebook):
            parent.forget(self)
        self.destroy()


# ── Main Application ───────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — {APP_SUBTITLE} v{VERSION}")
        self.geometry("1200x750")
        self.minsize(900, 550)
        self.configure(bg="#1e1e2e")

        self.store = SessionStore()
        self.config = ConfigStore()
        self.terminals = {}
        self._commands_visible = self.config.get("commands_visible", True)
        self._selected_card_idx = None

        self._font_size = self.config.get("font_size", 10)
        self._apply_theme()
        self._build_ui()
        self._refresh_cards()

        # Zoom: Cmd+/- (Mac) or Ctrl+/- (Windows)
        if sys.platform == "darwin":
            self.bind("<Command-equal>", lambda e: self._zoom(1))
            self.bind("<Command-minus>", lambda e: self._zoom(-1))
            self.bind("<Command-0>", lambda e: self._zoom(0))
        else:
            self.bind("<Control-equal>", lambda e: self._zoom(1))
            self.bind("<Control-minus>", lambda e: self._zoom(-1))
            self.bind("<Control-0>", lambda e: self._zoom(0))

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        bg = "#1e1e2e"
        fg = "#cdd6f4"

        style.configure(".", background=bg, foreground=fg, fieldbackground="#313244", borderwidth=0)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background="#45475a", foreground=fg, padding=(10, 5))
        style.map("TButton", background=[("active", "#585b70")])
        style.configure("Treeview", background="#313244", foreground=fg, fieldbackground="#313244",
                         rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background="#45475a", foreground=fg)
        style.map("Treeview", background=[("selected", "#45475a")])
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background="#45475a", foreground=fg, padding=(12, 6))
        style.map("TNotebook.Tab", background=[("selected", "#585b70")])
        style.configure("TEntry", fieldbackground="#313244", foreground=fg)
        style.configure("TCombobox", fieldbackground="#313244", foreground=fg)

    def _zoom(self, delta):
        """Change font size. delta=+1/-1 or 0 to reset."""
        if delta == 0:
            self._font_size = 10
        else:
            self._font_size = max(7, min(18, self._font_size + delta))
        self.config.set("font_size", self._font_size)
        s = self._font_size
        # Update all text widgets
        for widget in self._all_widgets():
            try:
                f = widget.cget("font")
                if isinstance(f, str) and f:
                    widget.configure(font=(f, s))
                elif isinstance(f, tuple) and len(f) >= 2:
                    widget.configure(font=(f[0], s) + f[2:])
            except (tk.TclError, TypeError):
                pass
        # Update terminal tabs
        for term in self.terminals.values():
            try:
                term.text.configure(font=("Consolas", s))
            except (tk.TclError, AttributeError):
                pass

    def _all_widgets(self):
        """Yield all widgets recursively."""
        stack = [self]
        while stack:
            w = stack.pop()
            yield w
            try:
                stack.extend(w.winfo_children())
            except Exception:
                pass

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def _draw_pca_logo(self, canvas, cx, cy, size):
        r = size // 2
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#2a2a3d", outline="#3b3b5c", width=2)
        label_font = ("Arial", size // 3, "bold")
        canvas.create_text(cx, cy - 2, text="PCA", fill="#6c8fff", font=label_font)
        dots = [(cx - 4, cy + r // 2), (cx, cy + r // 2 + 4), (cx + 4, cy + r // 2),
                (cx - 6, cy + r // 2 + 6), (cx, cy + r // 2 + 10), (cx + 6, cy + r // 2 + 6)]
        for dx, dy in dots:
            canvas.create_oval(dx - 1, dy - 1, dx + 1, dy + 1, fill="#6c8fff", outline="")

    def _build_ui(self):
        # ── Top: PCA brand bar ──
        top_bar = tk.Frame(self, bg="#181825", height=48)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)

        logo_canvas = tk.Canvas(top_bar, width=36, height=36, bg="#181825", highlightthickness=0)
        logo_canvas.pack(side=tk.LEFT, padx=(10, 6), pady=6)
        self._draw_pca_logo(logo_canvas, 18, 16, 30)

        brand_frame = tk.Frame(top_bar, bg="#181825")
        brand_frame.pack(side=tk.LEFT, pady=4)
        tk.Label(brand_frame, text=APP_NAME, bg="#181825", fg="#cdd6f4",
                 font=("Consolas", 13, "bold")).pack(anchor="w")
        tk.Label(brand_frame, text=APP_SUBTITLE, bg="#181825", fg="#6c7086",
                 font=("Consolas", 9)).pack(anchor="w")

        tk.Frame(top_bar, bg="#45475a", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=12, pady=8)

        links = [
            ("GitHub", "https://github.com/nickolay-frolov"),
            ("Boosty", "https://boosty.to/lot_andrey"),
            ("Telegram", "https://t.me/lot_andrey"),
            ("Поддержать (СБП)", "https://finance.ozon.ru/apps/sbp/ozonbankpay/019dc200-2a5d-7931-a619-782d285f6798"),
        ]
        for i, (text, url) in enumerate(links):
            if i > 0:
                tk.Label(top_bar, text="·", bg="#181825", fg="#6c7086", font=("Consolas", 9)).pack(side=tk.LEFT)
            lnk = tk.Label(top_bar, text=text, bg="#181825", fg="#89b4fa",
                           font=("Consolas", 9, "underline"), cursor="hand2")
            lnk.pack(side=tk.LEFT, padx=6)
            lnk.bind("<Button-1>", lambda e, u=url: self._open_url(u))

        tk.Label(top_bar, text="@lot_andrey", bg="#181825", fg="#6c7086",
                 font=("Consolas", 9)).pack(side=tk.RIGHT, padx=10)

        # ── Main layout ──
        main_frame = tk.Frame(self, bg="#1e1e2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left: card-based session panel
        self.left_panel = tk.Frame(main_frame, bg="#1e1e2e", width=320)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 4))
        self.left_panel.pack_propagate(False)
        self._build_card_panel(self.left_panel)

        # Center: terminal tabs
        center_frame = tk.Frame(main_frame, bg="#1e1e2e")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(center_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Welcome tab
        welcome = tk.Frame(self.notebook, bg="#1e1e2e")
        self.notebook.add(welcome, text="Добро пожаловать")
        tk.Label(
            welcome,
            text=f"{APP_NAME} v{VERSION}\n\n"
                 "• Двойной клик по карточке = подключение\n"
                 "• Быстрое подключение внизу слева\n"
                 "• Все сессии сохраняются автоматически\n"
                 "• Ctrl+C/D/L работают в терминале\n"
                 "• AI-агент справа — спроси что угодно\n"
                 "• Панель команд можно скрыть/показать",
            font=("Consolas", 12),
            justify=tk.CENTER,
            bg="#1e1e2e",
            fg="#cdd6f4",
        ).pack(expand=True)

        # Right: commands + agent panel
        self.right_panel = tk.Frame(main_frame, bg="#1e1e2e", width=360)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, 0))
        self.right_panel.pack_propagate(False)
        self._build_right_panel(self.right_panel)

    # ── Card Panel (Left) ─────────────────────────────────────

    def _build_card_panel(self, parent):
        # Toolbar
        toolbar = tk.Frame(parent, bg="#181825")
        toolbar.pack(fill=tk.X)

        btn_style = {"bg": "#313244", "fg": "#89b4fa", "activebackground": "#45475a",
                     "activeforeground": "#b4d0fb", "relief": tk.FLAT,
                     "font": ("Consolas", 10), "padx": 8, "pady": 4}

        tk.Button(toolbar, text="＋ Сессия", command=self._new_session, **btn_style).pack(side=tk.LEFT, padx=2, pady=3)
        tk.Button(toolbar, text="＋ Группа", command=self._new_group, **btn_style).pack(side=tk.LEFT, padx=2, pady=3)
        tk.Button(toolbar, text="✎", command=self._edit_session, width=3, **btn_style).pack(side=tk.LEFT, padx=1, pady=3)
        tk.Button(toolbar, text="✕", command=self._delete_session, width=3, **btn_style).pack(side=tk.LEFT, padx=1, pady=3)

        # Scrollable card area
        self.card_canvas = tk.Canvas(parent, bg="#1e1e2e", highlightthickness=0)
        card_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.card_canvas.yview)
        self.card_canvas.configure(yscrollcommand=card_scroll.set)

        card_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.card_canvas.pack(fill=tk.BOTH, expand=True)

        self.card_inner = tk.Frame(self.card_canvas, bg="#1e1e2e")
        self.card_canvas_window = self.card_canvas.create_window((0, 0), window=self.card_inner, anchor="nw")

        self.card_inner.bind("<Configure>", lambda e: self.card_canvas.configure(
            scrollregion=self.card_canvas.bbox("all")))
        self.card_canvas.bind("<Configure>", lambda e: self.card_canvas.itemconfigure(
            self.card_canvas_window, width=e.width))

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            if sys.platform == "darwin":
                self.card_canvas.yview_scroll(-1 * event.delta, "units")
            else:
                self.card_canvas.yview_scroll(-1 * (event.delta // 120), "units")

        self.card_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.card_canvas.bind("<Button-4>", lambda e: self.card_canvas.yview_scroll(-1, "units"))
        self.card_canvas.bind("<Button-5>", lambda e: self.card_canvas.yview_scroll(1, "units"))

        # Quick connect at bottom
        qf = tk.Frame(parent, bg="#181825", padx=8, pady=8)
        qf.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(qf, text="Быстрое подключение", bg="#181825", fg="#6c7086",
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 4))

        row1 = tk.Frame(qf, bg="#181825")
        row1.pack(fill=tk.X, pady=1)
        tk.Label(row1, text="Хост:", bg="#181825", fg="#6c7086", font=("Consolas", 9)).pack(side=tk.LEFT)
        self.q_host = tk.Entry(row1, width=14, bg="#313244", fg="#cdd6f4",
                               insertbackground="#cdd6f4", relief=tk.FLAT, font=("Consolas", 9))
        self.q_host.pack(side=tk.LEFT, padx=(4, 6))
        setup_entry_clipboard(self.q_host)
        tk.Label(row1, text="Порт:", bg="#181825", fg="#6c7086", font=("Consolas", 9)).pack(side=tk.LEFT)
        self.q_port = tk.Entry(row1, width=5, bg="#313244", fg="#cdd6f4",
                               insertbackground="#cdd6f4", relief=tk.FLAT, font=("Consolas", 9))
        self.q_port.insert(0, "22")
        self.q_port.pack(side=tk.LEFT, padx=4)
        setup_entry_clipboard(self.q_port)

        row2 = tk.Frame(qf, bg="#181825")
        row2.pack(fill=tk.X, pady=1)
        tk.Label(row2, text="Юзер:", bg="#181825", fg="#6c7086", font=("Consolas", 9)).pack(side=tk.LEFT)
        self.q_user = tk.Entry(row2, width=10, bg="#313244", fg="#cdd6f4",
                               insertbackground="#cdd6f4", relief=tk.FLAT, font=("Consolas", 9))
        self.q_user.insert(0, "root")
        self.q_user.pack(side=tk.LEFT, padx=(4, 6))
        setup_entry_clipboard(self.q_user)
        tk.Label(row2, text="Пароль:", bg="#181825", fg="#6c7086", font=("Consolas", 9)).pack(side=tk.LEFT)
        self.q_pass = tk.Entry(row2, width=10, bg="#313244", fg="#cdd6f4", show="*",
                               insertbackground="#cdd6f4", relief=tk.FLAT, font=("Consolas", 9))
        self.q_pass.pack(side=tk.LEFT, padx=4)
        setup_entry_clipboard(self.q_pass)

        tk.Button(qf, text="Подключиться", bg="#89b4fa", fg="#1e1e2e",
                  activebackground="#6c8fff", relief=tk.FLAT,
                  font=("Consolas", 9, "bold"), pady=3,
                  command=self._quick_connect).pack(fill=tk.X, pady=(4, 0))
        self.q_host.bind("<Return>", lambda e: self._quick_connect())
        self.q_pass.bind("<Return>", lambda e: self._quick_connect())

    def _refresh_cards(self):
        for widget in self.card_inner.winfo_children():
            widget.destroy()

        grouped = {}
        ungrouped = []
        for i, s in enumerate(self.store.sessions):
            g = s.get("group", "")
            if g:
                grouped.setdefault(g, []).append((i, s))
            else:
                ungrouped.append((i, s))

        color_idx = 0

        # Grouped sessions
        for g in self.store.groups:
            color = CARD_COLORS[color_idx % len(CARD_COLORS)]
            color_idx += 1
            sessions = grouped.get(g, [])
            self._create_group_section(self.card_inner, g, sessions, color)

        # Extra groups from sessions
        for g, items in grouped.items():
            if g not in self.store.groups:
                self.store.add_group(g)
                color = CARD_COLORS[color_idx % len(CARD_COLORS)]
                color_idx += 1
                self._create_group_section(self.card_inner, g, items, color)

        # Ungrouped
        if ungrouped:
            self._create_group_section(self.card_inner, "Без группы", ungrouped, "#6c7086")

    def _create_group_section(self, parent, group_name, sessions, color):
        # Group container with colored left border
        group_frame = tk.Frame(parent, bg="#1e1e2e")
        group_frame.pack(fill=tk.X, padx=4, pady=(6, 2))

        # Group header
        header = tk.Frame(group_frame, bg="#181825")
        header.pack(fill=tk.X)

        # Color indicator
        tk.Frame(header, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(header, text=f"  {group_name}", bg="#181825", fg=color,
                 font=("Consolas", 11, "bold"), pady=6).pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="w")

        count_text = f"{len(sessions)}"
        tk.Label(header, text=count_text, bg="#181825", fg="#6c7086",
                 font=("Consolas", 9), padx=8).pack(side=tk.RIGHT)

        # Group context menu on header
        if group_name != "Без группы":
            def _group_menu(event, gn=group_name):
                menu = tk.Menu(self, tearoff=0, bg="#313244", fg="#cdd6f4",
                               activebackground="#45475a")
                menu.add_command(label="Переименовать", command=lambda: self._rename_group_by_name(gn))
                menu.add_command(label="Удалить группу", command=lambda: self._delete_group_by_name(gn))
                menu.tk_popup(event.x_root, event.y_root)
            header.bind("<Button-3>", _group_menu)
            for w in header.winfo_children():
                w.bind("<Button-3>", _group_menu)

        # Cards grid
        cards_frame = tk.Frame(group_frame, bg="#1e1e2e")
        cards_frame.pack(fill=tk.X, padx=2, pady=(2, 4))

        col = 0
        row = 0
        max_cols = 2

        for idx, session in sessions:
            card = self._create_session_card(cards_frame, session, idx, color)
            card.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Make columns expand evenly
        for c in range(max_cols):
            cards_frame.columnconfigure(c, weight=1)

    def _create_session_card(self, parent, session, index, accent_color):
        is_selected = (index == self._selected_card_idx)
        card_bg = "#3b3b5c" if is_selected else "#313244"

        card = tk.Frame(parent, bg=card_bg, padx=10, pady=8, cursor="hand2",
                        highlightbackground=accent_color if is_selected else "#45475a",
                        highlightthickness=2)

        name = session.get("name", "???")
        host = session.get("host", "")
        port = session.get("port", 22)
        desc = session.get("description", "")

        # Name
        name_label = tk.Label(card, text=name, bg=card_bg, fg="#cdd6f4",
                              font=("Consolas", 10, "bold"), anchor="w")
        name_label.pack(fill=tk.X)

        # Description (if any)
        if desc:
            desc_label = tk.Label(card, text=desc, bg=card_bg, fg="#a6adc8",
                                  font=("Consolas", 8), anchor="w")
            desc_label.pack(fill=tk.X)

        # Address
        addr_text = f"{host}:{port}"
        addr_label = tk.Label(card, text=addr_text, bg=card_bg, fg="#6c7086",
                              font=("Consolas", 9), anchor="w")
        addr_label.pack(fill=tk.X)

        # Status dot
        dot_color = accent_color
        dot_canvas = tk.Canvas(card, width=8, height=8, bg=card_bg, highlightthickness=0)
        dot_canvas.create_oval(1, 1, 7, 7, fill=dot_color, outline="")
        dot_canvas.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)

        # Bindings
        def _enter(e):
            if index != self._selected_card_idx:
                card.configure(bg="#3b3b5c")
                for w in card.winfo_children():
                    if isinstance(w, tk.Label):
                        w.configure(bg="#3b3b5c")
                    elif isinstance(w, tk.Canvas):
                        w.configure(bg="#3b3b5c")

        def _leave(e):
            bg = "#3b3b5c" if index == self._selected_card_idx else "#313244"
            card.configure(bg=bg)
            for w in card.winfo_children():
                if isinstance(w, tk.Label):
                    w.configure(bg=bg)
                elif isinstance(w, tk.Canvas):
                    w.configure(bg=bg)

        def _click(e):
            old_idx = self._selected_card_idx
            self._selected_card_idx = index
            # Visual update without destroying widgets
            if old_idx != index:
                card.configure(bg="#3b3b5c", highlightbackground=accent_color)
                for w in card.winfo_children():
                    if isinstance(w, (tk.Label, tk.Canvas)):
                        try:
                            w.configure(bg="#3b3b5c")
                        except tk.TclError:
                            pass

        def _double_click(e):
            self._connect_by_idx(index)

        def _right_click(e):
            self._show_card_context_menu(e, index)

        for widget in [card, name_label, addr_label, dot_canvas] + ([desc_label] if desc else []):
            widget.bind("<Enter>", _enter)
            widget.bind("<Leave>", _leave)
            widget.bind("<Button-1>", _click)
            widget.bind("<Double-1>", _double_click)
            widget.bind("<Button-3>", _right_click)
            if sys.platform == "darwin":
                widget.bind("<Button-2>", _right_click)
                widget.bind("<Control-Button-1>", _right_click)

        return card

    def _show_card_context_menu(self, event, index):
        menu = tk.Menu(self, tearoff=0, bg="#313244", fg="#cdd6f4",
                       activebackground="#45475a")
        menu.add_command(label="Подключиться", command=lambda: self._connect_by_idx(index))
        menu.add_separator()

        # Move to group submenu
        move_menu = tk.Menu(menu, tearoff=0, bg="#313244", fg="#cdd6f4")
        move_menu.add_command(label="Без группы", command=lambda: self._move_and_refresh(index, ""))
        for g in self.store.groups:
            move_menu.add_command(label=g, command=lambda g=g: self._move_and_refresh(index, g))
        menu.add_cascade(label="Переместить в...", menu=move_menu)
        menu.add_separator()
        menu.add_command(label="Изменить", command=lambda: self._edit_session_by_idx(index))
        menu.add_command(label="Удалить", command=lambda: self._delete_session_by_idx(index))

        menu.tk_popup(event.x_root, event.y_root)

    def _move_and_refresh(self, index, group):
        self.store.move_to_group(index, group)
        self._refresh_cards()

    # ── Right Panel (Commands + Agent) ────────────────────────

    def _build_right_panel(self, parent):
        # Toggle button for commands
        toggle_frame = tk.Frame(parent, bg="#181825")
        toggle_frame.pack(fill=tk.X)

        self._toggle_btn = tk.Button(
            toggle_frame, text="Команды ▼" if self._commands_visible else "Команды ▶",
            bg="#181825", fg="#89b4fa", activebackground="#181825", activeforeground="#6c8fff",
            relief=tk.FLAT, font=("Consolas", 10, "bold"), cursor="hand2",
            command=self._toggle_commands,
        )
        self._toggle_btn.pack(side=tk.LEFT, padx=6, pady=4)

        # Paned window for commands + agent (draggable splitter)
        self._right_paned = tk.PanedWindow(
            parent, orient=tk.VERTICAL, bg="#45475a",
            sashwidth=6, sashrelief=tk.FLAT, opaqueresize=True,
        )
        self._right_paned.pack(fill=tk.BOTH, expand=True)

        # Commands panel (collapsible)
        self.commands_container = tk.Frame(self._right_paned, bg="#1e1e2e")
        if self._commands_visible:
            self._right_paned.add(self.commands_container, minsize=80)

        # Search bar
        search_frame = tk.Frame(self.commands_container, bg="#1e1e2e")
        search_frame.pack(fill=tk.X, padx=4, pady=4)
        tk.Label(search_frame, text="Поиск:", bg="#1e1e2e", fg="#6c7086",
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self.cmd_search = tk.Entry(search_frame, bg="#313244", fg="#cdd6f4",
                                   insertbackground="#cdd6f4", relief=tk.FLAT,
                                   font=("Consolas", 9))
        self.cmd_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        setup_entry_clipboard(self.cmd_search)
        self.cmd_search.bind("<KeyRelease>", self._filter_commands)

        # Commands tree
        cmd_tree_frame = tk.Frame(self.commands_container, bg="#1e1e2e")
        cmd_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.cmd_tree = ttk.Treeview(cmd_tree_frame, columns=("desc",), show="tree headings",
                                      selectmode="browse")
        self.cmd_tree.heading("#0", text="Команда")
        self.cmd_tree.heading("desc", text="Описание")
        self.cmd_tree.column("#0", width=180, minwidth=100)
        self.cmd_tree.column("desc", width=160, minwidth=80)

        cmd_scroll = ttk.Scrollbar(cmd_tree_frame, command=self.cmd_tree.yview)
        self.cmd_tree.configure(yscrollcommand=cmd_scroll.set)
        cmd_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.cmd_tree.pack(fill=tk.BOTH, expand=True)
        self.cmd_tree.bind("<Double-1>", self._send_command)

        tk.Label(self.commands_container, text="Двойной клик = отправить в терминал",
                 bg="#1e1e2e", fg="#6c7086", font=("Consolas", 8)).pack(fill=tk.X, pady=2)

        self._populate_commands()

        # ── Agent Panel ──
        agent_wrapper = tk.Frame(self._right_paned, bg="#1e1e2e")
        self._right_paned.add(agent_wrapper, minsize=120)

        agent_header = tk.Frame(agent_wrapper, bg="#181825")
        agent_header.pack(fill=tk.X)

        tk.Label(agent_header, text="AI Агент", bg="#181825", fg="#a6e3a1",
                 font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=6, pady=4)

        # Provider indicator
        provider = self.config.get("ai_provider", "local")
        provider_names = {"local": "Локальный", "claude": "Claude", "deepseek": "DeepSeek"}
        self._provider_label = tk.Label(
            agent_header, text=f"[{provider_names.get(provider, provider)}]",
            bg="#181825", fg="#6c7086", font=("Consolas", 8),
        )
        self._provider_label.pack(side=tk.LEFT, padx=2)

        tk.Button(agent_header, text="⚙", bg="#181825", fg="#6c7086",
                  activebackground="#181825", relief=tk.FLAT, font=("Consolas", 11),
                  cursor="hand2", command=self._ai_settings).pack(side=tk.RIGHT, padx=6)

        # Agent content
        self.agent_frame = tk.Frame(agent_wrapper, bg="#1e1e2e")
        self.agent_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        # Input
        agent_input = tk.Frame(self.agent_frame, bg="#1e1e2e")
        agent_input.pack(fill=tk.X, pady=(0, 4))

        self.agent_entry = tk.Entry(agent_input, bg="#313244", fg="#cdd6f4",
                                     insertbackground="#cdd6f4", relief=tk.FLAT,
                                     font=("Consolas", 10))
        self.agent_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        setup_entry_clipboard(self.agent_entry)
        self.agent_entry.insert(0, "как обновить ubuntu?")
        self.agent_entry.bind("<Return>", lambda e: self._agent_ask())

        tk.Button(agent_input, text="Спросить", bg="#a6e3a1", fg="#1e1e2e",
                  activebackground="#89b4fa", relief=tk.FLAT,
                  font=("Consolas", 9, "bold"), padx=8, pady=2,
                  command=self._agent_ask).pack(side=tk.RIGHT)

        # Result area
        self.agent_result = tk.Text(
            self.agent_frame, bg="#181825", fg="#cdd6f4",
            font=("Consolas", 9), wrap=tk.WORD, borderwidth=0,
            insertbackground="#cdd6f4", highlightthickness=0,
        )
        agent_scroll = ttk.Scrollbar(self.agent_frame, command=self.agent_result.yview)
        self.agent_result.configure(yscrollcommand=agent_scroll.set)
        agent_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.agent_result.pack(fill=tk.BOTH, expand=True)

        self.agent_result.tag_configure("cmd", foreground="#a6e3a1", font=("Consolas", 9, "bold"))
        self.agent_result.tag_configure("desc", foreground="#6c7086")
        self.agent_result.tag_configure("platform", foreground="#89b4fa")
        self.agent_result.tag_configure("hint", foreground="#f9e2af")
        self.agent_result.tag_configure("error", foreground="#f38ba8")
        self.agent_result.tag_configure("ai", foreground="#cba6f7")
        self.agent_result.tag_configure("thinking", foreground="#f9e2af", font=("Consolas", 9, "italic"))
        self.agent_result.configure(state=tk.DISABLED)
        self.agent_result.bind("<Double-1>", self._agent_send_cmd)

    def _toggle_commands(self):
        self._commands_visible = not self._commands_visible
        self.config.set("commands_visible", self._commands_visible)

        if self._commands_visible:
            # Add commands pane back (before agent)
            panes = self._right_paned.panes()
            if str(self.commands_container) not in panes:
                self._right_paned.add(self.commands_container, before=panes[0] if panes else None, minsize=80)
            self._toggle_btn.configure(text="Команды ▼")
        else:
            self._right_paned.forget(self.commands_container)
            self._toggle_btn.configure(text="Команды ▶")

    # ── AI Agent ──────────────────────────────────────────────

    def _ai_settings(self):
        dlg = AISettingsDialog(self, self.config.data)
        if dlg.result:
            for k, v in dlg.result.items():
                self.config.set(k, v)
            provider = self.config.get("ai_provider", "local")
            provider_names = {"local": "Локальный", "claude": "Claude", "deepseek": "DeepSeek"}
            self._provider_label.configure(text=f"[{provider_names.get(provider, provider)}]")

    def _agent_ask(self):
        query = self.agent_entry.get().strip()
        if not query:
            return

        provider = self.config.get("ai_provider", "local")

        if provider == "local":
            self._agent_ask_local(query)
        elif provider in ("claude", "deepseek"):
            self._agent_ask_api(query, provider)

    def _agent_ask_local(self, query):
        results = agent_search(query)
        self.agent_result.configure(state=tk.NORMAL)
        self.agent_result.delete("1.0", tk.END)
        if not results:
            self.agent_result.insert(tk.END, "Не нашёл команд. Попробуй другие слова:\n", "desc")
            self.agent_result.insert(tk.END, "обновить, диск, память, порт, пароль,\n", "hint")
            self.agent_result.insert(tk.END, "docker, nginx, ssl, vpn, wifi, dhcp\n\n", "hint")
            self.agent_result.insert(tk.END, "Совет: ", "desc")
            self.agent_result.insert(tk.END, "подключи Claude или DeepSeek API\n", "ai")
            self.agent_result.insert(tk.END, "для умного ассистента (⚙ настройки)", "ai")
        else:
            self.agent_result.insert(tk.END, "Двойной клик по команде = отправить\n\n", "desc")
            for _, platform, cmd, desc in results:
                self.agent_result.insert(tk.END, f"[{platform}] ", "platform")
                self.agent_result.insert(tk.END, f"{cmd}\n", "cmd")
                self.agent_result.insert(tk.END, f"  {desc}\n", "desc")
        self.agent_result.configure(state=tk.DISABLED)

    def _agent_ask_api(self, query, provider):
        self.agent_result.configure(state=tk.NORMAL)
        self.agent_result.delete("1.0", tk.END)
        self.agent_result.insert(tk.END, "Думаю...\n", "thinking")
        self.agent_result.configure(state=tk.DISABLED)

        def _call():
            try:
                if provider == "claude":
                    api_key = self.config.get("claude_api_key", "")
                    if not api_key:
                        return None, "API-ключ Claude не задан. Нажми ⚙"
                    response = call_claude_api(api_key, query)
                elif provider == "deepseek":
                    api_key = self.config.get("deepseek_api_key", "")
                    if not api_key:
                        return None, "API-ключ DeepSeek не задан. Нажми ⚙"
                    response = call_deepseek_api(api_key, query)
                else:
                    return None, "Неизвестный провайдер"
                return response, None
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")[:200]
                return None, f"HTTP {e.code}: {body}"
            except Exception as e:
                return None, str(e)

        def _on_result(response, error):
            self.agent_result.configure(state=tk.NORMAL)
            self.agent_result.delete("1.0", tk.END)
            if error:
                self.agent_result.insert(tk.END, f"Ошибка: {error}\n", "error")
            else:
                self.agent_result.insert(tk.END, "Двойной клик по команде = отправить\n\n", "desc")
                # Parse response for commands
                lines = response.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Try to detect command lines: starts with [linux]/[keenetic] or contains command pattern
                    if line.startswith("[linux]") or line.startswith("[keenetic]"):
                        parts = line.split("] ", 1)
                        platform = parts[0] + "]"
                        rest = parts[1] if len(parts) > 1 else ""
                        if " — " in rest:
                            cmd, desc = rest.split(" — ", 1)
                            self.agent_result.insert(tk.END, f"{platform} ", "platform")
                            self.agent_result.insert(tk.END, f"{cmd.strip()}\n", "cmd")
                            self.agent_result.insert(tk.END, f"  {desc.strip()}\n", "desc")
                        else:
                            self.agent_result.insert(tk.END, f"{platform} ", "platform")
                            self.agent_result.insert(tk.END, f"{rest}\n", "cmd")
                    elif line.startswith("`") or line.startswith("$") or line.startswith("sudo ") or line.startswith("show "):
                        # Looks like a command
                        cmd = line.strip("`").strip("$ ")
                        self.agent_result.insert(tk.END, f"{cmd}\n", "cmd")
                    elif " — " in line or " - " in line:
                        sep = " — " if " — " in line else " - "
                        cmd, desc = line.split(sep, 1)
                        cmd = cmd.strip().strip("`").strip("$ ")
                        if cmd:
                            self.agent_result.insert(tk.END, f"{cmd}\n", "cmd")
                            self.agent_result.insert(tk.END, f"  {desc.strip()}\n", "desc")
                        else:
                            self.agent_result.insert(tk.END, f"{line}\n", "ai")
                    else:
                        self.agent_result.insert(tk.END, f"{line}\n", "ai")
            self.agent_result.configure(state=tk.DISABLED)

        def _thread():
            response, error = _call()
            self.after(0, lambda: _on_result(response, error))

        threading.Thread(target=_thread, daemon=True).start()

    def _agent_send_cmd(self, event):
        idx = self.agent_result.index(f"@{event.x},{event.y}")
        line = self.agent_result.get(f"{idx} linestart", f"{idx} lineend").strip()
        # Skip description lines and headers
        if line.startswith("["):
            line = line.split("] ", 1)[-1] if "] " in line else line
        if not line or line.startswith("Двойной") or line.startswith("Не нашёл") or line.startswith("Думаю") or line.startswith("Ошибка") or line.startswith("Совет"):
            return
        # Skip description lines (indented with 2 spaces)
        raw = self.agent_result.get(f"{idx} linestart", f"{idx} lineend")
        if raw.startswith("  "):
            return

        current_tab = self.notebook.select()
        if not current_tab:
            return
        widget = self.nametowidget(current_tab)
        if isinstance(widget, TerminalWidget) and widget.channel and not widget.channel.closed:
            widget._send(line + "\r")
        else:
            # Try to find any active terminal
            for tab_id in self.notebook.tabs():
                w = self.nametowidget(tab_id)
                if isinstance(w, TerminalWidget) and w.channel and not w.channel.closed:
                    w._send(line + "\r")
                    self.notebook.select(w)
                    return
            messagebox.showinfo("Нет терминала", "Сначала подключитесь к серверу")

    # ── Commands Tree ─────────────────────────────────────────

    def _populate_commands(self, filter_text=""):
        self.cmd_tree.delete(*self.cmd_tree.get_children())
        ft = filter_text.lower()
        for platform, categories in COMMANDS.items():
            platform_id = self.cmd_tree.insert("", tk.END, text=platform, values=("",), open=not ft)
            has_children = False
            for category, cmds in categories.items():
                cat_id = self.cmd_tree.insert(platform_id, tk.END, text=category, values=("",), open=bool(ft))
                cat_has = False
                for cmd, desc in cmds:
                    if ft and ft not in cmd.lower() and ft not in desc.lower() and ft not in category.lower():
                        continue
                    self.cmd_tree.insert(cat_id, tk.END, text=cmd, values=(desc,))
                    cat_has = True
                    has_children = True
                if not cat_has:
                    self.cmd_tree.delete(cat_id)
            if not has_children:
                self.cmd_tree.delete(platform_id)

    def _filter_commands(self, event=None):
        text = self.cmd_search.get().strip()
        self._populate_commands(text)

    def _send_command(self, event=None):
        sel = self.cmd_tree.selection()
        if not sel:
            return
        item = sel[0]
        cmd = self.cmd_tree.item(item, "text")
        children = self.cmd_tree.get_children(item)
        if children:
            return
        current_tab = self.notebook.select()
        if not current_tab:
            return
        widget = self.nametowidget(current_tab)
        if isinstance(widget, TerminalWidget) and widget.channel and not widget.channel.closed:
            widget._send(cmd + "\r")
        else:
            messagebox.showinfo("Нет терминала", "Сначала подключитесь к серверу")

    # ── Session/Group CRUD ────────────────────────────────────

    def _connect_by_idx(self, idx):
        s = self.store.sessions[idx]
        pw = self.store.get_password(s)
        self._open_terminal(s["host"], s["port"], s["user"], pw, s["name"])

    def _new_session(self):
        pregroup = ""
        if self._selected_card_idx is not None:
            pregroup = self.store.sessions[self._selected_card_idx].get("group", "")
        session_defaults = {"group": pregroup} if pregroup else None
        dlg = SessionDialog(self, "Новая сессия", session=session_defaults,
                             groups=self.store.groups)
        if dlg.result:
            r = dlg.result
            self.store.add(r["host"], r["port"], r["user"], r["password"],
                           r["name"], r.get("group", ""))
            self._refresh_cards()

    def _edit_session(self):
        if self._selected_card_idx is not None:
            self._edit_session_by_idx(self._selected_card_idx)

    def _edit_session_by_idx(self, idx):
        s = self.store.sessions[idx].copy()
        s["password"] = ""
        dlg = SessionDialog(self, "Изменить сессию", s, groups=self.store.groups)
        if dlg.result:
            r = dlg.result
            update = {"name": r["name"], "description": r.get("description", ""),
                      "host": r["host"], "port": r["port"],
                      "user": r["user"], "group": r.get("group", "")}
            if r["password"]:
                update["password"] = r["password"]
            self.store.update(idx, **update)
            self._refresh_cards()

    def _delete_session(self):
        if self._selected_card_idx is not None:
            self._delete_session_by_idx(self._selected_card_idx)

    def _delete_session_by_idx(self, idx):
        s = self.store.sessions[idx]
        if messagebox.askyesno("Удалить?", f"Удалить сессию «{s['name']}»?"):
            self.store.remove(idx)
            self._selected_card_idx = None
            self._refresh_cards()

    def _new_group(self):
        name = simpledialog.askstring("Новая группа", "Название группы:", parent=self)
        if name and name.strip():
            self.store.add_group(name.strip())
            self._refresh_cards()

    def _rename_group_by_name(self, old):
        new = simpledialog.askstring("Переименовать", f"Новое имя для «{old}»:",
                                      parent=self, initialvalue=old)
        if new and new.strip() and new.strip() != old:
            self.store.rename_group(old, new.strip())
            self._refresh_cards()

    def _delete_group_by_name(self, name):
        if messagebox.askyesno("Удалить группу?",
                                f"Удалить группу «{name}»?\nСессии переместятся в «Без группы»."):
            self.store.remove_group(name)
            self._refresh_cards()

    def _quick_connect(self):
        host = self.q_host.get().strip()
        if not host:
            return
        try:
            port = int(self.q_port.get().strip() or "22")
        except ValueError:
            port = 22
        user = self.q_user.get().strip() or "root"
        pw = self.q_pass.get()

        self.store.add(host, port, user, pw)
        self._refresh_cards()
        self._open_terminal(host, port, user, pw)
        self.q_pass.delete(0, tk.END)

    def _open_terminal(self, host, port, user, password, name=None):
        tab_name = name or f"{user}@{host}"

        term = TerminalWidget(self.notebook, on_close=lambda: None)
        self.notebook.add(term, text=f"● {tab_name}")
        self.notebook.select(term)
        term.connect(host, port, user, password)

        # Store connection info for file manager
        term._conn_info = {"host": host, "port": port, "user": user, "password": password}

        close_btn_frame = tk.Frame(term, bg="#1e1e2e")

        btn_s = {"bg": "#313244", "fg": "#89b4fa", "activebackground": "#45475a",
                 "relief": tk.FLAT, "font": ("Consolas", 9), "padx": 6, "pady": 2}
        tk.Button(close_btn_frame, text="📁 Файлы",
                  command=lambda: self._open_file_manager(term),
                  **btn_s).pack(side=tk.LEFT, padx=4, pady=2)

        tk.Button(
            close_btn_frame, text="✕ Закрыть",
            bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            relief=tk.FLAT, font=("Consolas", 9), padx=6, pady=2,
            command=lambda: self._close_tab(term),
        ).pack(side=tk.RIGHT, padx=4, pady=2)
        close_btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def _open_file_manager(self, term):
        """Open SFTP file manager tab using terminal's SSH connection."""
        if not term.ssh or not term.ssh.get_transport() or not term.ssh.get_transport().is_active():
            messagebox.showerror("Ошибка", "SSH не подключён", parent=self)
            return
        info = getattr(term, "_conn_info", {})
        tab_name = f"📁 {info.get('user', '')}@{info.get('host', '')}"

        def send_cmd(path):
            """Send path/command to active terminal."""
            if term.channel and not term.channel.closed:
                term._send(path + "\n")
                self.notebook.select(term)

        fm = FileManagerWidget(self.notebook, term.ssh, on_send_cmd=send_cmd)
        self.notebook.add(fm, text=tab_name)
        self.notebook.select(fm)

    def _close_tab(self, term):
        term.disconnect()
        self.notebook.forget(term)
        term.destroy()

    def destroy(self):
        for child in self.notebook.winfo_children():
            if isinstance(child, TerminalWidget):
                child.disconnect()
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
