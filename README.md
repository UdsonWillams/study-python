# 🐍 Python do Zero

Um app local para **estudar Python** seguindo roadmaps prontos. Você lê uma lição curta,
resolve um exercício **no próprio navegador** e o app corrige na hora. O progresso fica
salvo num banco SQLite local.

O código Python dos exercícios roda **dentro do navegador** via
[Pyodide](https://pyodide.org/) (Python compilado para WebAssembly) — não há servidor
executando código, então é simples e seguro.

## Recursos

- Roadmap **"Python do Zero"** em 5 módulos (do "o que é programação" até funções).
- Editor de código com correção automática por testes.
- Progresso por tópico salvo em SQLite (via SQLAlchemy).
- Conteúdo em arquivos JSON — fácil de editar e expandir.

## Como rodar

Requer **Python 3.10+**.

```bash
# 1. (opcional) crie um ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. instale as dependências
pip install -r requirements.txt

# 3. rode o app
uvicorn app.main:app --reload
```

Abra <http://localhost:8000> no navegador.

> Na primeira vez que abrir um exercício, o Pyodide é baixado (alguns segundos). Depois fica rápido.

## Estrutura do projeto

```
study-python/
├─ app/
│  ├─ main.py            # FastAPI: páginas + API de progresso
│  ├─ database.py        # engine/sessão SQLAlchemy
│  ├─ models.py          # models ORM (Roadmap, Module, Topic, Exercise, Progress)
│  ├─ schemas.py         # modelos Pydantic da API
│  ├─ seed.py            # carrega o conteúdo dos JSONs no banco
│  └─ content/
│     └─ python-do-zero.json   # o roadmap (conteúdo)
├─ web/
│  ├─ templates/         # base.html, index.html, topic.html
│  └─ static/
│     ├─ css/style.css
│     └─ js/runner.js, progress.js
├─ requirements.txt
└─ study.db              # banco SQLite (gerado automaticamente)
```

## Como adicionar novas aulas / roadmaps

Todo o conteúdo vive em `app/content/*.json`. Para criar um novo roadmap, adicione um
arquivo `.json` nessa pasta seguindo o formato:

```jsonc
{
  "slug": "meu-roadmap",          // identificador único (sem espaços)
  "title": "Meu Roadmap",
  "description": "...",
  "position": 1,                   // ordem entre roadmaps
  "modules": [
    {
      "slug": "modulo-1",
      "title": "Módulo 1 — ...",
      "summary": "...",
      "position": 0,
      "topics": [
        {
          "slug": "topico-1",
          "title": "Tópico 1",
          "position": 0,
          "lesson_md": "# Markdown da lição...",
          "exercises": [
            {
              "position": 0,
              "prompt": "Enunciado em markdown.",
              "starter_code": "# código inicial\n",
              "test_code": "assert resultado == 42, 'mensagem de erro'",
              "solution": "resultado = 42"
            }
          ]
        }
      ]
    }
  ]
}
```

Depois é só reiniciar o app. O conteúdo é recarregado a cada inicialização, e o
**progresso já salvo é preservado** (religado pelos `slug` dos tópicos).

### Como funcionam os exercícios

Ao clicar em **Verificar**, o app executa, no navegador:

1. o **código do aluno** (define variáveis/funções);
2. o **`test_code`** no mesmo namespace.

Se o `test_code` rodar sem lançar exceção (os `assert` passam), o exercício é considerado
correto. Use mensagens claras nos `assert` para orientar o aluno. A variável especial
`_student_code` contém o texto do código do aluno (útil para testar saída de `print`,
como no "Hello, World!").

## Tecnologias

FastAPI · Uvicorn · SQLAlchemy · Jinja2 · SQLite · Pyodide · CodeMirror

## Inspiração de conteúdo

- [gto76/python-cheatsheet](https://github.com/gto76/python-cheatsheet) (referência — licença CC BY-NC-SA)
- [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python) (exercícios futuros — licença MIT)
