# L03 · Automated Eval Suite — PayPilot · ДЗ №2

Автор: Roman Olshevskyi. Підготовка: 2026-10-04. Мандат: Ship it.
Статус: кроки 1–8 виконано; три живі прогони, прогноз і фінальний residual-risk ще не виконані.
Репозиторій здачі: https://github.com/roman-olshevskiy/paypilot-hw2. Робоча гілка roman-olshevskyi/hw2; здача — main.

## Запуск

Кіт: https://github.com/sergeytkachenko/paypilot-l03-eval, commit 8108fc88f2cd39d193b09cb326b8463f8c439345.
Стенд: https://github.com/roman-olshevskiy/paypilot-stand, commit a876b7311d2b0a36bf4cb361cb4d27d5e211d5f2.
Покласти golden.jsonl з цього репозиторію у sets/ кіту, generate_golden.py — у корінь кіту.
Файли hw2_capture.py, hw2_runtime.py та tests/ — власне додаткове оточення; копіюються в кіт для збирання повних доказів.

Стенд має бути локальним, із live Anthropic. Ключ лише в локальному .env стенду.
Налаштування L03: STAND_DIR=../paypilot-stand, EVAL_STAND_URL=http://host.docker.internal:8000, JUDGE_MODEL=not-used.
Clock: 2026-09-15T10:00:00Z. Сам course runner не застосовує context.clock; capture adapter встановлює та перевіряє його після кожного reset.
Модель за конфігурацією preflight: Anthropic, default claude-haiku-4-5. Фактичний model ID запитів буде підтверджено лише live traces.

З каталогу кіту:

~~~powershell
# Без моделі: регенерація та перевірка
docker compose run --rm -T eval python generate_golden.py --output sets/golden.jsonl --manifest evidence/generation-manifest.json
docker compose run --rm -T eval --set golden --dry-run
docker compose run --rm -T eval python -m unittest discover -s tests -p test_hw2_contract.py -v

# Обов’язкові live-прогони кроку 9; ПОКИ НЕ ВИКОНАНО
docker compose run --rm -T eval python hw2_capture.py --set golden --profile clean
docker compose run --rm -T eval python hw2_capture.py --set golden --profile lesson-03
~~~

hw2_capture.py делегує незмінному cli.py/runner.py; формат сирого course report не змінено.
Він додатково зберігає повні відповіді, request IDs, traces, input/output usage та model-call count;
відновлює попередні profile/extra defects/clock у finally. База після запуску залишається reset-станом; вихідний довільний стан БД не відновлюється.
Не запускати інші тести паралельно на цьому стенді.
Додаткові captures — evidence/runs/, сирі course reports — reports/.

set_hash: 92f5e7f20c48
Повний SHA256: 92f5e7f20c48a91a0fe03c5307abfd8f6fbd0345b595320d96525cde812130d6

## Скарги

| Скарга | Власний кейс | Клієнт / операція та уточнення | Oracle | Чому не готовий demo |
|---|---|---|---|---|
| C-01 | SWF-001 | CUS-0001; конкретизовано SWIFT 1000 EUR для перевірки сумарного тарифу | engine: fx.transfer_fee | SWIFT-кейсів у демо та генераторі кіту немає |
| C-11 | CMP-C11 | CUS-0009 Iryna, PharmaPlus TX-0902, fraud_card_not_present | engine: disputes.check | Саме ця операція та її eligibility не входять у кіт; не підміна TX-0701 |
| C-12 | CMP-C12 | CUS-0002, CloudServe TX-0201 на EUR-рахунку; TX-0202 на USD не вважаємо доведеним повторним списанням | engine: disputes.check | Новий transaction-specific eligibility case; не просте перейменування питання про «60» |
| C-14 | CMP-C14 | CUS-0002 як явний навчальний контекст; перелік усіх reason codes І duplicate window | engine: policy.DISPUTE_WINDOWS_DAYS | Нове комбіноване очікування; діагностику retrieval ця перевірка не покриває |
| C-17 | TON-HW2-001 | CUS-0002 / TX-0201 — конкретизована ситуація роздратованого клієнта | human | Нова рубрика tone/next step, release, не оцінена daily |

C-01/C-14/C-17 не містять усіх потрібних даних у скарзі; доданий навчальний контекст зазначено явно.
Друга купка triage кіту має лише три скарги, тому відбір розширено власною перевіркою контексту інших скарг.
C-03/DIS-002-N та C-09/LIM-001 уже представлені в демо і не зараховуються новими.
C-05 уже має 6000 EUR і відповідає FX-003; CMP-C05 — окремий edge-варіант на 2000 EUR, не відтворення нової скарги.
C-07 без даних початкового FX quote не оголошується точно відтвореним.
Детальна новизна кожного кейса — [походження](case-provenance.md).

## Генератор

generate_golden.py походить від generate_from_engines.py: розширено fx_cases plan, додано complaint/limit сценарії та авторські human-рубрики.
Очікування engine-кейсів обчислено реальним offline запуском чистих модулів app.engines, а не переписано з лекції.
CUSTOMERS/операції читаються з seed; transfer limits враховують усі settled outgoing транзакції, як у check_limits.
Для engine_call записано відтворювані вирази; результати кожного виклику збережено в [generation manifest](evidence/generation-manifest.json).

