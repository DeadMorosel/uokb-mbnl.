from pathlib import Path
import json
import re

base = Path(__file__).resolve().parent
q_file = base / 'message (2).txt'
e_file = base / 'message.txt'
if not q_file.exists() or not e_file.exists():
    raise FileNotFoundError('Source files message (2).txt or message.txt not found')

q_text = q_file.read_text(encoding='utf-8')
e_text = e_file.read_text(encoding='utf-8')

# Parse explanations from second file
explanations = {}
for line in e_text.splitlines():
    m = re.match(r'^(\d+) loka:\s*(.*)$', line)
    if m:
        explanations[int(m.group(1))] = m.group(2).strip()

# Parse questions from first file
blocks = []
block = []
for line in q_text.splitlines():
    if re.match(r'^(\d+)\.', line):
        if block:
            blocks.append(block)
            block = []
    if line.strip() or block:
        block.append(line)
if block:
    blocks.append(block)

questions = []
for block in blocks:
    header = block[0]
    m = re.match(r'^(\d+)\.(.*)$', header)
    if not m:
        continue
    num = int(m.group(1))
    question_text = m.group(2).strip()
    opts = {}
    answer = None
    for line in block[1:]:
        line = line.strip()
        if not line:
            continue
        mopt = re.match(r'^([A-E])\.\s*(.*)$', line)
        if mopt:
            opts[mopt.group(1)] = mopt.group(2).strip()
            continue
        mans = re.match(r'^ANSWER:\s*([A-E])', line)
        if mans:
            answer = mans.group(1)
            continue
        mtab = re.match(r'^([A-E])\t+(.*)$', line)
        if mtab:
            opts[mtab.group(1)] = mtab.group(2).strip()
    if answer and opts:
        questions.append({
            'num': num,
            'question': question_text,
            'options': opts,
            'answer': answer,
            'explanation': explanations.get(num, '')
        })

if not questions:
    raise ValueError('No questions parsed from message.txt')

