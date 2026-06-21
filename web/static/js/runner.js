// Renderiza lições/exercícios, roda código Python no navegador (Pyodide)
// e libera a conclusão do tópico quando todos os exercícios passam.

(function () {
  // --- 1. Renderizar markdown da lição e dos enunciados ---
  function renderMarkdown() {
    const lessonEl = document.getElementById("lesson-content");
    const lessonMd = document.getElementById("lesson-md");
    if (lessonEl && lessonMd) {
      lessonEl.innerHTML = marked.parse(lessonMd.textContent);
    }
    document.querySelectorAll(".exercise").forEach((ex) => {
      const target = ex.querySelector("[data-prompt]");
      const src = ex.querySelector("[data-prompt-md]");
      if (target && src) target.innerHTML = marked.parse(src.textContent);
    });
  }

  // --- 2. Editores de código (CodeMirror) ---
  const editors = new Map(); // exerciseEl -> CodeMirror instance

  function setupEditors() {
    document.querySelectorAll(".exercise").forEach((ex) => {
      const textarea = ex.querySelector(".code-editor");
      if (!textarea) return;
      const cm = CodeMirror.fromTextArea(textarea, {
        mode: "python",
        theme: "material-darker",
        lineNumbers: true,
        indentUnit: 4,
        viewportMargin: Infinity,
      });
      editors.set(ex, cm);
    });
  }

  // --- 3. Pyodide (carregado sob demanda) ---
  let pyodidePromise = null;
  const statusEl = document.getElementById("pyodide-status");

  function ensurePyodide() {
    if (!pyodidePromise) {
      pyodidePromise = loadPyodide().then((py) => {
        if (statusEl) {
          statusEl.textContent = "✓ Ambiente Python pronto!";
          statusEl.classList.add("ready");
        }
        return py;
      });
    }
    return pyodidePromise;
  }

  // --- 4. Estado de conclusão dos exercícios ---
  const totalExercises = document.querySelectorAll(".exercise").length;
  const passed = new Set();
  const completeBtn = document.getElementById("complete-btn");

  function refreshCompleteButton() {
    if (!completeBtn) return;
    const isDone = completeBtn.classList.contains("is-done");
    if (isDone) return;
    if (totalExercises === 0) {
      completeBtn.disabled = false; // tópico conceitual: liberar logo
    } else if (passed.size >= totalExercises) {
      completeBtn.disabled = false;
      completeBtn.textContent = "Marcar como concluído";
    } else {
      completeBtn.disabled = true;
    }
  }

  // --- 5. Rodar um exercício ---
  async function runExercise(ex) {
    const cm = editors.get(ex);
    const output = ex.querySelector("[data-output]");
    const testCode = ex.querySelector("[data-test-code]").textContent;
    const studentCode = cm.getValue();
    const exId = parseInt(ex.dataset.exerciseId, 10);

    output.hidden = false;
    output.className = "output";
    output.textContent = "Executando…";

    let py;
    try {
      py = await ensurePyodide();
    } catch (e) {
      output.classList.add("err");
      output.textContent = "Não foi possível carregar o ambiente Python. Verifique sua conexão.";
      return;
    }

    py.globals.set("_student_src", studentCode);
    py.globals.set("_test_src", testCode);

    try {
      await py.runPythonAsync(`
_ns = {"_student_code": _student_src}
exec(_student_src, _ns)
exec(_test_src, _ns)
`);
      output.classList.add("ok");
      output.textContent = "✅ Correto! Muito bem.";
      passed.add(exId);
      refreshCompleteButton();
    } catch (err) {
      output.classList.add("err");
      output.textContent = "❌ " + formatPyError(err.message);
    } finally {
      py.globals.delete("_student_src");
      py.globals.delete("_test_src");
    }
  }

  // Extrai a mensagem útil do traceback do Python.
  function formatPyError(message) {
    const lines = message.trim().split("\n").filter((l) => l.trim());
    const last = lines[lines.length - 1] || "Erro desconhecido";
    if (last.startsWith("AssertionError")) {
      const msg = last.replace("AssertionError:", "").trim();
      return msg || "O resultado não passou na verificação. Tente de novo.";
    }
    return last;
  }

  // --- 6. Ligar os botões ---
  function wireButtons() {
    document.querySelectorAll(".exercise").forEach((ex) => {
      const runBtn = ex.querySelector("[data-run]");
      const solBtn = ex.querySelector("[data-solution]");
      const solution = ex.querySelector("[data-solution-code]").textContent;

      runBtn.addEventListener("click", () => runExercise(ex));
      solBtn.addEventListener("click", () => {
        if (confirm("Mostrar a solução? Tente resolver sozinho primeiro 🙂")) {
          editors.get(ex).setValue(solution);
        }
      });
    });

    if (completeBtn) {
      completeBtn.addEventListener("click", async () => {
        if (completeBtn.classList.contains("is-done")) return;
        const topicId = parseInt(completeBtn.dataset.topicId, 10);
        try {
          await Progress.markDone(topicId);
          completeBtn.classList.add("is-done");
          completeBtn.textContent = "✓ Concluído";
          completeBtn.disabled = false;
        } catch (e) {
          alert("Não foi possível salvar o progresso.");
        }
      });
    }
  }

  // --- Inicialização ---
  document.addEventListener("DOMContentLoaded", () => {
    renderMarkdown();
    setupEditors();
    wireButtons();
    refreshCompleteButton();
    if (totalExercises > 0) ensurePyodide(); // começa a carregar em background
  });
})();
