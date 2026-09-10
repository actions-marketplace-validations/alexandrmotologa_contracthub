"""Web Diff Studio single-page application markup and styles."""


def get_studio_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ContractHub Studio - Universal Schema Governance</title>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --card-header: #1f242c;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --accent-hover: #79b8ff;
      --green: #238636;
      --green-hover: #2ea043;
      --green-bg: rgba(35, 134, 54, 0.15);
      --red: #da3633;
      --red-bg: rgba(218, 54, 51, 0.15);
      --yellow: #d29922;
      --yellow-bg: rgba(210, 153, 34, 0.15);
      --purple: #a371f7;
      --purple-bg: rgba(163, 113, 247, 0.15);
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
      padding: 0.6rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    .brand-section {
      display: flex;
      align-items: center;
      gap: 1rem;
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
    .nav-tabs {
      display: flex;
      gap: 0.5rem;
    }
    .nav-tab {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.4rem 0.9rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.15s ease;
    }
    .nav-tab:hover {
      color: var(--text);
      background: rgba(255, 255, 255, 0.04);
    }
    .nav-tab.active {
      background: var(--card-header);
      color: #fff;
      border-color: var(--border);
      font-weight: 600;
    }
    .layout {
      display: flex;
      flex: 1;
      overflow: hidden;
    }
    /* Left Sidebar: Subjects & Timeline */
    aside {
      width: 290px;
      background: #090d13;
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }
    .sidebar-header {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
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
      padding: 0.65rem 1rem;
      border-bottom: 1px solid rgba(48, 54, 61, 0.4);
      cursor: pointer;
      transition: background 0.15s;
    }
    .subject-item:hover, .subject-item.active {
      background: #161b22;
    }
    .subject-title {
      font-weight: 600;
      font-size: 0.85rem;
      color: #e6edf3;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .timeline-container {
      padding: 0.5rem 0.75rem;
      background: #161b22;
      border-top: 1px solid var(--border);
      max-height: 200px;
      overflow-y: auto;
    }
    .timeline-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.35rem 0.25rem;
      font-size: 0.8rem;
    }
    .timeline-badge {
      background: #21262d;
      border: 1px solid var(--border);
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      font-weight: 600;
      color: var(--accent);
      font-size: 0.75rem;
    }
    /* Tab Panes */
    main {
      flex: 1;
      overflow-y: auto;
      padding: 1.25rem 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .tab-content {
      display: none;
      flex-direction: column;
      gap: 1rem;
      flex: 1;
    }
    .tab-content.active {
      display: flex;
    }
    .controls {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem 1.25rem;
      display: flex;
      gap: 1rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .field-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    label { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }
    select, button, input {
      background: #21262d;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.4rem 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
      outline: none;
    }
    select:focus, input:focus, textarea:focus {
      border-color: var(--accent);
    }
    button {
      cursor: pointer;
      font-weight: 500;
      transition: background 0.15s, border-color 0.15s;
    }
    button:hover {
      background: #30363d;
    }
    button.primary {
      background: var(--green);
      border-color: rgba(240, 246, 252, 0.1);
      color: #fff;
      font-weight: 600;
    }
    button.primary:hover { background: var(--green-hover); }
    button.accent {
      background: #1f6feb;
      border-color: rgba(240, 246, 252, 0.1);
      color: #fff;
      font-weight: 600;
    }
    button.accent:hover { background: #388bfd; }
    button.remedy {
      background: #8957e5;
      color: #fff;
      font-weight: 600;
      border-color: rgba(240, 246, 252, 0.1);
    }
    button.remedy:hover { background: #9e6cf2; }
    button.small {
      padding: 0.2rem 0.5rem;
      font-size: 0.75rem;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      flex: 1;
      min-height: 360px;
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
      background: var(--card-header);
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
      padding: 0.9rem;
      resize: none;
      outline: none;
      min-height: 280px;
      tab-size: 2;
    }
    .results-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .status-banner {
      padding: 0.75rem 1rem;
      border-radius: 6px;
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
    .semver-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.8rem;
      border-radius: 6px;
      font-size: 0.825rem;
      font-weight: 600;
      background: rgba(88, 166, 255, 0.12);
      border: 1px solid rgba(88, 166, 255, 0.3);
      color: var(--accent);
    }
    .semver-major {
      background: var(--red-bg);
      border-color: rgba(218, 54, 51, 0.4);
      color: #f85149;
    }
    .semver-minor {
      background: var(--yellow-bg);
      border-color: rgba(210, 153, 34, 0.4);
      color: var(--yellow);
    }
    .semver-patch {
      background: var(--green-bg);
      border-color: rgba(35, 134, 54, 0.4);
      color: #3fb950;
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
    .tag-warning {
      background: rgba(210, 153, 34, 0.2);
      color: var(--yellow);
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .code-val { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--accent); }
    .actions-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      font-size: 0.825rem;
      padding: 0.5rem 0;
    }
    .action-item {
      padding: 0.5rem 0.75rem;
      background: #090d13;
      border: 1px solid var(--border);
      border-radius: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand-section">
      <div class="brand">
        ContractHub Studio
        <span class="badge">v0.1.0</span>
      </div>
      <nav class="nav-tabs">
        <button type="button" class="nav-tab active" id="tabBtnDiff" onclick="switchTab('diff')">🔍 Schema Diff & SemVer</button>
        <button type="button" class="nav-tab" id="tabBtnValidator" onclick="switchTab('validator')">🧪 Payload Validator</button>
        <button type="button" class="nav-tab" id="tabBtnCodegen" onclick="switchTab('codegen')">⚡ Client Codegen</button>
      </nav>
    </div>
    <div style="font-size: 0.8rem; color: var(--text-muted); display: flex; gap: 1rem; align-items: center;">
      <span>REST API: <code class="code-val">/v1</code></span>
      <span>Confluent Registry: <code class="code-val">Wire-compatible</code></span>
    </div>
  </header>

  <div class="layout">
    <!-- Left Subject Explorer Sidebar -->
    <aside>
      <div class="sidebar-header">
        <span>SUBJECT REGISTRY</span>
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

    <!-- Main Content Area -->
    <main>
      <!-- TAB 1: SCHEMA DIFF & SEMVER -->
      <div id="tabContentDiff" class="tab-content active">
        <div class="controls">
          <div class="field-group">
            <label for="schemaType">Format:</label>
            <select id="schemaType" onchange="onFormatChanged()">
              <option value="PROTOBUF">Protobuf (Proto3)</option>
              <option value="AVRO">Apache Avro (.avsc)</option>
              <option value="OPENAPI">OpenAPI 3.x</option>
              <option value="JSON_SCHEMA">JSON Schema</option>
              <option value="GRAPHQL">GraphQL SDL (.graphql)</option>
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

          <div class="field-group">
            <label for="currentVersionInput">Base Version:</label>
            <input type="text" id="currentVersionInput" value="1.0.0" style="width: 80px;" placeholder="1.0.0">
          </div>

          <button type="button" onclick="loadSampleTemplate()">Load Sample</button>
          <button type="button" class="remedy" id="btnAutoFix" onclick="runAutoFix()" style="display: none;">🛠 Auto-Fix Candidate</button>
          <button type="button" class="primary" style="margin-left: auto;" onclick="runFullCheck()">Compare & Recommend SemVer</button>
        </div>

        <div class="grid">
          <div class="editor-card">
            <div class="editor-header">
              <span>Base Schema (V1 / Previous)</span>
              <button type="button" class="small" onclick="copyToClipboard('baseSchema')">Copy</button>
            </div>
            <textarea id="baseSchema" spellcheck="false" placeholder="Paste base schema here..."></textarea>
          </div>

          <div class="editor-card">
            <div class="editor-header">
              <span>Candidate Schema (V2 / Proposed)</span>
              <button type="button" class="small" onclick="copyToClipboard('candidateSchema')">Copy</button>
            </div>
            <textarea id="candidateSchema" spellcheck="false" placeholder="Paste candidate schema here..."></textarea>
          </div>
        </div>

        <div id="resultsArea" class="results-card" style="display: none;">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div id="statusBanner" class="status-banner" style="flex: 1; margin-bottom: 0;"></div>
            <div id="semverBadgeArea"></div>
          </div>
          <div id="semverRationaleArea" style="font-size: 0.85rem; color: var(--text-muted); padding: 0.25rem 0.5rem;"></div>
          <div id="violationsTableWrapper"></div>
        </div>
      </div>

      <!-- TAB 2: PAYLOAD VALIDATOR -->
      <div id="tabContentValidator" class="tab-content">
        <div class="controls">
          <div class="field-group">
            <label for="valSchemaType">Format:</label>
            <select id="valSchemaType">
              <option value="PROTOBUF">Protobuf (Proto3)</option>
              <option value="AVRO">Apache Avro (.avsc)</option>
              <option value="OPENAPI">OpenAPI 3.x</option>
              <option value="JSON_SCHEMA">JSON Schema</option>
              <option value="GRAPHQL">GraphQL SDL (.graphql)</option>
            </select>
          </div>

          <div class="field-group">
            <label for="valTargetEntity">Target Entity / Type:</label>
            <input type="text" id="valTargetEntity" placeholder="(Optional, e.g. User)" style="width: 160px;">
          </div>

          <button type="button" onclick="syncSchemaFromCandidate()">Use Candidate Schema</button>
          <button type="button" onclick="generateMockPayload()">Generate Synthetic Mock</button>
          <button type="button" class="primary" style="margin-left: auto;" onclick="runPayloadValidation()">Validate Payload</button>
        </div>

        <div class="grid">
          <div class="editor-card">
            <div class="editor-header">
              <span>Schema Specification</span>
              <span style="font-size: 0.75rem; color: var(--text-muted);">Contract definition</span>
            </div>
            <textarea id="valSchema" spellcheck="false" placeholder="Paste contract schema definition here..."></textarea>
          </div>

          <div class="editor-card">
            <div class="editor-header">
              <span>JSON Payload / Instance</span>
              <span style="font-size: 0.75rem; color: var(--text-muted);">Message or API payload to validate</span>
            </div>
            <textarea id="valPayload" spellcheck="false" placeholder='{ "id": "123", ... }'></textarea>
          </div>
        </div>

        <div id="valResultsArea" class="results-card" style="display: none;">
          <div id="valStatusBanner" class="status-banner"></div>
          <div id="valErrorsWrapper"></div>
        </div>
      </div>

      <!-- TAB 3: CLIENT CODE GENERATION -->
      <div id="tabContentCodegen" class="tab-content">
        <div class="controls">
          <div class="field-group">
            <label for="cgTarget">Target Language:</label>
            <select id="cgTarget" onchange="runCodegen()">
              <option value="typescript">TypeScript Interfaces & Enums</option>
              <option value="pydantic">Python Pydantic v2 Models</option>
            </select>
          </div>

          <div class="field-group">
            <label for="cgSchemaType">Format:</label>
            <select id="cgSchemaType" onchange="runCodegen()">
              <option value="PROTOBUF">Protobuf (Proto3)</option>
              <option value="AVRO">Apache Avro (.avsc)</option>
              <option value="OPENAPI">OpenAPI 3.x</option>
              <option value="JSON_SCHEMA">JSON Schema</option>
              <option value="GRAPHQL">GraphQL SDL (.graphql)</option>
            </select>
          </div>

          <button type="button" onclick="syncSchemaForCodegen()">Use Candidate Schema</button>
          <button type="button" class="accent" style="margin-left: auto;" onclick="copyToClipboard('cgOutput')">Copy Generated Code</button>
        </div>

        <div class="grid">
          <div class="editor-card">
            <div class="editor-header">
              <span>Input Schema Contract</span>
            </div>
            <textarea id="cgSchema" spellcheck="false" placeholder="Paste schema here..."></textarea>
          </div>

          <div class="editor-card">
            <div class="editor-header">
              <span id="cgOutputTitle">Generated Client Code</span>
            </div>
            <textarea id="cgOutput" readonly spellcheck="false" placeholder="Generated code will appear here..."></textarea>
          </div>
        </div>
      </div>
    </main>
  </div>

  <script>
    // Samples for each format
    const samples = {
      PROTOBUF: {
        base: `syntax = "proto3";
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
}`,
        cand: `syntax = "proto3";
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
}`
      },
      AVRO: {
        base: JSON.stringify({
          type: "record",
          name: "UserEvent",
          namespace: "com.example",
          fields: [
            { name: "userId", type: "string" },
            { name: "email", type: "string" }
          ]
        }, null, 2),
        cand: JSON.stringify({
          type: "record",
          name: "UserEvent",
          namespace: "com.example",
          fields: [
            { name: "userId", type: "string" },
            { name: "email", type: "string" },
            { name: "phoneNumber", type: "string" }
          ]
        }, null, 2)
      },
      OPENAPI: {
        base: JSON.stringify({
          openapi: "3.0.0",
          info: { title: "Pet Store", version: "1.0.0" },
          paths: {
            "/pets": {
              get: { summary: "List pets", responses: { "200": { description: "ok" } } },
              post: { summary: "Create pet", responses: { "201": { description: "created" } } }
            },
            "/pets/{id}": {
              get: { summary: "Get pet", responses: { "200": { description: "ok" } } },
              delete: { summary: "Delete pet", responses: { "204": { description: "deleted" } } }
            }
          }
        }, null, 2),
        cand: JSON.stringify({
          openapi: "3.0.0",
          info: { title: "Pet Store", version: "2.0.0" },
          paths: {
            "/pets": {
              get: { summary: "List pets", responses: { "200": { description: "ok" } } }
            }
          }
        }, null, 2)
      },
      JSON_SCHEMA: {
        base: JSON.stringify({
          $schema: "http://json-schema.org/draft-07/schema#",
          type: "object",
          properties: {
            id: { type: "string" },
            username: { type: "string" }
          },
          required: ["id"]
        }, null, 2),
        cand: JSON.stringify({
          $schema: "http://json-schema.org/draft-07/schema#",
          type: "object",
          properties: {
            id: { type: "string" },
            username: { type: "string" },
            age: { type: "integer" }
          },
          required: ["id", "age"]
        }, null, 2)
      },
      GRAPHQL: {
        base: `type User {
  id: ID!
  username: String!
  email: String!
  bio: String
}

input CreateUserInput {
  username: String!
  email: String!
}`,
        cand: `type User {
  id: ID!
  email: String!
}

input CreateUserInput {
  username: String!
  email: String!
  inviteCode: String!
}`
      }
    };

    function switchTab(tabName) {
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      if (tabName === 'diff') {
        document.getElementById('tabBtnDiff').classList.add('active');
        document.getElementById('tabContentDiff').classList.add('active');
      } else if (tabName === 'validator') {
        document.getElementById('tabBtnValidator').classList.add('active');
        document.getElementById('tabContentValidator').classList.add('active');
        if (!document.getElementById('valSchema').value) {
          syncSchemaFromCandidate();
        }
      } else if (tabName === 'codegen') {
        document.getElementById('tabBtnCodegen').classList.add('active');
        document.getElementById('tabContentCodegen').classList.add('active');
        if (!document.getElementById('cgSchema').value) {
          syncSchemaForCodegen();
        }
        runCodegen();
      }
    }

    function onFormatChanged() {
      const type = document.getElementById('schemaType').value;
      document.getElementById('valSchemaType').value = type;
      document.getElementById('cgSchemaType').value = type;
      loadSampleTemplate();
    }

    function loadSampleTemplate() {
      const type = document.getElementById('schemaType').value;
      const s = samples[type] || samples.PROTOBUF;
      document.getElementById('baseSchema').value = s.base;
      document.getElementById('candidateSchema').value = s.cand;
      document.getElementById('btnAutoFix').style.display = 'none';
      document.getElementById('resultsArea').style.display = 'none';
    }

    async function copyToClipboard(elementId) {
      const el = document.getElementById(elementId);
      if (el) {
        await navigator.clipboard.writeText(el.value);
        alert('Copied to clipboard!');
      }
    }

    async function loadSubjects() {
      const listEl = document.getElementById('subjectsList');
      try {
        const resp = await fetch('/v1/subjects');
        const subjects = await resp.json();
        if (subjects.length === 0) {
          listEl.innerHTML = '<li style="padding: 1rem; color: var(--text-muted); font-size: 0.85rem;">No registered subjects.</li>';
          return;
        }
        listEl.innerHTML = subjects.map(s => `
          <li class="subject-item" id="subject-${s}" onclick="selectSubject('${s}')">
            <div class="subject-title">
              <span>${s}</span>
              <span class="timeline-badge">Subject</span>
            </div>
          </li>
        `).join('');
        if (subjects.length > 0) {
          selectSubject(subjects[0]);
        }
      } catch (err) {
        listEl.innerHTML = '<li style="padding: 1rem; color: #f85149; font-size: 0.85rem;">Failed to fetch subjects.</li>';
      }
    }

    async function selectSubject(name) {
      document.querySelectorAll('.subject-item').forEach(el => el.classList.remove('active'));
      const activeEl = document.getElementById('subject-' + name);
      if (activeEl) activeEl.classList.add('active');

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
          document.getElementById('valSchemaType').value = data.schemaType;
          document.getElementById('cgSchemaType').value = data.schemaType;
        }
      } catch (err) {
        alert('Failed to load version: ' + err.message);
      }
    }

    async function runFullCheck() {
      const schemaType = document.getElementById('schemaType').value;
      const mode = document.getElementById('compatMode').value;
      const baseSchema = document.getElementById('baseSchema').value.trim();
      const candidateSchema = document.getElementById('candidateSchema').value.trim();
      const currentVersion = document.getElementById('currentVersionInput').value.trim() || '1.0.0';

      if (!baseSchema || !candidateSchema) {
        alert('Please provide both Base and Candidate schemas.');
        return;
      }

      try {
        // Parallel fetch for Diff and SemVer
        const [diffResp, semverResp] = await Promise.all([
          fetch('/v1/diff', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ baseSchema, candidateSchema, schemaType, mode })
          }),
          fetch('/v1/semver', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ baseSchema, candidateSchema, current_version: currentVersion, schemaType, mode })
          })
        ]);

        const diffData = await diffResp.json();
        const semverData = await semverResp.json();

        const resultsArea = document.getElementById('resultsArea');
        const statusBanner = document.getElementById('statusBanner');
        const badgeArea = document.getElementById('semverBadgeArea');
        const rationaleArea = document.getElementById('semverRationaleArea');
        const wrapper = document.getElementById('violationsTableWrapper');
        const btnAutoFix = document.getElementById('btnAutoFix');

        resultsArea.style.display = 'block';

        // SemVer Badge styling
        let bumpClass = 'semver-patch';
        if (semverData.bump_type === 'MAJOR') bumpClass = 'semver-major';
        else if (semverData.bump_type === 'MINOR') bumpClass = 'semver-minor';

        const recVer = semverData.recommended_version || semverData.next_version || '2.0.0';
        const semReason = semverData.reason || semverData.rationale || 'Compatibility verified.';

        badgeArea.innerHTML = `
          <div class="semver-badge ${bumpClass}">
            <span>${semverData.current_version} ➔ Recommended: ${recVer} (${semverData.bump_type})</span>
          </div>
        `;
        rationaleArea.textContent = 'SemVer Analysis: ' + semReason;

        if (diffData.is_compatible) {
          btnAutoFix.style.display = 'none';
          statusBanner.className = 'status-banner status-pass';
          statusBanner.innerHTML = `<span>Passed: Candidate schema is ${mode} compatible.</span><span>0 Violations</span>`;
          wrapper.innerHTML = '<p style="color: var(--text-muted); padding: 0.5rem 0;">All structural and semantic invariants satisfied.</p>';
        } else {
          btnAutoFix.style.display = 'inline-block';
          statusBanner.className = 'status-banner status-fail';
          const breakingCount = (diffData.violations || []).filter(v => v.severity === 'BREAKING').length;
          statusBanner.innerHTML = `<span>Failed: ${breakingCount} breaking violation(s) detected.</span><span>Mode: ${mode}</span>`;

          let rows = diffData.violations.map(v => {
            const isBreaking = v.severity === 'BREAKING';
            const tagClass = isBreaking ? 'tag-breaking' : 'tag-warning';
            return `
              <tr>
                <td><span class="${tagClass}">${v.severity}</span></td>
                <td class="code-val">${v.code}</td>
                <td class="code-val" style="color: var(--yellow);">${v.path}</td>
                <td>${v.message}</td>
                <td style="color: #58a6ff;">${v.suggestion || '-'}</td>
              </tr>
            `;
          }).join('');

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

    async function runAutoFix() {
      const schemaType = document.getElementById('schemaType').value;
      const baseSchema = document.getElementById('baseSchema').value.trim();
      const candidateSchema = document.getElementById('candidateSchema').value.trim();

      try {
        const resp = await fetch('/v1/fix', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ baseSchema, candidateSchema, schemaType })
        });

        const data = await resp.json();
        if (data.actions && data.actions.length > 0) {
          document.getElementById('candidateSchema').value = data.fixed_content;
          alert(`Auto-remediation successful! Applied ${data.actions.length} repair action(s). Re-running compatibility check.`);
          runFullCheck();
        } else {
          alert('No automatic repairs were applicable for these violations.');
        }
      } catch (err) {
        alert('Failed to run auto-remediation: ' + err.message);
      }
    }

    // --- Tab 2: Validator Logic ---
    function syncSchemaFromCandidate() {
      const cand = document.getElementById('candidateSchema').value;
      const type = document.getElementById('schemaType').value;
      document.getElementById('valSchema').value = cand;
      document.getElementById('valSchemaType').value = type;
    }

    async function generateMockPayload() {
      const schema_content = document.getElementById('valSchema').value.trim();
      const schema_type = document.getElementById('valSchemaType').value;
      const target_entity = document.getElementById('valTargetEntity').value.trim() || null;

      if (!schema_content) {
        alert('Please provide a schema specification first.');
        return;
      }

      try {
        const resp = await fetch('/v1/mock', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ schema: schema_content, schemaType: schema_type, targetEntity: target_entity })
        });
        const data = await resp.json();
        document.getElementById('valPayload').value = JSON.stringify(data, null, 2);
      } catch (err) {
        alert('Failed to generate mock payload: ' + err.message);
      }
    }

    async function runPayloadValidation() {
      const schema_content = document.getElementById('valSchema').value.trim();
      const schema_type = document.getElementById('valSchemaType').value;
      const target_entity = document.getElementById('valTargetEntity').value.trim() || null;
      const rawPayload = document.getElementById('valPayload').value.trim();

      if (!schema_content || !rawPayload) {
        alert('Please provide both schema and payload.');
        return;
      }

      let parsedPayload;
      try {
        parsedPayload = JSON.parse(rawPayload);
      } catch (e) {
        alert('Payload is not valid JSON: ' + e.message);
        return;
      }

      try {
        const resp = await fetch('/v1/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            schema: schema_content,
            payload: parsedPayload,
            schemaType: schema_type,
            target_entity: target_entity
          })
        });
        const data = await resp.json();

        const resultsArea = document.getElementById('valResultsArea');
        const statusBanner = document.getElementById('valStatusBanner');
        const errorsWrapper = document.getElementById('valErrorsWrapper');

        resultsArea.style.display = 'block';

        if (data.is_valid) {
          statusBanner.className = 'status-banner status-pass';
          statusBanner.innerHTML = '<span>Valid: Payload adheres strictly to the schema specification.</span><span>0 Errors</span>';
          errorsWrapper.innerHTML = '<p style="color: var(--text-muted);">Payload validated against all schema rules and constraints.</p>';
        } else {
          statusBanner.className = 'status-banner status-fail';
          statusBanner.innerHTML = `<span>Invalid: Payload has ${(data.errors || []).length} validation error(s).</span>`;
          errorsWrapper.innerHTML = `
            <ul class="actions-list">
              ${(data.errors || []).map(err => `
                <li class="action-item">
                  <span class="code-val" style="color: #f85149;">${err.path || 'root'}</span>
                  <span>${err.message}</span>
                </li>
              `).join('')}
            </ul>
          `;
        }
      } catch (err) {
        alert('Failed to validate payload: ' + err.message);
      }
    }

    // --- Tab 3: Codegen Logic ---
    function syncSchemaForCodegen() {
      const cand = document.getElementById('candidateSchema').value;
      const type = document.getElementById('schemaType').value;
      document.getElementById('cgSchema').value = cand;
      document.getElementById('cgSchemaType').value = type;
    }

    async function runCodegen() {
      const schema_content = document.getElementById('cgSchema').value.trim();
      const target = document.getElementById('cgTarget').value;
      const schema_type = document.getElementById('cgSchemaType').value;

      if (!schema_content) return;

      try {
        const resp = await fetch('/v1/codegen', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ schema: schema_content, target: target, schemaType: schema_type })
        });
        const data = await resp.json();
        document.getElementById('cgOutput').value = data.code;
        document.getElementById('cgOutputTitle').textContent = `Generated ${target === 'typescript' ? 'TypeScript' : 'Python Pydantic v2'} Code`;
      } catch (err) {
        document.getElementById('cgOutput').value = '// Failed to generate client models: ' + err.message;
      }
    }

    // Initial load
    loadSampleTemplate();
    loadSubjects();
    setTimeout(runFullCheck, 300);
  </script>
</body>
</html>
"""
