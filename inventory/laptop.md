# Ноутбук — инвентаризация (демо)

### host-laptop
- name: Ноутбук · macOS
- host: laptop
- kind: machine
- group: infra
- status: up
- purpose: Рабочая машина: разработка, Claude Code, заметки. Спит и уезжает — поэтому на нём нет ничего, что должно работать по расписанию.
- how: Apple Silicon, launchd для своих агентов, WireGuard до VPS.
- tech: macOS

### claude-code
- name: Claude Code
- host: laptop
- kind: tool
- group: dev
- status: up
- purpose: Агент для кода; через MCP видит задачи и проекты CRM, пишет в журнал и закрывает этапы.
- how: MCP-сервер crm по stdio, ключ с ролью agent.
- tech: Claude Code, MCP
- links:
  - -> crm-mcp : stdio : инструменты
  - -> ext-anthropic : https : модель

### crm-mcp
- name: MCP-сервер CRM
- host: laptop
- kind: mcp
- group: dev
- status: up
- purpose: Инструменты today, tasks, project_journal, project_stage, search, pulse.
- how: тонкий клиент к REST API с X-API-Key; правит файл дорожной карты на диске.
- tech: Python, mcp
- links:
  - -> crm-api : https : REST
  - -> project-folders : файлы : дорожные карты

### project-folders
- name: Папки проектов
- host: laptop
- kind: share
- group: dev
- status: up
- purpose: Спецификация, дорожная карта и журнал каждого проекта — источник правды для CRM.
- how: Markdown; хук сессии отправляет свежую карту в CRM.
- tech: Markdown

### notes-sync
- name: notes-sync (LaunchAgent)
- host: laptop
- kind: launchagent
- group: automation
- status: up
- purpose: Двусторонняя синхронизация заметок CRM с папкой Markdown.
- how: раз в 15 минут, конфликт — обе версии с пометкой.
- tech: Python, launchd
- links:
  - -> crm-api : /notes : синхронизация
  - -> crm-api : POST /feed/beat : биение

### pulse-agent-laptop
- name: Агент пульса (ноутбук)
- host: laptop
- kind: agent
- group: monitoring
- status: up
- purpose: Биение ноутбука; пока он спит, пульс не считает его задачи тревогой.
- how: LaunchAgent, раз в 2 минуты.
- tech: Python, launchd
- links:
  - -> crm-api : POST /feed/beat : биение

### docker-desktop
- name: Colima (Docker)
- host: laptop
- kind: container
- group: dev
- status: disabled
- statusNote: запускается только на время работы: ноутбуку нужна память
- purpose: Локальный стенд CRM — копия прод-стека.
- how: colima start → docker compose up; после работы — down.
- tech: Colima, Docker

### ext-anthropic
- name: Anthropic API
- host: cloud
- kind: external
- group: external
- status: up
- purpose: Модель для Claude Code.
