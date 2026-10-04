# Відтворення ДЗ №2

## Запуск

Кіт: https://github.com/sergeytkachenko/paypilot-l03-eval, commit 8108fc88f2cd39d193b09cb326b8463f8c439345.
Стенд: https://github.com/roman-olshevskiy/paypilot-stand, commit a876b7311d2b0a36bf4cb361cb4d27d5e211d5f2.
Покласти golden.jsonl з цього репозиторію у sets/ кіту, generate_golden.py — у корінь кіту.
Файли hw2_capture.py, hw2_runtime.py та tests/ копіюються в кіт для збирання повних доказів.
Для offline acceptance також потрібний evidence/kit-baseline-manifest.json; для prompt-change тесту — evidence/forecast-commit.json.

Стенд має бути локальним, із live Anthropic. Ключ лише в локальному .env стенду.
Налаштування L03: STAND_DIR=../paypilot-stand, EVAL_STAND_URL=http://host.docker.internal:8000, JUDGE_MODEL=not-used.
Clock: 2026-09-15T10:00:00Z. Сам course runner не застосовує context.clock; capture adapter встановлює та перевіряє його після кожного reset.
Фактична модель усіх живих викликів за traces: claude-haiku-4-5-20251001.

З каталогу кіту:

~~~powershell
# Без моделі: регенерація та перевірка
docker compose run --rm -T eval python generate_golden.py --output sets/golden.jsonl --manifest evidence/generation-manifest.json
docker compose run --rm -T eval --set golden --dry-run
docker compose run --rm -T eval python -m unittest discover -s tests -p test_hw2_contract.py -v

~~~

hw2_capture.py делегує незмінному cli.py/runner.py; формат сирого course report не змінено.
Він додатково зберігає повні відповіді, request IDs, traces, input/output usage та model-call count;
відновлює попередні profile/extra defects/clock у finally. База після запуску залишається reset-станом; вихідний довільний стан БД не відновлюється.
Не запускати інші тести паралельно на цьому стенді.
Додаткові captures — evidence/runs/, сирі course reports — reports/.

set_hash: 92f5e7f20c48
Повний SHA256: 92f5e7f20c48a91a0fe03c5307abfd8f6fbd0345b595320d96525cde812130d6

Для повтору з каталогу кіту, після копіювання власних support-файлів і evidence/forecast-commit.json:

~~~powershell
$env:HW2_RUN_PROFILE='clean'
$env:HW2_RUN_LABEL='baseline-clean'
python -m unittest discover -s tests -p test_live_hw2.py -v
$env:HW2_RUN_PROFILE='lesson-03'
$env:HW2_RUN_LABEL='defective-lesson03'
python -m unittest discover -s tests -p test_live_hw2.py -v
$env:HW2_RUN_PROFILE='clean'
$env:HW2_RUN_LABEL='prompt-changed-clean'
$env:HW2_PROMPT_LINE=(Get-Content evidence/forecast-commit.json -Raw | ConvertFrom-Json).line
python -m unittest discover -s tests -p test_live_hw2.py -v
Remove-Item Env:HW2_PROMPT_LINE
$env:HW2_ONLY='FX-007'
$env:HW2_RUN_LABEL='restored-clean-control'
python -m unittest discover -s tests -p test_live_hw2.py -v
Remove-Item Env:HW2_ONLY
~~~

Python для host-тесту має бути реальним інтерпретатором, не Windows Store alias; Docker eval — Python 3.12.15.
Runtime base prompt відновлено побайтово: before/after SHA256 однакові.
Зовнішній prompt-guard snapshot може містити попередні D04/D05/D25, які відновлюються між тестами;
фактичні clean/lesson-03 snapshots — before.json/during.json у кожному каталозі runs, профіль кожного запиту також є в trace.
Не трактувати version label base.v1 як відсутність доданого рядка.

Чистий клон кіту: loader dry-run пройшов із тим самим hash, offline acceptance/guards — 6/6 passed. [Журнал](evidence/clean-clone-offline-tests.txt).