html = f"""<!DOCTYPE html>
<html lang='ru'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>Квиз в стиле Kahoot</title>
<style>
body{{font-family:Arial,sans-serif;background:radial-gradient(circle at top,#4b79a1,#283e51);color:#fff;margin:0;min-height:100vh;}}
.container{{max-width:1000px;margin:0 auto;padding:16px;}}
.header{{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;}}
.header h1{{font-size:1.9rem;margin:0;flex:1 1 100%;}}
.status-bar{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;}}
.status-item{{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.14);padding:12px 14px;border-radius:16px;font-size:.95rem;box-shadow:0 12px 28px rgba(0,0,0,.16);}}
.progress-container{{width:100%;background:rgba(255,255,255,.15);height:12px;border-radius:999px;overflow:hidden;margin-top:12px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);}}
.progress-fill{{height:100%;width:0%;background:linear-gradient(90deg,#38bdf8,#22c55e);transition:width .35s ease;}}
.card{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);border-radius:24px;padding:22px;margin-top:24px;box-shadow:0 22px 60px rgba(0,0,0,.32);}}
.question-number{{font-size:.95rem;opacity:.85;margin-bottom:12px;}}
.question{{font-size:1.54rem;line-height:1.45;margin-bottom:22px;}}
.options{{display:grid;grid-template-columns:1fr;gap:14px;}}
.option-btn{{border:none;padding:18px 20px;border-radius:18px;font-size:1rem;cursor:pointer;text-align:left;transition:.22s;box-shadow:0 12px 22px rgba(0,0,0,.18);color:#1f2937;background:#f8fafc;min-height:64px;}}
.option-btn:hover{{transform:translateY(-2px);}}
.option-btn.correct{{background:#22c55e;color:#fff;}}
.option-btn.wrong{{background:#ef4444;color:#fff;}}
.footer{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-top:22px;}}
.footer button{{padding:16px 24px;border:none;border-radius:16px;font-size:1rem;cursor:pointer;background:#38bdf8;color:#1e293b;transition:.18s;}}
.footer button:hover{{background:#0ea5e9;}}
.result{{margin-top:16px;padding:18px;border-radius:16px;background:rgba(0,0,0,.24);}}
.explanation{{margin-top:14px;padding:18px;border-radius:16px;background:rgba(255,255,255,.08);color:#f8fafc;font-size:1rem;line-height:1.7;}}
.nav-panel{{margin-top:24px;padding:16px;background:rgba(255,255,255,.08);border-radius:16px;border:1px solid rgba(255,255,255,.12);}}
.nav-title{{font-size:.9rem;opacity:.8;margin-bottom:12px;text-transform:uppercase;}}
.nav-buttons{{display:grid;grid-template-columns:repeat(auto-fill,minmax(40px,1fr));gap:8px;}}
.nav-btn{{border:2px solid rgba(255,255,255,.3);background:rgba(255,255,255,.08);color:#fff;width:40px;height:40px;border-radius:8px;cursor:pointer;font-size:.9rem;transition:.2s;font-weight:500;}}
.nav-btn:hover{{background:rgba(255,255,255,.15);border-color:rgba(255,255,255,.5);}}
.nav-btn.current{{background:#38bdf8;border-color:#38bdf8;color:#1e293b;}}
.nav-btn.answered{{background:#22c55e;border-color:#22c55e;color:#fff;}}
.nav-btn.pending{{background:rgba(239,68,68,.3);border-color:#ef4444;color:#fca5a5;}}
@media (max-width:680px){{
  .container{{padding:14px;}}
  .header h1{{font-size:1.6rem;}}
  .status-item{{flex:1 1 100%;justify-content:space-between;}}
  .question{{font-size:1.28rem;}}
  .option-btn{{font-size:1rem;min-height:70px;}}
  .footer button{{width:100%;}}
  .nav-buttons{{grid-template-columns:repeat(auto-fill,minmax(35px,1fr));}}
  .nav-btn{{width:35px;height:35px;font-size:.8rem;}}
}}
</style>
</head>
<body>
<div class='container'>
<div class='header'>
<h1>Квиз в стиле Kahoot</h1>
<div class='status-bar'>
  <div class='status-item'>Осталось: <strong id='remaining'>{len(questions)}</strong></div>
  <div class='status-item'>Всего: <strong id='total'>{len(questions)}</strong></div>
  <div class='status-item'>Баллы: <strong id='score'>0</strong></div>
</div>
<div class='progress-container'><div class='progress-fill' id='progress-fill'></div></div>
</div>
<div class='card'>
<div class='question-number' id='question-number'></div>
<div class='question' id='question'></div>
<div class='options' id='options'></div>
<div class='result' id='result' style='display:none;'></div>
<div class='explanation' id='explanation' style='display:none;'></div>
<div class='nav-panel'>
  <div class='nav-title'>Навигация по вопросам</div>
  <div class='nav-buttons' id='nav-buttons'></div>
</div>
<div class='footer'>
<button id='nextBtn' disabled>Следующий вопрос</button>
<button id='restartBtn' style='display:none;'>Пройти заново</button>
</div>
</div>
</div>
<script>
const questions = {json.dumps(questions, ensure_ascii=False)};
const total = questions.length;
let score = 0;
const pending = Array.from({{length: total}}, (_, i) => i);
let currentIndex = null;
const correctSet = new Set();
const remainingEl = document.getElementById('remaining');
const totalEl = document.getElementById('total');
const scoreEl = document.getElementById('score');
const progressFill = document.getElementById('progress-fill');
const qNumEl = document.getElementById('question-number');
const qEl = document.getElementById('question');
const optionsEl = document.getElementById('options');
const resultEl = document.getElementById('result');
const explEl = document.getElementById('explanation');
const nextBtn = document.getElementById('nextBtn');
const restartBtn = document.getElementById('restartBtn');
const navButtonsEl = document.getElementById('nav-buttons');
function shuffle(array) {{
  for (let i = array.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }}
  return array;
}}
function updateNavigation() {{
  navButtonsEl.innerHTML = '';
  for (let i = 0; i < total; i++) {{
    const btn = document.createElement('button');
    btn.className = 'nav-btn';
    btn.textContent = i + 1;
    btn.dataset.index = i;
    
    if (i === currentIndex) {{
      btn.classList.add('current');
    }} else if (correctSet.has(i)) {{
      btn.classList.add('answered');
    }} else if (pending.includes(i)) {{
      btn.classList.add('pending');
    }}
    
    btn.addEventListener('click', () => jumpToQuestion(i));
    navButtonsEl.appendChild(btn);
  }}
}}
function jumpToQuestion(index) {{
  if (index < 0 || index >= total) return;
  currentIndex = index;
  renderQuestionByIndex();
}}
function updateProgress() {{
  const answered = correctSet.size;
  const percent = total ? Math.round((answered / total) * 100) : 100;
  remainingEl.textContent = total - answered;
  totalEl.textContent = total;
  progressFill.style.width = `${{percent}}%`;
  updateNavigation();
}}
function getNextQuestionIndex() {{
  if (pending.length === 0) {{
    return null;
  }}
  return pending.shift();
}}
function renderQuestion() {{
  const nextIndex = getNextQuestionIndex();
  if (nextIndex === null) {{
    showFinal();
    return;
  }}
  currentIndex = nextIndex;
  renderQuestionByIndex();
}}
function renderQuestionByIndex() {{
  const item = questions[currentIndex];
  updateProgress();
  qNumEl.textContent = `Вопрос ${{item.num}}`;
  qEl.textContent = item.question;
  optionsEl.innerHTML = '';
  resultEl.style.display = 'none';
  explEl.style.display = 'none';
  nextBtn.disabled = true;
  nextBtn.textContent = 'Следующий вопрос';
  const keys = shuffle(Object.keys(item.options));
  for (const key of keys) {{
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.textContent = `${{key}}. ${{item.options[key]}}`;
    btn.dataset.key = key;
    btn.addEventListener('click', onSelect);
    optionsEl.appendChild(btn);
  }}
}}
function onSelect(event) {{
  const key = event.currentTarget.dataset.key;
  const item = questions[currentIndex];
  const buttons = optionsEl.querySelectorAll('button');
  buttons.forEach(btn => {{
    const btnKey = btn.dataset.key;
    btn.disabled = true;
    if (btnKey === item.answer) btn.classList.add('correct');
    if (btnKey === key && key !== item.answer) btn.classList.add('wrong');
  }});
  const correct = key === item.answer;
  if (correct) {{
    if (!correctSet.has(currentIndex)) {{
      correctSet.add(currentIndex);
      score += 10;
      scoreEl.textContent = score;
    }}
    // remove any future scheduled occurrence of this question
    for (let i = pending.length - 1; i >= 0; i--) {{
      if (pending[i] === currentIndex) pending.splice(i, 1);
    }}
  }} else {{
    // schedule this question to reappear after 3 subsequent questions
    if (!pending.includes(currentIndex)) {{
      const insertPos = Math.min(3, pending.length);
      pending.splice(insertPos, 0, currentIndex);
    }}
  }}
  resultEl.style.display = 'block';
  resultEl.textContent = correct ? 'Верно! Отлично.' : `Неверно. Правильный ответ: ${{item.answer}}.`;
  if (item.explanation) {{
    explEl.style.display = 'block';
    explEl.textContent = item.explanation;
  }}
  nextBtn.disabled = false;
  if (pending.length === 0) {{
    nextBtn.textContent = 'Узнать результат';
  }}
}}
nextBtn.addEventListener('click', () => {{
  renderQuestion();
}});
restartBtn.addEventListener('click', () => {{
  pending.splice(0, pending.length, ...Array.from({{length: total}}, (_, i) => i));
  correctSet.clear();
  score = 0;
  scoreEl.textContent = score;
  currentIndex = null;
  nextBtn.textContent = 'Следующий вопрос';
  nextBtn.style.display = 'inline-block';
  restartBtn.style.display = 'none';
  renderQuestion();
}});
function showFinal() {{
  optionsEl.innerHTML = '';
  qNumEl.textContent = 'Финиш';
  qEl.textContent = `Вы набрали ${{score}} из ${{total * 10}} возможных.`;
  resultEl.style.display = 'block';
  resultEl.textContent = correctSet.size === total ? 'Все вопросы отвечены правильно! 🎉' : `Ответлено правильно: ${{correctSet.size}}/${{total}}`;
  explEl.style.display = 'none';
  nextBtn.disabled = true;
  nextBtn.style.display = 'none';
  restartBtn.style.display = 'inline-block';
  updateNavigation();
}}
renderQuestion();
</script>
</body>
</html>"""

(output := base / 'test1.html').write_text(html, encoding='utf-8')
print(f'Created {output} with {len(questions)} questions.')
