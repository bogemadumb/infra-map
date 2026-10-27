# Домашний сервер — инвентаризация (демо)

### host-homelab
- name: Домашний сервер · мини-ПК
- host: homelab
- kind: machine
- group: infra
- status: up
- purpose: Тяжёлые и долгие задачи, медиатека и вторая копия бэкапов. Наружу не открыт, доступ — через WireGuard.
- how: 8 ядер, 32 ГБ RAM, два диска в RAID1, Debian 13.
- tech: Debian 13, Docker, mdadm

### jellyfin
- name: Jellyfin
- host: homelab
- kind: app
- group: media
- status: up
- purpose: Медиатека для телевизора и телефона.
- how: контейнер, аппаратное транскодирование VAAPI, библиотека на /mnt/media.
- tech: Jellyfin 10.10
- links:
  - -> media-disk : bind : библиотека

### media-index
- name: media-index.timer
- host: homelab
- kind: timer
- group: media
- status: failed
- statusNote: /mnt/media не смонтирован после перезагрузки
- purpose: Раз в час пересканирует медиатеку и обновляет метаданные.
- how: systemd-таймер → Jellyfin API; на ошибке — биение fail в пульс.
- tech: bash, curl
- links:
  - -> jellyfin : http API : пересканирование
  - -> crm-api : POST /feed/beat : биение

### media-disk
- name: /mnt/media (RAID1)
- host: homelab
- kind: share
- group: media
- status: partial
- statusNote: не смонтирован автоматически: в fstab нет nofail
- purpose: Диски медиатеки.
- how: mdadm RAID1, ext4.
- tech: mdadm

### restic-pull
- name: restic-pull.timer
- host: homelab
- kind: timer
- group: backup
- status: up
- purpose: Забирает зашифрованные дампы с VPS и кладёт в локальный и облачный репозиторий restic.
- how: 06:30, ssh-ключ с принудительной командой (только отдача файлов), restic forget --keep-daily 14.
- tech: restic
- links:
  - -> backup-timer : ssh : забор дампов
  - -> ext-s3 : restic : внешняя копия

### restore-check
- name: restore-check.timer
- host: homelab
- kind: timer
- group: backup
- status: up
- purpose: Раз в месяц восстанавливает последний дамп в пустой Postgres и сверяет число строк.
- how: временный контейнер, pg_restore, сравнение с метриками из CRM.
- tech: bash, docker
- links:
  - -> restic-pull : restic restore : последний дамп
  - -> crm-api : POST /feed/beat : результат проверки

### ollama
- name: Локальная LLM
- host: homelab
- kind: model
- group: automation
- status: up
- purpose: Разметка и пересказ заметок без отправки данных наружу.
- how: модель 8B в 4 бит, API только в сети wg.
- tech: llama.cpp
- links:
  - <- notes-digest : http : пересказ

### notes-digest
- name: notes-digest.timer
- host: homelab
- kind: timer
- group: automation
- status: up
- purpose: Каждое утро собирает новые заметки из RSS в короткий дайджест.
- how: читает заметки через API CRM, пересказывает локальной моделью, пишет одну заметку-дайджест.
- tech: Python
- links:
  - -> crm-api : GET/POST /notes : заметки
  - -> ollama : http : пересказ

### pulse-agent-homelab
- name: Агент пульса (домашний сервер)
- host: homelab
- kind: agent
- group: monitoring
- status: up
- purpose: Биения таймеров домашнего сервера; если молчит он сам — в пульсе одна тревога по машине, а не по каждой задаче.
- how: каждые 5 минут, через WireGuard.
- tech: Python
- links:
  - -> crm-api : POST /feed/beats : биения
  - -> wireguard : wg : канал до VPS
