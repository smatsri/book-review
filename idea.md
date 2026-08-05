# מערכת סוכני AI לניתוח והעשרת ספרים

> Vision / future design. **Current truth:** [`docs/architecture.md`](docs/architecture.md).  
> Session memory: [`todo.md`](todo.md). Agent workflow: [`AGENTS.md`](AGENTS.md).

## רעיון כללי

המטרה היא לבנות מערכת Multi-Agent שמדמה צוות עריכה ספרותי.

במקום לתת למודל שפה לבצע משימה אחת גדולה, מחלקים את העבודה למספר סוכנים בעלי תפקידים ברורים:

- סוכן קורא ומנתח את הספר.
- סוכן מבקר בודק את איכות הניתוח.
- סוכן עורך מייצר תוצר סופי.
- בהמשך ניתן להוסיף סוכנים נוספים:
  - חוקר מקורות.
  - יוצר הערות שוליים.
  - סוכן תמונות ואיורים.
  - סוכן בדיקת עובדות.
  - סוכן עיצוב ופרסום.

המטרה הסופית:
יצירת גרסה מועשרת של ספר הכוללת:

- תקציר.
- ניתוח ספרותי.
- הערות שוליים.
- איורים.
- הקשרים היסטוריים ורעיוניים.

---

# מודל מחשבתי של Agent

Agent הוא שילוב של:

```
Agent =
    LLM
    +
    Role
    +
    Goal
    +
    Context
    +
    Tools
    +
    State
```

לדוגמה:

## Reader Agent

אחריות:

- קריאת הספר.
- חלוקה לפרקים.
- זיהוי דמויות.
- זיהוי אירועים.
- זיהוי נושאים מרכזיים.
- יצירת ניתוח מובנה.

---

## Critic Agent

אחריות:

- בדיקת איכות הניתוח.
- איתור חוסרים.
- בדיקת עקביות.
- הצעת שיפורים.

---

## Editor Agent

אחריות:

- שילוב המידע.
- כתיבה לקורא אנושי.
- יצירת מסמך סופי.

---

# ארכיטקטורה ראשונית

```
                 Editor Agent
                      |
        +-------------+-------------+
        |                           |
   Reader Agent              Critic Agent
        |
   Book Processing
        |
 Chapters / Notes
```

---

# ארכיטקטורה עתידית

```
                     Supervisor Agent

                           |
        +------------------+------------------+
        |                  |                  |
 Reader Agent       Research Agent     Visual Agent
        |                  |                  |
 Analysis          Footnotes/Sources       Images

                           |
                    Writer Agent

                           |
                    Final Book
```

---

# סביבת פיתוח מומלצת

## Python

בחירה מומלצת להתחלה.

סיבות:

- רוב ספריות ה-Agent נמצאות שם.
- רוב הדוגמאות והמחקרים מתפרסמים שם.
- מתאים מאוד לניסויים מהירים.

---

# ספריות וכלים אפשריים

## LangGraph

ניהול זרימות עבודה בין Agents.

מתאים במיוחד למודל:

```
State
 |
Agent
 |
Decision
 |
Agent
 |
Result
```

---

## LlamaIndex

מתאים לעבודה עם מסמכים:

- ספרים.
- מאמרים.
- מאגרי ידע.

---

## AutoGen / CrewAI

Frameworks לבניית מערכות עם מספר Agents.

---

# מבנה פרויקט התחלתי

```
book-ai/

├── agents/
│   ├── reader.py
│   ├── critic.py
│   └── editor.py
│
├── data/
│   └── book.txt
│
├── state/
│   └── analysis.json
│
├── output/
│   ├── summary.md
│   └── notes.md
│
└── main.py
```

---

# שלבי פיתוח

## שלב 1 - Agent יחיד

מטרה:

להבין עבודה בסיסית עם מודל שפה.

```
Book
 |
LLM
 |
Summary
```

פלט:

סיכום בסיסי של הספר.

---

## שלב 2 - הפרדת תפקידים

הוספת Reader ו-Editor.

```
Book
 |
Reader Agent
 |
Editor Agent
 |
Summary
```

---

## שלב 3 - הוספת ביקורת

הוספת Critic Agent.

```
Reader
 |
Editor
 |
Critic
 |
Revision
 |
Final Output
```

המטרה:

יצירת לולאת שיפור.

---

## שלב 4 - Memory וידע

הוספת יכולת לזכור ולחפש מידע.

טכנולוגיות:

- Embeddings.
- Vector Database.
- RAG (Retrieval Augmented Generation).

דוגמה:

```
Question
   |
Semantic Search
   |
Relevant Chapters
   |
LLM Response
```

---

# שלב 5 - העשרת הספר

## Visual Agent

אחריות:

- זיהוי סצנות מתאימות לאיור.
- יצירת תיאורי תמונה.
- שילוב תמונות.

---

## Footnote Agent

אחריות:

הוספת:

- הסברים היסטוריים.
- מושגים.
- קשרים תרבותיים.
- מקורות.

---

## Layout Agent

אחריות:

הפקת:

- Markdown.
- HTML.
- PDF.
- EPUB.

---

# עקרונות עבודה

## להתחיל קטן

לא להתחיל עם מערכת של 10 Agents.

עדיף:

```
Agent אחד שעובד היטב
        |
הוספת תפקיד נוסף
        |
בדיקה
        |
הרחבה
```

---

## לחשוב על State

במערכות Agents המידע שעובר בין השלבים הוא מרכזי.

לדוגמה:

```json
{
  "book": "The Castle",
  "chapters": [],
  "characters": [],
  "themes": [],
  "analysis": [],
  "criticism": []
}
```

---

## לבנות Feedback Loops

מערכות חזקות בדרך כלל אינן:

```
Prompt -> Answer
```

אלא:

```
Generate
    |
Critique
    |
Improve
    |
Final
```

---

# יעד ראשון מומלץ

גרסה ראשונה:

קלט:

```
ספר בפורמט txt
```

תהליך:

```
Reader Agent

      |

Critic Agent

      |

Editor Agent
```

פלט:

קובץ Markdown המכיל:

- תקציר.
- ניתוח דמויות.
- נושאים מרכזיים.
- הערות ביקורת.
- רעיונות להרחבה.

זהו בסיס שממנו ניתן להתפתח למערכת עריכה ספרותית מלאה.
