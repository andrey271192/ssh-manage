"""
KU SSH Manager — Portable SSH client with auto-save sessions.
Tkinter GUI + paramiko SSH + JSON session store.
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import paramiko
import threading
import json
import os
import sys
import re
import base64
import socket
from datetime import datetime
from pathlib import Path

APP_NAME = "PCA SSH"
APP_SUBTITLE = "Private Control Administration"
VERSION = "1.1"

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


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

SESSIONS_FILE = app_dir() / "sessions.json"

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

ANSI_COLORS = {
    "30": "#1a1a1a", "31": "#cc4444", "32": "#44cc44", "33": "#cccc44",
    "34": "#4488cc", "35": "#cc44cc", "36": "#44cccc", "37": "#cccccc",
    "90": "#666666", "91": "#ff6666", "92": "#66ff66", "93": "#ffff66",
    "94": "#6699ff", "95": "#ff66ff", "96": "#66ffff", "97": "#ffffff",
}

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

        self.text.tag_configure("error", foreground="#f38ba8")
        self.text.tag_configure("info", foreground="#89b4fa")
        for code, color in ANSI_COLORS.items():
            self.text.tag_configure(f"fg{code}", foreground=color)

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
            self._write(f"Подключено!\n", "info")
            self._read_loop()
        except Exception as ex:
            self._write(f"\nОшибка: {ex}\n", "error")
            self.running = False
            if self.on_close:
                self.after(100, self.on_close)

    def _read_loop(self):
        buf = b""
        while self.running and self.channel and not self.channel.closed:
            try:
                data = self.channel.recv(4096)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace")
                clean = strip_ansi(text)
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
        def _do():
            self.text.configure(state=tk.NORMAL)
            if tag:
                self.text.insert(tk.END, text, tag)
            else:
                self.text.insert(tk.END, text)
            self.text.see(tk.END)
        self.after(0, _do)

    def _send(self, data):
        if self.channel and not self.channel.closed:
            try:
                self.channel.send(data.encode() if isinstance(data, str) else data)
            except Exception:
                pass
        return "break"

    def _on_key(self, event):
        if event.state & 4:  # Ctrl
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
        self.grab_set()

        frame = ttk.Frame(self, padding=15)
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
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=3)
            entry = ttk.Entry(frame, width=35)
            if key == "password":
                entry.configure(show="*")
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky="ew", pady=3, padx=(8, 0))
            self.entries[key] = entry

        # Group selector
        row_group = len(fields)
        ttk.Label(frame, text="Группа:").grid(row=row_group, column=0, sticky="w", pady=3)
        group_frame = ttk.Frame(frame)
        group_frame.grid(row=row_group, column=1, sticky="ew", pady=3, padx=(8, 0))

        group_values = groups or []
        current_group = session.get("group", "") if session else ""
        self.group_var = tk.StringVar(value=current_group)
        self.group_combo = ttk.Combobox(group_frame, textvariable=self.group_var,
                                         values=group_values, width=20)
        self.group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row_group + 1, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=4)

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


# ── Main Application ───────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — {APP_SUBTITLE} v{VERSION}")
        self.geometry("1100x700")
        self.minsize(800, 500)
        self.configure(bg="#1e1e2e")

        self.store = SessionStore()
        self.terminals = {}  # tab_id -> TerminalWidget

        self._apply_theme()
        self._build_ui()
        self._refresh_session_list()

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        sel = "#45475a"

        style.configure(".", background=bg, foreground=fg, fieldbackground="#313244", borderwidth=0)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background="#45475a", foreground=fg, padding=(10, 5))
        style.map("TButton", background=[("active", "#585b70")])
        style.configure("Treeview", background="#313244", foreground=fg, fieldbackground="#313244",
                         rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background="#45475a", foreground=fg)
        style.map("Treeview", background=[("selected", sel)])
        style.configure("TEntry", fieldbackground="#313244", foreground=fg)
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background="#45475a", foreground=fg, padding=(12, 6))
        style.map("TNotebook.Tab", background=[("selected", "#585b70")])

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
        tk.Label(
            brand_frame, text=APP_NAME, bg="#181825", fg="#cdd6f4",
            font=("Consolas", 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand_frame, text=APP_SUBTITLE, bg="#181825", fg="#6c7086",
            font=("Consolas", 9),
        ).pack(anchor="w")

        sep_v = tk.Frame(top_bar, bg="#45475a", width=1)
        sep_v.pack(side=tk.LEFT, fill=tk.Y, padx=12, pady=8)

        links = [
            ("GitHub", "https://github.com/nickolay-frolov"),
            ("Boosty", "https://boosty.to/lot_andrey"),
            ("Telegram", "https://t.me/lot_andrey"),
            ("Поддержать (СБП)", "https://finance.ozon.ru/apps/sbp/ozonbankpay/019dc200-2a5d-7931-a619-782d285f6798"),
        ]
        for i, (text, url) in enumerate(links):
            if i > 0:
                tk.Label(top_bar, text="·", bg="#181825", fg="#6c7086", font=("Consolas", 9)).pack(side=tk.LEFT)
            lnk = tk.Label(
                top_bar, text=text, bg="#181825", fg="#89b4fa",
                font=("Consolas", 9, "underline"), cursor="hand2",
            )
            lnk.pack(side=tk.LEFT, padx=6)
            lnk.bind("<Button-1>", lambda e, u=url: self._open_url(u))

        tk.Label(
            top_bar, text="@lot_andrey", bg="#181825", fg="#6c7086",
            font=("Consolas", 9),
        ).pack(side=tk.RIGHT, padx=10)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ── Left: session list with groups ──
        left = ttk.Frame(paned, width=300)
        paned.add(left, weight=0)

        toolbar = ttk.Frame(left)
        toolbar.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(toolbar, text="＋ Сессия", command=self._new_session).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✎", command=self._edit_session, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="✕", command=self._delete_session, width=3).pack(side=tk.LEFT, padx=1)

        toolbar2 = ttk.Frame(left)
        toolbar2.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(toolbar2, text="＋ Группа", command=self._new_group).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar2, text="✎ Группа", command=self._rename_group).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar2, text="✕ Группа", command=self._delete_group).pack(side=tk.LEFT, padx=2)

        self.tree = ttk.Treeview(left, columns=("desc", "addr"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Сессия")
        self.tree.heading("desc", text="Описание")
        self.tree.heading("addr", text="Адрес")
        self.tree.column("#0", width=130, minwidth=80)
        self.tree.column("desc", width=100, minwidth=60)
        self.tree.column("addr", width=120, minwidth=70)
        tree_scroll = ttk.Scrollbar(left, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # Drag & drop state
        self._drag_item = None
        self._drag_after_id = None
        self.tree.bind("<ButtonPress-1>", self._drag_start)
        self.tree.bind("<B1-Motion>", self._drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._drag_end)

        # Right-click context menu
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.configure(bg="#313244", fg="#cdd6f4", activebackground="#45475a")
        self.tree.bind("<Button-3>", self._show_context_menu)
        if sys.platform == "darwin":
            self.tree.bind("<Button-2>", self._show_context_menu)
            self.tree.bind("<Control-Button-1>", self._show_context_menu)

        # Quick connect bar
        qf = ttk.LabelFrame(left, text="Быстрое подключение", padding=8)
        qf.pack(fill=tk.X, pady=(6, 0))

        row1 = ttk.Frame(qf)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Хост:").pack(side=tk.LEFT)
        self.q_host = ttk.Entry(row1, width=16)
        self.q_host.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Label(row1, text="Порт:").pack(side=tk.LEFT)
        self.q_port = ttk.Entry(row1, width=6)
        self.q_port.insert(0, "22")
        self.q_port.pack(side=tk.LEFT, padx=4)

        row2 = ttk.Frame(qf)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Юзер:").pack(side=tk.LEFT)
        self.q_user = ttk.Entry(row2, width=12)
        self.q_user.insert(0, "root")
        self.q_user.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Label(row2, text="Пароль:").pack(side=tk.LEFT)
        self.q_pass = ttk.Entry(row2, width=12, show="*")
        self.q_pass.pack(side=tk.LEFT, padx=4)

        ttk.Button(qf, text="Подключиться", command=self._quick_connect).pack(fill=tk.X, pady=(6, 0))
        self.q_host.bind("<Return>", lambda e: self._quick_connect())
        self.q_pass.bind("<Return>", lambda e: self._quick_connect())

        # ── Center: terminal tabs ──
        right_paned = ttk.PanedWindow(paned, orient=tk.HORIZONTAL)
        paned.add(right_paned, weight=1)

        self.notebook = ttk.Notebook(right_paned)
        right_paned.add(self.notebook, weight=1)

        # ── Right: commands panel ──
        cmd_frame = ttk.Frame(right_paned, width=320)
        right_paned.add(cmd_frame, weight=0)

        cmd_header = tk.Label(
            cmd_frame, text="Команды", bg="#181825", fg="#cdd6f4",
            font=("Consolas", 11, "bold"), pady=6,
        )
        cmd_header.pack(fill=tk.X)

        # Search bar
        search_frame = ttk.Frame(cmd_frame)
        search_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.cmd_search = ttk.Entry(search_frame, width=20)
        self.cmd_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        self.cmd_search.bind("<KeyRelease>", self._filter_commands)

        # Commands tree
        cmd_tree_frame = ttk.Frame(cmd_frame)
        cmd_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.cmd_tree = ttk.Treeview(
            cmd_tree_frame, columns=("desc",), show="tree headings",
            selectmode="browse",
        )
        self.cmd_tree.heading("#0", text="Команда")
        self.cmd_tree.heading("desc", text="Описание")
        self.cmd_tree.column("#0", width=200, minwidth=120)
        self.cmd_tree.column("desc", width=180, minwidth=100)

        cmd_scroll = ttk.Scrollbar(cmd_tree_frame, command=self.cmd_tree.yview)
        self.cmd_tree.configure(yscrollcommand=cmd_scroll.set)
        cmd_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.cmd_tree.pack(fill=tk.BOTH, expand=True)

        self.cmd_tree.bind("<Double-1>", self._send_command)

        # Hint label
        hint = tk.Label(
            cmd_frame, text="Двойной клик = отправить в терминал",
            bg="#1e1e2e", fg="#6c7086", font=("Consolas", 8),
        )
        hint.pack(fill=tk.X, pady=2)

        self._populate_commands()

        # ── Agent tab (under commands) ──
        agent_frame = ttk.LabelFrame(cmd_frame, text="Агент-подсказчик", padding=6)
        agent_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        agent_input_frame = ttk.Frame(agent_frame)
        agent_input_frame.pack(fill=tk.X)
        self.agent_entry = ttk.Entry(agent_input_frame, width=22)
        self.agent_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.agent_entry.insert(0, "как обновить ubuntu?")
        ttk.Button(agent_input_frame, text="?", command=self._agent_ask, width=3).pack(side=tk.RIGHT)
        self.agent_entry.bind("<Return>", lambda e: self._agent_ask())

        self.agent_result = tk.Text(
            agent_frame, height=8, bg="#181825", fg="#cdd6f4",
            font=("Consolas", 9), wrap=tk.WORD, borderwidth=0,
            insertbackground="#cdd6f4", highlightthickness=0,
        )
        self.agent_result.pack(fill=tk.X, pady=(4, 0))
        self.agent_result.tag_configure("cmd", foreground="#a6e3a1", font=("Consolas", 9, "bold"))
        self.agent_result.tag_configure("desc", foreground="#6c7086")
        self.agent_result.tag_configure("platform", foreground="#89b4fa")
        self.agent_result.tag_configure("hint", foreground="#f9e2af")
        self.agent_result.configure(state=tk.DISABLED)
        self.agent_result.bind("<Double-1>", self._agent_send_cmd)

        # Welcome tab
        welcome = ttk.Frame(self.notebook)
        self.notebook.add(welcome, text="Добро пожаловать")
        msg = ttk.Label(
            welcome,
            text=f"{APP_NAME} v{VERSION}\n\n"
                 "• Двойной клик по сессии = подключение\n"
                 "• Быстрое подключение внизу слева\n"
                 "• Все сессии сохраняются автоматически\n"
                 "• Ctrl+C/D/L работают в терминале\n"
                 "• Панель команд справа — клик = отправка\n"
                 "• Агент внизу справа — спроси что угодно",
            font=("Consolas", 12),
            justify=tk.CENTER,
        )
        msg.pack(expand=True)

    # ── Drag & Drop ──

    def _drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item and self.tree.parent(item):
            self._drag_item = item
        else:
            self._drag_item = None

    def _drag_motion(self, event):
        if not self._drag_item:
            return
        target = self.tree.identify_row(event.y)
        if target:
            self.tree.selection_set(target)

    def _drag_end(self, event):
        if not self._drag_item:
            return
        target = self.tree.identify_row(event.y)
        if not target or target == self._drag_item:
            self._drag_item = None
            return

        src_iid = self._drag_item
        src_tags = self.tree.item(src_iid, "tags")
        if not src_tags or not src_tags[0].startswith("s_"):
            self._drag_item = None
            return
        src_idx = int(src_tags[0].split("_")[1])

        # Determine target group
        target_tags = self.tree.item(target, "tags")
        if target_tags and target_tags[0].startswith("g_"):
            new_group = target_tags[0][2:]
        elif target_tags and target_tags[0].startswith("s_"):
            parent = self.tree.parent(target)
            if parent:
                ptags = self.tree.item(parent, "tags")
                new_group = ptags[0][2:] if ptags and ptags[0].startswith("g_") else ""
            else:
                new_group = ""
        else:
            new_group = ""

        if new_group == "__ungrouped__":
            new_group = ""

        self.store.move_to_group(src_idx, new_group)
        self._refresh_session_list()
        self._drag_item = None

    # ── Context Menu ──

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)
        self._ctx_menu.delete(0, tk.END)

        tags = self.tree.item(item, "tags")
        if tags and tags[0].startswith("s_"):
            idx = int(tags[0].split("_")[1])
            self._ctx_menu.add_command(label="Подключиться", command=lambda: self._connect_by_idx(idx))
            self._ctx_menu.add_separator()

            # Move to group submenu
            move_menu = tk.Menu(self._ctx_menu, tearoff=0, bg="#313244", fg="#cdd6f4")
            move_menu.add_command(label="Без группы", command=lambda: self._move_session(idx, ""))
            for g in self.store.groups:
                move_menu.add_command(label=g, command=lambda g=g: self._move_session(idx, g))
            self._ctx_menu.add_cascade(label="Переместить в...", menu=move_menu)
            self._ctx_menu.add_separator()
            self._ctx_menu.add_command(label="Изменить", command=self._edit_session)
            self._ctx_menu.add_command(label="Удалить", command=self._delete_session)

        elif tags and tags[0].startswith("g_"):
            gname = tags[0][2:]
            if gname != "__ungrouped__":
                self._ctx_menu.add_command(label="Переименовать", command=self._rename_group)
                self._ctx_menu.add_command(label="Удалить группу", command=self._delete_group)

        self._ctx_menu.tk_popup(event.x_root, event.y_root)

    def _move_session(self, idx, group):
        self.store.move_to_group(idx, group)
        self._refresh_session_list()

    def _connect_by_idx(self, idx):
        s = self.store.sessions[idx]
        pw = self.store.get_password(s)
        self._open_terminal(s["host"], s["port"], s["user"], pw, s["name"])

    # ── Agent ──

    def _agent_ask(self):
        query = self.agent_entry.get().strip()
        if not query:
            return
        results = agent_search(query)
        self.agent_result.configure(state=tk.NORMAL)
        self.agent_result.delete("1.0", tk.END)
        if not results:
            self.agent_result.insert(tk.END, "Не нашёл команд. Попробуй другие слова:\n", "desc")
            self.agent_result.insert(tk.END, "обновить, диск, память, порт, пароль,\n", "hint")
            self.agent_result.insert(tk.END, "docker, nginx, ssl, vpn, wifi, dhcp", "hint")
        else:
            self.agent_result.insert(tk.END, "Двойной клик по команде = отправить\n\n", "desc")
            for _, platform, cmd, desc in results:
                tag = "linux" if platform == "linux" else "keenetic"
                self.agent_result.insert(tk.END, f"[{platform}] ", "platform")
                self.agent_result.insert(tk.END, f"{cmd}\n", "cmd")
                self.agent_result.insert(tk.END, f"  {desc}\n", "desc")
        self.agent_result.configure(state=tk.DISABLED)

    def _agent_send_cmd(self, event):
        idx = self.agent_result.index(f"@{event.x},{event.y}")
        line = self.agent_result.get(f"{idx} linestart", f"{idx} lineend").strip()
        if line.startswith("["):
            line = line.split("] ", 1)[-1] if "] " in line else line
        if not line or line.startswith("Двойной") or line.startswith("Не нашёл"):
            return
        current_tab = self.notebook.select()
        if not current_tab:
            return
        widget = self.nametowidget(current_tab)
        if isinstance(widget, TerminalWidget) and widget.channel and not widget.channel.closed:
            widget._send(line + "\r")
        else:
            messagebox.showinfo("Нет терминала", "Сначала подключитесь к серверу")

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

    def _refresh_session_list(self):
        self.tree.delete(*self.tree.get_children())

        # Group sessions
        grouped = {}
        ungrouped = []
        for i, s in enumerate(self.store.sessions):
            g = s.get("group", "")
            if g:
                grouped.setdefault(g, []).append((i, s))
            else:
                ungrouped.append((i, s))

        # Show groups from store order
        for g in self.store.groups:
            gid = self.tree.insert("", tk.END, text=f"  {g}", values=("", ""),
                                    open=True, tags=(f"g_{g}",))
            for i, s in grouped.get(g, []):
                desc = s.get("description", "")
                self.tree.insert(gid, tk.END, text=s["name"],
                                  values=(desc, f"{s['host']}:{s['port']}"),
                                  tags=(f"s_{i}",))

        # Groups that exist in sessions but not in store.groups
        for g, items in grouped.items():
            if g not in self.store.groups:
                self.store.add_group(g)
                gid = self.tree.insert("", tk.END, text=f"  {g}", values=("", ""),
                                        open=True, tags=(f"g_{g}",))
                for i, s in items:
                    desc = s.get("description", "")
                    self.tree.insert(gid, tk.END, text=s["name"],
                                      values=(desc, f"{s['host']}:{s['port']}"),
                                      tags=(f"s_{i}",))

        # Ungrouped sessions
        if ungrouped:
            uid = self.tree.insert("", tk.END, text="  Без группы", values=("", ""),
                                    open=True, tags=("g___ungrouped__",))
            for i, s in ungrouped:
                desc = s.get("description", "")
                self.tree.insert(uid, tk.END, text=s["name"],
                                  values=(desc, f"{s['host']}:{s['port']}"),
                                  tags=(f"s_{i}",))

    def _get_selected_session_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        tags = self.tree.item(sel[0], "tags")
        if tags and tags[0].startswith("s_"):
            return int(tags[0].split("_")[1])
        return None

    def _get_selected_group_name(self):
        sel = self.tree.selection()
        if not sel:
            return None
        tags = self.tree.item(sel[0], "tags")
        if tags and tags[0].startswith("g_"):
            name = tags[0][2:]
            return name if name != "__ungrouped__" else None
        return None

    def _on_tree_double_click(self, event):
        idx = self._get_selected_session_index()
        if idx is not None:
            self._connect_by_idx(idx)

    # ── Group CRUD ──

    def _new_group(self):
        from tkinter import simpledialog
        name = simpledialog.askstring("Новая группа", "Название группы:", parent=self)
        if name and name.strip():
            self.store.add_group(name.strip())
            self._refresh_session_list()

    def _rename_group(self):
        old = self._get_selected_group_name()
        if not old:
            sel = self.tree.selection()
            if sel:
                tags = self.tree.item(sel[0], "tags")
                if tags and tags[0].startswith("s_"):
                    parent = self.tree.parent(sel[0])
                    if parent:
                        ptags = self.tree.item(parent, "tags")
                        if ptags and ptags[0].startswith("g_") and ptags[0][2:] != "__ungrouped__":
                            old = ptags[0][2:]
            if not old:
                return
        from tkinter import simpledialog
        new = simpledialog.askstring("Переименовать", f"Новое имя для «{old}»:", parent=self,
                                      initialvalue=old)
        if new and new.strip() and new.strip() != old:
            self.store.rename_group(old, new.strip())
            self._refresh_session_list()

    def _delete_group(self):
        name = self._get_selected_group_name()
        if not name:
            return
        if messagebox.askyesno("Удалить группу?",
                                f"Удалить группу «{name}»?\nСессии переместятся в «Без группы»."):
            self.store.remove_group(name)
            self._refresh_session_list()

    # ── Session CRUD ──

    def _new_session(self):
        # Pre-select group from tree selection
        pregroup = self._get_selected_group_name() or ""
        if not pregroup:
            idx = self._get_selected_session_index()
            if idx is not None:
                pregroup = self.store.sessions[idx].get("group", "")

        session_defaults = {"group": pregroup} if pregroup else None
        dlg = SessionDialog(self, "Новая сессия", session=session_defaults,
                             groups=self.store.groups)
        if dlg.result:
            r = dlg.result
            self.store.add(r["host"], r["port"], r["user"], r["password"],
                           r["name"], r.get("group", ""))
            self._refresh_session_list()

    def _edit_session(self):
        idx = self._get_selected_session_index()
        if idx is None:
            return
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
            self._refresh_session_list()

    def _delete_session(self):
        idx = self._get_selected_session_index()
        if idx is None:
            return
        s = self.store.sessions[idx]
        if messagebox.askyesno("Удалить?", f"Удалить сессию «{s['name']}»?"):
            self.store.remove(idx)
            self._refresh_session_list()

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
        group = self._get_selected_group_name() or ""

        self.store.add(host, port, user, pw, group=group)
        self._refresh_session_list()
        self._open_terminal(host, port, user, pw)
        self.q_pass.delete(0, tk.END)

    def _open_terminal(self, host, port, user, password, name=None):
        tab_name = name or f"{user}@{host}"

        def on_close():
            pass

        term = TerminalWidget(self.notebook, on_close=on_close)
        self.notebook.add(term, text=f"● {tab_name}")
        self.notebook.select(term)
        term.connect(host, port, user, password)

        close_btn_frame = ttk.Frame(term)
        close_btn = ttk.Button(
            close_btn_frame, text="✕ Закрыть вкладку",
            command=lambda: self._close_tab(term),
        )
        close_btn.pack(side=tk.RIGHT, padx=4, pady=2)
        close_btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

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
