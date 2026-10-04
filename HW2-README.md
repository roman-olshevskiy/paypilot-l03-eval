# L03 · Automated Eval Suite — PayPilot · ДЗ №2

Автор: Roman Olshevskyi. Підготовка: 2026-10-04. Мандат: Ship it.
Статус: комплект ДЗ завершено; три живі daily-прогони та контроль відновлення виконано. Здача в LMS — посилання на main.
Репозиторій здачі: https://github.com/roman-olshevskiy/paypilot-hw2. Робоча гілка roman-olshevskyi/hw2; здача — main.

Відтворення у чистому кіті: [RUNNING.md](RUNNING.md). Покажчик: [SUBMISSION.md](SUBMISSION.md).

## Скарги

| Скарга | Власний кейс | Клієнт / операція та уточнення | Oracle | Чому не готовий demo |
|---|---|---|---|---|
| C-01 | SWF-001 | CUS-0001; конкретизовано SWIFT 1000 EUR для перевірки сумарного тарифу | engine: fx.transfer_fee | SWIFT-кейсів у демо та генераторі кіту немає |
| C-11 | CMP-C11 | CUS-0009 Iryna, PharmaPlus TX-0902, fraud_card_not_present | engine: disputes.check | Саме ця операція та її eligibility не входять у кіт; не підміна TX-0701 |
| C-12 | CMP-C12 | CUS-0002, CloudServe TX-0201 на EUR-рахунку; TX-0202 на USD не вважаємо доведеним повторним списанням | engine: disputes.check | Новий transaction-specific eligibility case; не просте перейменування питання про «60» |
| C-14 | CMP-C14 | CUS-0002 як явний навчальний контекст; перелік усіх reason codes І duplicate window | engine: policy.DISPUTE_WINDOWS_DAYS | Нове комбіноване очікування; діагностику retrieval ця перевірка не покриває |
| C-17 | TON-HW2-001 | CUS-0002 / TX-0201 — конкретизована ситуація роздратованого клієнта | human | Нова рубрика tone/next step, release, не оцінена daily |

C-01/C-14/C-17 не містять усіх потрібних даних у скарзі; доданий навчальний контекст зазначено явно.
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

Відбір: граничні пари, різні observable (сума/спред), нові скарги та eligibility/limit payload.
На межі allowance спред нульовий, після перевищення — на всю суму (all-or-nothing).
Engine expectations обчислено чистими модулями; 12 kit-кейсів зберігають added_in=l03.
CMP-003 (balance/DB) та CMP-006 (product phrase) виключено; деталі — case-provenance.md.

35 кейсів: 12 kit + 18 власних обчислених + 5 власних human = 23 власних.
Daily: 30 кейсів ×1; release: 5 human ×5, вони не входять до трьох daily-прогонів.
Джерела: complaint=7, engine=12, edge=16. Oracle: engine=29, corpus=1, human=5.
Рівні: 1/2/3/4/7. Severity 100%; critical=7, high=28.
Точної новизни лише за відмінністю input недостатньо: [case-provenance.md](case-provenance.md) описує зміну параметра або observable.

## Прогони

| Прогін | Профіль | Результат | Сирий звіт |
|---|---|---|---|
| Baseline | clean | 30/30 | [golden-clean-20261004T000956.json](https://github.com/roman-olshevskiy/paypilot-hw2/blob/main/reports/golden-clean-20261004T000956.json) |
| Дефектна система | lesson-03 | 14/30 | [golden-lesson-03-20261004T001243.json](https://github.com/roman-olshevskiy/paypilot-hw2/blob/main/reports/golden-lesson-03-20261004T001243.json) |
| Власний рядок промпту | clean | 30/30 | [golden-clean-20261004T001507.json](https://github.com/roman-olshevskiy/paypilot-hw2/blob/main/reports/golden-clean-20261004T001507.json) |
| Контроль після відновлення | clean | 1/1 | [golden-clean-20261004T001927.json](https://github.com/roman-olshevskiy/paypilot-hw2/blob/main/reports/golden-clean-20261004T001927.json) |

Усі звіти мають set_hash 92f5e7f20c48. Три основні виконали ті самі 30 daily-кейсів, четвертий — лише FX-007.
П'ять release/human кейсів не запускалися і не оцінювалися.
Прогноз зафіксовано окремим [комітом 1768082](https://github.com/roman-olshevskiy/paypilot-hw2/commit/1768082aba930dd6a08fea499c3a967de57d1222)
2026-10-04 00:12:01 UTC; третій звіт створено о 00:15:07 UTC.
Точний рядок та початковий прогноз збережено нижче без виправлення заднім числом.

Фактична чутливість до цієї зміни: **0/30**, pass→fail=0, fail→pass=0; прогноз восьми падінь не справдився.
Усі вісім відповідей містять правильну final_amount після спреду; наприклад FX-007 назвав 1078.25 USD.
Рядок додано до базового файла, але модель не виконала його заборону показувати final_amount.
Це спостереження одного запуску, не доказ стійкості до довільних змін промпту.
FX-002 залишився green попри хибне пояснення часткового allowance: числовий oracle перевіряє суму, не весь текст.

Профіль lesson-03: 16 падінь, ознаки всіх п'яти дефектів у payload:
D19 — DIS-006 (90 замість 60 днів); D20 — FX-007-S (1.5% замість 0.9%);
D21 — FX-007 (spread лише на понадлімітний 1 EUR); D22 — LIM-003 (daily як monthly);
D26 — DIS-007 (eligible=true при compliance_hold).
[Матриця доказів](evidence/defect-analysis.json) містить request IDs і фактичні значення.
Дефекти ввімкнено одночасно; ізольованих mutant-прогонів не було, тому це не п'ять незалежних оцінок detection rate.

Усі дії зі стендом виконано реальними Python unittest:
test_preflight_hw2.py і test_live_hw2.py; live-тест запускає Docker eval через hw2_capture.py,
який делегує незмінному runner. Успішний unittest означає завершений прогін і збережені докази;
lesson-03 всередині має 16 quality failures.

## Докази й вартість

[Аналіз](evidence/run-analysis.json), [повні captures](evidence/runs/), [ризики](residual-risk.md).
Підготовчі manifests фіксують стан до live-серії; остаточні цифри — run-analysis.json.

Три daily: 90 chat requests, 185 model calls, input=438084, output=20890, total=458974 tokens.
Разом із контролем: 91 chat requests, 187 model calls, input=442697, output=21153, total=463850.
Captures узгоджуються із сумою tokens кожного raw report.
Ціна Haiku 4.5: $1/M input та $5/M output ([офіційний прайс](https://platform.claude.com/docs/en/about-claude/pricing)).
Оцінка: $0.542534 за три daily, $0.005928 за контроль, **$0.548462 разом**.
Формула: (input + 5 × output) / 1000000. Judge-викликів немає.
Білінг підтверджено: Cost this month збільшився на **$0.55**, що збігається з $0.548462 після округлення до центів.
Звірено сукупний приріст за серію з контролем; окремі API-виклики та cache-позиції рахунку не звірялися.
[Підтвердження звірки](evidence/billing-reconciliation.json).

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
