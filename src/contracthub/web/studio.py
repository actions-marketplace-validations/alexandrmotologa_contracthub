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
    }
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .brand {
      font-weight: 700;
      font-size: 1.25rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .badge {
      background: rgba(88, 166, 255, 0.15);
      color: var(--accent);
      border: 1px solid rgba(88, 166, 255, 0.3);
      padding: 0.2rem 0.5rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    main {
      max-width: 1400px;
      margin: 2rem auto;
      padding: 0 1.5rem;
    }
    .controls {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem 1.5rem;
      margin-bottom: 1.5rem;
      display: flex;
      gap: 1.5rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .field-group {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    label { font-size: 0.875rem; color: var(--text-muted); font-weight: 500; }
    select, button {
      background: #21262d;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      font-size: 0.875rem;
      outline: none;
    }
    select:focus { border-color: var(--accent); }
    button.primary {
      background: #238636;
      border-color: rgba(240, 246, 252, 0.1);
      color: #fff;
      font-weight: 600;
      cursor: pointer;
      margin-left: auto;
      transition: background 0.15s ease;
    }
    button.primary:hover { background: #2ea043; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
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
      padding: 0.75rem 1rem;
      font-size: 0.875rem;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    textarea {
      width: 100%;
      height: 380px;
      background: #090d13;
      border: none;
      color: #e6edf3;
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      font-size: 0.875rem;
      padding: 1rem;
      resize: vertical;
      outline: none;
    }
    .results-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-top: 1.5rem;
    }
    .status-banner {
      padding: 1rem 1.25rem;
      border-radius: 6px;
      margin-bottom: 1.25rem;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
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
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
    }
    th, td {
      text-align: left;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
    }
    th {
      background: rgba(255, 255, 255, 0.02);
      color: var(--text-muted);
      font-weight: 600;
    }
    .tag-breaking {
      background: rgba(218, 54, 51, 0.2);
      color: #f85149;
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .code-val {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--accent);
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      ContractHub Studio
      <span class="badge">Universal Schema Linter</span>
    </div>
    <div style="font-size: 0.85rem; color: var(--text-muted);">
      Connected to Local Registry: <code>/v1</code>
    </div>
  </header>

  <main>
    <div class="controls">
      <div class="field-group">
        <label for="schemaType">Format:</label>
        <select id="schemaType">
          <option value="PROTOBUF">Protobuf (Proto3)</option>
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

    // Auto-load sample on first load
    loadSample();
  </script>
</body>
</html>
"""
