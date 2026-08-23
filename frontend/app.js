(() => {
  "use strict";

  const API = "/api/meetings";
  const POLL_INTERVAL_MS = 1500;
  const IN_PROGRESS = new Set(["pending", "transcribing", "summarizing"]);

  // ---- DOM refs -----------------------------------------------------------
  const apiStatusPill = document.getElementById("api-status");
  const meetingListEl = document.getElementById("meeting-list");
  const emptyHint = document.getElementById("empty-hint");
  const meetingCountEl = document.getElementById("meeting-count");

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const fileChip = document.getElementById("file-chip");
  const uploadBtn = document.getElementById("upload-btn");

  const placeholderCard = document.getElementById("placeholder-card");
  const detailCard = document.getElementById("detail-card");
  const detailFilename = document.getElementById("detail-heading");
  const detailSub = document.getElementById("detail-sub");
  const deleteBtn = document.getElementById("delete-btn");

  const pipelineEl = document.getElementById("pipeline");
  const stepsEl = document.getElementById("steps");
  const errorBanner = document.getElementById("error-banner");
  const resultsEl = document.getElementById("results");
  const summaryText = document.getElementById("summary-text");
  const decisionList = document.getElementById("decision-list");
  const actionList = document.getElementById("action-list");
  const transcriptToggle = document.getElementById("transcript-toggle");
  const transcriptBody = document.getElementById("transcript-body");

  // ---- State ----------------------------------------------------------------
  /** @type {Map<number, object>} */
  const meetings = new Map();
  let activeId = null;
  let pollTimer = null;
  let pendingFile = null;

  // ---- Helpers ----------------------------------------------------------------
  const STEP_ORDER = ["pending", "transcribing", "summarizing", "done"];

  function stepIndex(status) {
    const idx = STEP_ORDER.indexOf(status);
    return idx === -1 ? 0 : idx;
  }

  function formatDuration(seconds) {
    if (seconds == null) return null;
    const s = Math.round(seconds);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m}:${String(r).padStart(2, "0")}`;
  }

  function statusLabel(status) {
    return { pending: "Queued", transcribing: "Transcribing…", summarizing: "Summarizing…", done: "Done", failed: "Failed" }[status] || status;
  }

  async function api(path, options) {
    const res = await fetch(`${API}${path}`, options);
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) { /* ignore parse errors */ }
      throw new Error(detail);
    }
    return res.status === 204 ? null : res.json();
  }

  // ---- API status pill --------------------------------------------------------
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error();
      apiStatusPill.textContent = "API online";
      apiStatusPill.className = "pill online";
    } catch {
      apiStatusPill.textContent = "API unreachable";
      apiStatusPill.className = "pill offline";
    }
  }

  // ---- Sidebar -----------------------------------------------------------------
  async function loadMeetingList() {
    const list = await api("");
    meetings.clear();
    list.forEach((m) => meetings.set(m.id, m));
    renderSidebar();
  }

  function renderSidebar() {
    const items = Array.from(meetings.values());
    meetingCountEl.textContent = String(items.length);
    emptyHint.hidden = items.length > 0;

    meetingListEl.querySelectorAll(".meeting-item").forEach((el) => el.remove());

    items.forEach((m) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.className = "meeting-item" + (m.id === activeId ? " active" : "");
      btn.innerHTML = `
        <span class="meeting-item-name">${escapeHtml(m.filename)}</span>
        <span class="meeting-item-meta">
          <span class="status-dot ${m.status}"></span>
          ${statusLabel(m.status)}
        </span>`;
      btn.addEventListener("click", () => selectMeeting(m.id));
      li.appendChild(btn);
      meetingListEl.appendChild(li);
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ---- Detail / pipeline rendering ---------------------------------------------
  function renderDetail(meeting) {
    placeholderCard.hidden = true;
    detailCard.hidden = false;

    detailFilename.textContent = meeting.filename;
    const duration = formatDuration(meeting.duration_seconds);
    detailSub.textContent = [statusLabel(meeting.status), duration ? `${duration} audio` : null]
      .filter(Boolean)
      .join(" · ");

    // Pipeline stepper
    pipelineEl.classList.remove("active", "done", "failed");
    if (meeting.status === "failed") {
      pipelineEl.classList.add("failed");
    } else if (meeting.status === "done") {
      pipelineEl.classList.add("done");
    } else {
      pipelineEl.classList.add("active");
    }

    const currentIdx = meeting.status === "failed" ? stepIndex("pending") : stepIndex(meeting.status);
    stepsEl.querySelectorAll(".step").forEach((stepEl, idx) => {
      stepEl.classList.remove("is-current", "is-complete");
      if (meeting.status !== "failed") {
        if (idx < currentIdx) stepEl.classList.add("is-complete");
        else if (idx === currentIdx) stepEl.classList.add("is-current");
      }
    });

    // Error banner
    if (meeting.status === "failed") {
      errorBanner.hidden = false;
      errorBanner.textContent = meeting.error_message || "Processing failed for an unknown reason.";
    } else {
      errorBanner.hidden = true;
    }

    // Results
    if (meeting.status === "done") {
      resultsEl.hidden = false;
      summaryText.textContent = meeting.summary || "No summary was generated.";

      decisionList.innerHTML = "";
      if (meeting.key_decisions && meeting.key_decisions.length) {
        meeting.key_decisions.forEach((d) => {
          const li = document.createElement("li");
          li.textContent = d;
          decisionList.appendChild(li);
        });
      } else {
        decisionList.innerHTML = `<li class="no-items">No explicit decisions were detected.</li>`;
      }

      actionList.innerHTML = "";
      if (meeting.action_items && meeting.action_items.length) {
        meeting.action_items.forEach((item) => {
          const li = document.createElement("li");
          li.className = "action-item";
          li.innerHTML = `
            <span class="action-item-check" aria-hidden="true"></span>
            <span class="action-item-body">
              <span class="action-item-task">${escapeHtml(item.task)}</span>
              <span class="action-item-meta">
                <span>${escapeHtml(item.owner || "Unassigned")}</span>
                <span>·</span>
                <span>${escapeHtml(item.deadline || "Not specified")}</span>
              </span>
            </span>`;
          actionList.appendChild(li);
        });
      } else {
        actionList.innerHTML = `<li class="no-items">No action items were detected.</li>`;
      }

      transcriptBody.textContent = meeting.transcript || "";
    } else {
      resultsEl.hidden = true;
    }
  }

  async function selectMeeting(id) {
    activeId = id;
    stopPolling();
    renderSidebar();
    try {
      const meeting = await api(`/${id}`);
      meetings.set(id, meeting);
      renderDetail(meeting);
      if (IN_PROGRESS.has(meeting.status)) startPolling(id);
    } catch (err) {
      console.error(err);
    }
  }

  // ---- Polling ------------------------------------------------------------------
  function startPolling(id) {
    stopPolling();
    pollTimer = setInterval(async () => {
      try {
        const meeting = await api(`/${id}`);
        meetings.set(id, meeting);
        if (id === activeId) renderDetail(meeting);
        renderSidebar();
        if (!IN_PROGRESS.has(meeting.status)) stopPolling();
      } catch (err) {
        console.error(err);
        stopPolling();
      }
    }, POLL_INTERVAL_MS);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // ---- Upload -----------------------------------------------------------------
  function handleFileChosen(file) {
    pendingFile = file;
    fileChip.hidden = false;
    fileChip.textContent = file.name;
    uploadBtn.disabled = false;
  }

  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) handleFileChosen(fileInput.files[0]);
  });

  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) handleFileChosen(file);
  });

  uploadBtn.addEventListener("click", async () => {
    if (!pendingFile) return;
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading…";

    const formData = new FormData();
    formData.append("file", pendingFile);

    try {
      const meeting = await api("/upload", { method: "POST", body: formData });
      meetings.set(meeting.id, meeting);
      pendingFile = null;
      fileChip.hidden = true;
      fileInput.value = "";
      renderSidebar();
      await selectMeeting(meeting.id);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      uploadBtn.disabled = true;
      uploadBtn.textContent = "Upload & process";
    }
  });

  // ---- Delete -------------------------------------------------------------------
  deleteBtn.addEventListener("click", async () => {
    if (activeId == null) return;
    if (!confirm("Delete this meeting and its audio file? This cannot be undone.")) return;
    try {
      await api(`/${activeId}`, { method: "DELETE" });
      meetings.delete(activeId);
      activeId = null;
      stopPolling();
      detailCard.hidden = true;
      placeholderCard.hidden = false;
      renderSidebar();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  });

  // ---- Transcript collapse -------------------------------------------------------
  transcriptToggle.addEventListener("click", () => {
    const expanded = transcriptToggle.getAttribute("aria-expanded") === "true";
    transcriptToggle.setAttribute("aria-expanded", String(!expanded));
    transcriptBody.hidden = expanded;
  });

  // ---- Init -----------------------------------------------------------------------
  checkHealth();
  loadMeetingList().catch((err) => console.error("Failed to load meetings:", err));
})();
