const sectionsRoot = document.getElementById("sectionsRoot");
const historyRoot = document.getElementById("historyRoot");
const entryForm = document.getElementById("entryForm");
const employeeNameInput = document.getElementById("employeeName");
const entryDateInput = document.getElementById("entryDate");
const notesInput = document.getElementById("notes");
const resetDraftButton = document.getElementById("resetDraftButton");
const statusMessage = document.getElementById("statusMessage");
const templateSummary = document.getElementById("templateSummary");
const workbookName = document.getElementById("workbookName");

const draftKey = "daily-huddle-entry-draft";

function setStatus(message, tone = "neutral") {
  statusMessage.textContent = message;
  statusMessage.dataset.tone = tone;
}

function formatReferenceValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Blank";
  }
  return `${value}`;
}

function renderTemplate(data) {
  workbookName.textContent = data.workbookName;
  templateSummary.textContent = `${data.fieldCount} tracked rows from ${data.sheetName}`;
  sectionsRoot.innerHTML = "";

  data.sections.forEach((section) => {
    const sectionCard = document.createElement("section");
    sectionCard.className = "section-card";

    const title = document.createElement("h3");
    title.textContent = section.title;
    sectionCard.appendChild(title);

    const sectionGrid = document.createElement("div");
    sectionGrid.className = "section-grid";

    section.fields.forEach((field) => {
      const row = document.createElement("div");
      row.className = "field-row";

      const meta = document.createElement("div");
      meta.className = "field-meta";
      meta.innerHTML = `
        <p class="field-label">${field.label}</p>
        <p class="field-reference">Reference: ${section.headers[0]} ${formatReferenceValue(
          field.referenceValues.left
        )} | ${section.headers[1]} ${formatReferenceValue(field.referenceValues.right)}</p>
      `;

      const inputs = document.createElement("div");
      inputs.className = "field-inputs";
      inputs.innerHTML = `
        <label>
          <span>${section.headers[0]}</span>
          <input type="number" step="any" data-field-key="${field.key}" data-side="left" />
        </label>
        <label>
          <span>${section.headers[1]}</span>
          <input type="number" step="any" data-field-key="${field.key}" data-side="right" />
        </label>
      `;

      row.append(meta, inputs);
      sectionGrid.appendChild(row);
    });

    sectionCard.appendChild(sectionGrid);
    sectionsRoot.appendChild(sectionCard);
  });
}

function collectFormValues() {
  const values = {};
  document.querySelectorAll("input[data-field-key]").forEach((input) => {
    const fieldKey = input.dataset.fieldKey;
    const side = input.dataset.side;
    values[fieldKey] ||= { left: null, right: null };
    values[fieldKey][side] = input.value === "" ? null : Number(input.value);
  });
  return values;
}

function fillFormFromDraft(draft) {
  employeeNameInput.value = draft.employeeName || "";
  entryDateInput.value = draft.entryDate || new Date().toISOString().slice(0, 10);
  notesInput.value = draft.notes || "";

  document.querySelectorAll("input[data-field-key]").forEach((input) => {
    const fieldValues = draft.values?.[input.dataset.fieldKey];
    const value = fieldValues?.[input.dataset.side];
    input.value = value ?? "";
  });
}

function saveDraft() {
  const draft = {
    employeeName: employeeNameInput.value,
    entryDate: entryDateInput.value,
    notes: notesInput.value,
    values: collectFormValues(),
  };
  localStorage.setItem(draftKey, JSON.stringify(draft));
}

function clearDraft() {
  localStorage.removeItem(draftKey);
  entryForm.reset();
  entryDateInput.value = new Date().toISOString().slice(0, 10);
  document.querySelectorAll("input[data-field-key]").forEach((input) => {
    input.value = "";
  });
  setStatus("Draft cleared.", "neutral");
}

function loadDraft() {
  const raw = localStorage.getItem(draftKey);
  if (!raw) {
    entryDateInput.value = new Date().toISOString().slice(0, 10);
    return;
  }
  try {
    fillFormFromDraft(JSON.parse(raw));
    setStatus("Draft restored from this browser.", "neutral");
  } catch {
    entryDateInput.value = new Date().toISOString().slice(0, 10);
  }
}

function renderHistory(submissions) {
  if (!submissions.length) {
    historyRoot.innerHTML = `<div class="empty-state">No entries yet. The first saved submission will appear here.</div>`;
    return;
  }

  historyRoot.innerHTML = submissions
    .map((submission) => {
      const completedRows = Object.values(submission.values || {}).filter(
        (item) => item.left !== null || item.right !== null
      ).length;
      return `
        <article class="history-card">
          <div class="history-topline">
            <strong>${submission.employeeName}</strong>
            <span>${submission.entryDate}</span>
          </div>
          <p>${completedRows} rows filled</p>
          <p class="history-meta">Saved ${submission.submittedAt}</p>
        </article>
      `;
    })
    .join("");
}

async function refreshHistory() {
  const response = await fetch("/api/submissions");
  const submissions = await response.json();
  renderHistory(submissions);
}

async function loadTemplate() {
  const response = await fetch("/api/template");
  const data = await response.json();
  renderTemplate(data);
  loadDraft();
}

entryForm.addEventListener("input", saveDraft);
resetDraftButton.addEventListener("click", clearDraft);

entryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    employeeName: employeeNameInput.value.trim(),
    entryDate: entryDateInput.value,
    notes: notesInput.value.trim(),
    values: collectFormValues(),
  };

  const response = await fetch("/api/submissions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const result = await response.json();
  if (!response.ok) {
    setStatus(result.error || "Unable to save the entry.", "error");
    return;
  }

  localStorage.removeItem(draftKey);
  entryForm.reset();
  document.querySelectorAll("input[data-field-key]").forEach((input) => {
    input.value = "";
  });
  entryDateInput.value = new Date().toISOString().slice(0, 10);
  setStatus("Entry saved successfully.", "success");
  await refreshHistory();
});

await loadTemplate();
await refreshHistory();
