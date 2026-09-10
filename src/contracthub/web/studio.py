"""Web Diff Studio single-page application markup and styles."""


def get_studio_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ContractHub Studio</title>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --green: #238636;
      --green-bg: rgba(35, 134, 54, 0.15);
      --red: #da3633;
      --red-bg: rgba(218, 54, 51, 0.15);
      --yellow: #d29922;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 0.75rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    .brand {
      font-weight: 700;
      font-size: 1.15rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .badge {
      background: rgba(88, 166, 255, 0.15);
      color: var(--accent);
      border: 1px solid rgba(88, 166, 255, 0.3);
      padding: 0.15rem 0.5rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .layout {
      display: flex;
      flex: 1;
      overflow: hidden;
    }
    /* Left Sidebar: Subjects & Timeline */
    aside {
      width: 320px;
      background: #090d13;
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }
    .sidebar-header {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .subject-list {
      flex: 1;
      overflow-y: auto;
      list-style: none;
    }
    .subject-item {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid rgba(48, 54, 61, 0.5);
      cursor: pointer;
      transition: background 0.15s;
    }
    .subject-item:hover, .subject-item.active {
      background: #161b22;
    }
    .subject-title {
      font-weight: 600;
      font-size: 0.875rem;
      color: #e6edf3;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .timeline-container {
      padding: 0.75rem 1rem;
      background: #161b22;
      border-top: 1px solid var(--border);
      max-height: 220px;
      overflow-y: auto;
    }
    .timeline-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.4rem 0;
      font-size: 0.8rem;
    }
    .timeline-badge {
      background: #21262d;
      border: 1px solid var(--border);
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      font-weight: 600;
      color: var(--accent);
    }
    /* Main Diff Area */
    main {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .controls {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem 1.25rem;
      display: flex;
      gap: 1.25rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .field-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    label { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }
    select, button {
      background: #21262d;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.4rem 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
      outline: none;
    }
    button.primary {
      background: #238636;
      border-color: rgba(240, 246, 252, 0.1);
      color: #fff;
      font-weight: 600;
      cursor: pointer;
      margin-left: auto;
    }
    button.primary:hover { background: #2ea043; }
    button.small {
      padding: 0.2rem 0.5rem;
      font-size: 0.75rem;
      cursor: pointer;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      flex: 1;
      min-height: 380px;
    }
    .editor-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .editor-header {
      background: rgba(255, 255, 255, 0.02);
      border-bottom: 1px solid var(--border);
      padding: 0.5rem 1rem;
      font-size: 0.8rem;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    textarea {
      width: 100%;
      flex: 1;
      background: #090d13;
      border: none;
      color: #e6edf3;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.85rem;
      padding: 1rem;
      resize: none;
      outline: none;
    }
    .results-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem 1.25rem;
    }
    .status-banner {
      padding: 0.75rem 1rem;
      border-radius: 6px;
      margin-bottom: 1rem;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.875rem;
    }
    .status-pass {
      background: var(--green-bg);
      border: 1px solid rgba(35, 134, 54, 0.4);
      color: #3fb950;
    }
    .status-fail {
      background: var(--red-bg);
      border: 1px solid rgba(218, 54, 51, 0.4);
      color: #f85149;
    }
    table { width: 100%; border-collapse: collapse; font-size: 0.825rem; }
    th, td { text-align: left; padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--border); }
    th { background: rgba(255, 255, 255, 0.02); color: var(--text-muted); font-weight: 600; }
    .tag-breaking {
      background: rgba(218, 54, 51, 0.2);
      color: #f85149;
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .code-val { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--accent); }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      ContractHub Studio
      <span class="badge">Universal Schema Governance</span>
    </div>
    <div style="font-size: 0.85rem; color: var(--text-muted);">
      Connected API: <code>/v1</code> & <code>Confluent Wire</code>
    </div>
  </header>

  <div class="layout">
    <!-- Left Subject Explorer Sidebar -->
    <aside>
      <div class="sidebar-header">
        <span>REGISTERED SUBJECTS</span>
        <button type="button" class="small" onclick="loadSubjects()">Refresh</button>
      </div>
      <ul id="subjectsList" class="subject-list">
        <li style="padding: 1rem; color: var(--text-muted); font-size: 0.85rem;">Loading subjects...</li>
      </ul>
      <div id="timelineArea" style="display: none;">
        <div class="sidebar-header">
          <span id="timelineSubjectName">VERSIONS</span>
        </div>
        <div id="timelineItems" class="timeline-container"></div>
      </div>
    </aside>

    <!-- Main Diff & Verification Canvas -->
    <main>
      <div class="controls">
        <div class="field-group">
          <label for="schemaType">Format:</label>
          <select id="schemaType">
            <option value="PROTOBUF">Protobuf (Proto3)</option>
            <option value="AVRO">Apache Avro (.avsc)</option>
            <option value="OPENAPI">OpenAPI 3.x</option>
            <option value="JSON_SCHEMA">JSON Schema</option>
          </select>
        </div>

        <div class="field-group">
          <label for="compatMode">Mode:</label>
          <select id="compatMode">
            <option value="FULL">FULL (Backward + Forward)</option>
            <option value="BACKWARD">BACKWARD</option>
            <option value="FORWARD">FORWARD</option>
          </select>
        </div>

        <button type="button" onclick="loadSample()">Load Sample</button>
        <button type="button" class="primary" onclick="runCheck()">Run Compatibility Check</button>
      </div>

      <div class="grid">
        <div class="editor-card">
          <div class="editor-header">
            <span>Base Schema (Old Version / V1)</span>
          </div>
          <textarea id="baseSchema" spellcheck="false" placeholder="Paste base schema here..."></textarea>
        </div>

        <div class="editor-card">
          <div class="editor-header">
            <span>Candidate Schema (New Version / V2)</span>
          </div>
          <textarea id="candidateSchema" spellcheck="false" placeholder="Paste candidate schema here..."></textarea>
        </div>
      </div>

      <div id="resultsArea" class="results-card" style="display: none;">
        <div id="statusBanner" class="status-banner"></div>
        <div id="violationsTableWrapper"></div>
      </div>
    </main>
  </div>

  <script>
    const sampleProtoV1 = `syntax = "proto3";
package commerce.orders;

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
  ORDER_STATUS_CANCELLED = 3;
}

message OrderItem {
  string item_id = 1;
  int32 quantity = 2;
  double price = 3;
}

message OrderEvent {
  string order_id = 1;
  string customer_id = 2;
  OrderStatus status = 3;
  repeated OrderItem items = 4;
  int64 created_at_ms = 5;
}`;

    const sampleProtoV2Breaking = `syntax = "proto3";
package commerce.orders;

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
}

message OrderItem {
  string item_id = 1;
  string quantity = 2;
  double price = 3;
}

message OrderEvent {
  string order_id = 10;
  OrderStatus status = 3;
  repeated OrderItem items = 4;
  int64 created_at_ms = 5;
}`;

    function loadSample() {
      document.getElementById('schemaType').value = 'PROTOBUF';
      document.getElementById('baseSchema').value = sampleProtoV1;
      document.getElementById('candidateSchema').value = sampleProtoV2Breaking;
    }

    async function loadSubjects() {
      const listEl = document.getElementById('subjectsList');
      try {
        const resp = await fetch('/v1/subjects');
        const subjects = await resp.json();
        if (subjects.length === 0) {
          listEl.innerHTML = '<li style="padding: 1rem; color: var(--text-muted); font-size: 0.85rem;">No subjects registered yet.</li>';
          return;
        }
        listEl.innerHTML = subjects.map(s => `
          <li class="subject-item" onclick="selectSubject('${s}')">
            <div class="subject-title">
              <span>${s}</span>
              <span class="timeline-badge">Subject</span>
            </div>
          </li>
        `).join('');
      } catch (err) {
        listEl.innerHTML = '<li style="padding: 1rem; color: #f85149; font-size: 0.85rem;">Failed to fetch subjects.</li>';
      }
    }

    async function selectSubject(name) {
      document.querySelectorAll('.subject-item').forEach(el => el.classList.remove('active'));
      const timelineArea = document.getElementById('timelineArea');
      const timelineItems = document.getElementById('timelineItems');
      const titleEl = document.getElementById('timelineSubjectName');

      titleEl.textContent = name.toUpperCase() + ' VERSIONS';
      timelineArea.style.display = 'block';

      try {
        const resp = await fetch(`/v1/subjects/${name}/versions`);
        const versions = await resp.json();
        timelineItems.innerHTML = versions.map(v => `
          <div class="timeline-item">
            <span class="timeline-badge">V${v}</span>
            <div style="display: flex; gap: 0.25rem;">
              <button class="small" onclick="loadVersionInto('${name}', ${v}, 'base')">Base</button>
              <button class="small" onclick="loadVersionInto('${name}', ${v}, 'candidate')">Candidate</button>
            </div>
          </div>
        `).join('');
      } catch (err) {
        timelineItems.innerHTML = '<p style="color: #f85149; font-size: 0.75rem;">Failed to fetch versions.</p>';
      }
    }

    async function loadVersionInto(subject, version, target) {
      try {
        const resp = await fetch(`/v1/subjects/${subject}/versions/${version}`);
        const data = await resp.json();
        const textarea = target === 'base' ? document.getElementById('baseSchema') : document.getElementById('candidateSchema');
        textarea.value = data.schema;
        if (data.schemaType) {
          document.getElementById('schemaType').value = data.schemaType;
        }
      } catch (err) {
        alert('Failed to load version: ' + err.message);
      }
    }

    async function runCheck() {
      const schemaType = document.getElementById('schemaType').value;
      const mode = document.getElementById('compatMode').value;
      const baseSchema = document.getElementById('baseSchema').value.trim();
      const candidateSchema = document.getElementById('candidateSchema').value.trim();

      if (!baseSchema || !candidateSchema) {
        alert('Please provide both Base and Candidate schemas.');
        return;
      }

      try {
        const resp = await fetch('/v1/diff', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ baseSchema, candidateSchema, schemaType, mode })
        });

        const data = await resp.json();
        const resultsArea = document.getElementById('resultsArea');
        const statusBanner = document.getElementById('statusBanner');
        const wrapper = document.getElementById('violationsTableWrapper');

        resultsArea.style.display = 'block';

        if (data.is_compatible) {
          statusBanner.className = 'status-banner status-pass';
          statusBanner.innerHTML = `<span>Passed: Candidate schema is ${mode} compatible.</span><span>0 Violations</span>`;
          wrapper.innerHTML = '<p style="color: var(--text-muted);">All structural and semantic invariants satisfied.</p>';
        } else {
          statusBanner.className = 'status-banner status-fail';
          statusBanner.innerHTML = `<span>Failed: ${data.breaking_count} breaking violation(s) detected.</span><span>Mode: ${mode}</span>`;

          let rows = data.violations.map(v => `
            <tr>
              <td><span class="tag-breaking">${v.severity}</span></td>
              <td class="code-val">${v.code}</td>
              <td class="code-val" style="color: var(--yellow);">${v.path}</td>
              <td>${v.message}</td>
              <td style="color: #58a6ff;">${v.suggestion || '-'}</td>
            </tr>
          `).join('');

          wrapper.innerHTML = `
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Error Code</th>
                  <th>Path</th>
                  <th>Violation Details</th>
                  <th>Recommendation</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          `;
        }
      } catch (err) {
        alert('Error connecting to ContractHub API: ' + err.message);
      }
    }

    loadSample();
    loadSubjects();
  </script>
</body>
</html>
"""