Додані межі:
- CUS-0007: 1000 / 1001 EUR, FX-006/007 та spread-пари.
- CUS-0001: 380 / 381 EUR після використаних 120 EUR, FX-008/009 та spread-пари.
- CUS-0002: 200 / 201 EUR після використаних 800 EUR, FX-010/011.
- SWF-002: USD1000 з fee у EUR — валюта як нова межа тарифного обчислення.

Критерій відбору: потрібні граничні пари, відмінні observable (сума/спред), нові complaint-сценарії,
контролі eligibility та daily/monthly fields; зайві готові FX-комбінації не додаються тільки заради кількості.
12 kit-сценаріїв зберігають свою ідентичність added_in=l03; параметри/числа перевірено чистими модулями.
CMP-003 (balance/DB) та CMP-006 (вузький product phrase) виключено з демо-піднабору, щоб не називати їх повним engine/catalog oracle.

Знахідки: на межі allowance спред нульовий, на один EUR понад нею — на всю суму. Результат узгоджується з правилом all-or-nothing.
Перевірка flags у C-11/C-12 очікує True: для цих конкретних дат обидві операції в межах своїх різних reason-code windows.
Додавання «60» у тексті не є доказом correct action; тому для eligibility обрано tool_result_flag.

35 кейсів: 12 kit + 18 власних обчислених + 5 власних human = 23 власних.
Daily: 30 кейсів ×1; release: 5 human ×5, вони не входять до трьох daily-прогонів.
Джерела: complaint=7, engine=12, edge=16. Oracle: engine=29, corpus=1, human=5.
Рівні: 1/2/3/4/7. Severity 100%; critical=7, high=28.
Точної новизни лише за відмінністю input недостатньо: [case-provenance.md](case-provenance.md) описує зміну параметра або observable.

## Прогони

| Прогін | Профіль | Результат | Звіт |
|---|---|---|---|
| Baseline | clean | Не виконано, крок 9 | Ще не створено |
| Дефектна система | lesson-03 | Не виконано, крок 9 | Ще не створено |
| Зміна промпту | clean + власний рядок | Не виконано, крок 10 | Ще не створено |

Рядок промпту та прогноз ще не обрано. Перед третім прогоном прогноз буде окремим комітом у цьому репозиторії.
Час/hash коміту зберігаються окремим evidence, до створення третього report.
test_live_hw2.py дозволяє тимчасову правку лише з forecast-commit.json; відновлює базовий файл у finally.
Зараз live-test discovery дав SKIP: серія не запускалася.

Планова матриця дефектів, ще не виміряний результат:

| Дефект lesson-03 | Кандидати на виявлення | Обмеження |
|---|---|---|
| D19 wrong duplicate window | DIS-002-N, DIS-006, CMP-004, DIS-001 | CMP-C12 може пройти при обох вікнах; не повне покриття |
| D20 wrong tier spread | FX-003/005/007/009/011, CMP-C05 | На безкоштовному allowance спред лишається 0 |
| D21 partial allowance | FX-007/009/011, FX-004 | Числа треба звірити з фактичними tool results |
| D22 daily as monthly | LIM-003, LIM-HW2-MONTHLY | Текстовий LIM-001 може приховати зіпсований payload |
| D26 ignored restriction | DIS-007 | False payload має підтверджуватися trace, не лише словами |

Виконано до live-серії:
- Генератор і loader dry-run — passed.
- Offline acceptance/guards — 6/6 passed.
- Реальний preflight unittest — 1/1 passed, chat/model calls=0.
- Початковий profile/clock і байти runtime base prompt після тесту відновлено.
- [Докази підготовки](evidence/preparation-manifest.json), [preflight](evidence/preflight.json), [журнал](evidence/preflight-tests.txt).

Попередній бюджет трьох daily-прогонів: 90 chat requests.
За agent usage L02 (USD0.383063 за 65 відповідей, без judge) орієнтир ≈USD0.53, плюс контроль відновлення.
Це оцінка перенесення середнього usage, не measured L03 cost і не верхня межа.
Плановий запас до ≈USD1.10 потребує контролю після кожного запуску; автоматичного dollar cap у L03 runner немає.
Фактичні tokens, model calls і вартість будуть обчислені з captures та raw reports у кроці 11.

## Прогноз перед третім прогоном

Рядок англійською:

~~~text
For currency conversion answers, state only the pre-spread gross amount as the amount received and do not repeat the after-spread final amount.
~~~

Прогноз: FX-004, FX-002, FX-003, FX-005, FX-007, FX-009, FX-011 і CMP-C05 мають впасти.
Підстава: чистий quote_fx поверне правильний after-spread final_amount, але текст під впливом нового рядка
покаже лише gross_amount; tool_grounded_numeric потребує того самого правильного числа й у відповіді.
FX-006, FX-008, FX-010 мають пройти: при нульовому спреді gross_amount дорівнює final_amount.
Spread-field checks, SWIFT, limits та dispute checks прямо не змінюються.
Очікуємо щонайменше одну реальну регресію; якщо прогноз не справдиться, пояснення запишемо після запуску.
Датасет: set_hash 92f5e7f20c48, 30 daily-кейсів. Прогноз записано до зміни runtime-промпту й третього report.
