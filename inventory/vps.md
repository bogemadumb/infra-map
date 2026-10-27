# VPS — инвентаризация (демо)

Снято только чтением. Секретов в файле нет: только имена служб, портов и файлов.

### host-vps
- name: VPS · облако, Ubuntu 24.04
- host: vps
- kind: machine
- group: infra
- status: up
- purpose: Единственная машина с публичным адресом: точки входа по HTTPS, база, API и VPN-вход для домашних машин.
- how: 2 vCPU, 4 ГБ RAM, 60 ГБ диск. Docker для Postgres и API, systemd-таймеры для остального, fail2ban, unattended-upgrades.
- tech: Ubuntu 24.04, Docker, systemd
- links:
  - -> ext-internet : eth0 : весь исходящий трафик

### nginx
- name: nginx (фронт-прокси)
- host: vps
- kind: proxy
- group: network
- status: up
- purpose: Принимает HTTPS и раздаёт запросы контейнерам и статике.
- how: 80/443, TLS от Let's Encrypt, лимит частоты на /login, HSTS.
- tech: nginx 1.26
- links:
  - -> crm-web : http :8080 : SPA и /api
  - -> blog-static : файлы : статический блог
  - -> grafana : http :3000 : /grafana/
  - -> ext-letsencrypt : ACME : продление сертификатов

### certbot-timer
- name: certbot.timer
- host: vps
- kind: timer
- group: network
- status: up
- purpose: Дважды в сутки проверяет сертификаты и продлевает за 30 дней до конца.
- how: systemd-таймер, после продления — reload nginx и биение в пульс.
- tech: certbot
- links:
  - -> nginx : reload : новые сертификаты
  - -> crm-api : POST /feed/beat : биение

### postgres
- name: PostgreSQL 17
- host: vps
- kind: db
- group: core
- status: up
- purpose: Одна база для CRM: схемы crm (данные) и hub (лента и биения).
- how: контейнер, порт опубликован только во внутреннюю сеть compose, пароль — docker secret.
- tech: postgres:17-alpine

### crm-api
- name: CRM API (FastAPI)
- host: vps
- kind: service
- group: core
- status: up
- purpose: REST API личной CRM: задачи, проекты, заметки, календарь, лента событий и пульс фоновых задач.
- how: uvicorn, миграции Alembic при старте, healthcheck /api/v2/health.
- tech: Python 3.12, FastAPI, SQLModel
- links:
  - -> postgres : psycopg : все данные
  - -> ext-telegram : Bot API : тревоги пульса

### crm-web
- name: CRM SPA (nginx в контейнере)
- host: vps
- kind: frontend
- group: core
- status: up
- purpose: Веб-интерфейс CRM; отдаёт статику и проксирует /api в контейнер API.
- how: React-сборка в образе nginx, кэш ассетов навсегда, index.html — без кэша.
- tech: React 19, Vite, Tailwind
- links:
  - -> crm-api : http :8000 : /api

### backup-timer
- name: crm-backup.timer
- host: vps
- kind: timer
- group: backup
- status: up
- purpose: Ночной дамп базы, шифрование, хранение трёх последних копий.
- how: 04:10, pg_dump → openssl enc; дамп меньше 70 % прошлого — сбой, а не успех. Копии забирает домашний сервер.
- tech: bash, openssl
- links:
  - -> postgres : pg_dump : дамп
  - -> crm-api : POST /feed/beat : биение
  - <- restic-pull : ssh : забор копий

### wireguard
- name: WireGuard (wg0)
- host: vps
- kind: service
- group: network
- status: up
- purpose: Частная сеть между VPS, домашним сервером и ноутбуком: домашние машины доступны без открытых портов.
- how: UDP 51820, по пиру на машину, AllowedIPs только подсеть wg.
- tech: wireguard-tools
- links:
  - -> host-homelab : wg : туннель
  - -> host-laptop : wg : туннель

### rss-collector
- name: rss-collector.timer
- host: vps
- kind: timer
- group: automation
- status: partial
- statusNote: два источника отвечают 503
- purpose: Раз в полчаса собирает RSS-ленты и складывает новые записи в заметки CRM.
- how: Python-скрипт, повтор с экспоненциальной паузой, external_id против дублей.
- tech: Python, httpx, feedparser
- links:
  - -> ext-rss : https : ленты
  - -> crm-api : POST /notes : новые записи

### blog-static
- name: Блог (статика)
- host: vps
- kind: app
- group: web
- status: up
- purpose: Статический сайт, который собирает CI и выкладывает по rsync.
- how: каталог /srv/blog, nginx отдаёт с кэшированием.
- tech: Astro
- links:
  - <- ext-github : rsync из Actions : выкладка

### grafana
- name: Grafana
- host: vps
- kind: app
- group: monitoring
- status: disabled
- statusNote: выключена: пульса CRM хватает
- purpose: Графики нагрузки машин.
- how: контейнер остановлен, данные тома сохранены.
- tech: Grafana 11

### node-exporter
- name: node_exporter
- host: vps
- kind: service
- group: monitoring
- status: up
- purpose: Метрики машины для агента пульса.
- how: только localhost:9100.
- tech: prometheus node_exporter
- links:
  - <- pulse-agent-vps : http : чтение метрик

### pulse-agent-vps
- name: Агент пульса (VPS)
- host: vps
- kind: agent
- group: monitoring
- status: up
- purpose: Раз в 5 минут опрашивает таймеры systemd и шлёт пачку биений в CRM.
- how: systemctl list-timers + последний код выхода юнитов → POST /feed/beats.
- tech: Python
- links:
  - -> crm-api : POST /feed/beats : биения таймеров

### ext-internet
- name: Интернет
- host: cloud
- kind: external
- group: external
- status: up
- purpose: Внешняя сеть.

### ext-letsencrypt
- name: Let's Encrypt
- host: cloud
- kind: external
- group: external
- status: up
- purpose: Бесплатные TLS-сертификаты по ACME.

### ext-telegram
- name: Telegram Bot API
- host: cloud
- kind: external
- group: external
- status: up
- purpose: Канал тревог: сообщения о сбоях фоновых задач.

### ext-github
- name: GitHub
- host: cloud
- kind: external
- group: external
- status: up
- purpose: Репозитории и CI (Actions).

### ext-rss
- name: RSS-источники
- host: cloud
- kind: external
- group: external
- status: partial
- statusNote: 2 из 14 отвечают 503
- purpose: Блоги и новостные ленты.

### ext-s3
- name: Объектное хранилище (S3)
- host: cloud
- kind: external
- group: external
- status: up
- purpose: Внешняя копия бэкапов restic.
