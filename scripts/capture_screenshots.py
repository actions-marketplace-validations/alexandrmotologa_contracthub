import os
import subprocess
import threading
import time
from pathlib import Path

import uvicorn

BASE_DIR = Path(__file__).parent.parent.resolve()
IMAGES_DIR = BASE_DIR / "docs" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 1. Setup sample database
DEMO_DB = BASE_DIR / "scripts" / "demo.db"
DEMO_DB.unlink(missing_ok=True)

os.environ["CONTRACTHUB_DB"] = f"sqlite:///{DEMO_DB.resolve()}"

from contracthub.config import settings

settings.db_url = f"sqlite:///{DEMO_DB.resolve()}"

from contracthub.api.server import create_app
from contracthub.storage.database import (
    SchemaVersionModel,
    SubjectModel,
    get_session_factory,
    init_db,
)

init_db()

# Populate sample registry data
factory = get_session_factory()
with factory() as session:
    # 1. order-events (Protobuf)
    s1 = SubjectModel(name="order-events", compatibility_mode="BACKWARD")
    session.add(s1)
    session.flush()

    v1_proto = (BASE_DIR / "examples" / "order_v1.proto").read_text(encoding="utf-8")
    v2_proto = (BASE_DIR / "examples" / "order_v2_compatible.proto").read_text(encoding="utf-8")
    
    session.add(SchemaVersionModel(subject_id=s1.id, version=1, schema_content=v1_proto, schema_type="PROTOBUF", fingerprint="fp1_proto"))
    session.add(SchemaVersionModel(subject_id=s1.id, version=2, schema_content=v2_proto, schema_type="PROTOBUF", fingerprint="fp2_proto"))

    # 2. inventory-avro (Avro)
    s2 = SubjectModel(name="inventory-avro", compatibility_mode="FULL")
    session.add(s2)
    session.flush()

    v1_avro = (BASE_DIR / "examples" / "order_v1.avsc").read_text(encoding="utf-8")
    session.add(SchemaVersionModel(subject_id=s2.id, version=1, schema_content=v1_avro, schema_type="AVRO", fingerprint="fp1_avro"))

    # 3. payment-service-api (OpenAPI)
    s3 = SubjectModel(name="payment-service-api", compatibility_mode="BACKWARD")
    session.add(s3)
    session.flush()

    openapi_sample = """openapi: 3.0.0
info:
  title: Payment API
  version: 1.0.0
paths:
  /v1/charges:
    post:
      summary: Create charge
      responses:
        '200':
          description: OK
"""
    session.add(SchemaVersionModel(subject_id=s3.id, version=1, schema_content=openapi_sample, schema_type="OPENAPI", fingerprint="fp1_openapi"))

    # 4. customer-profile (JSON Schema)
    s4 = SubjectModel(name="customer-profile", compatibility_mode="FULL")
    session.add(s4)
    session.flush()

    jsonschema_sample = """{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "user_id": { "type": "string" },
    "email": { "type": "string", "format": "email" }
  },
  "required": ["user_id"]
}"""
    session.add(SchemaVersionModel(subject_id=s4.id, version=1, schema_content=jsonschema_sample, schema_type="JSONSCHEMA", fingerprint="fp1_jsonschema"))
    session.commit()

print("Populated demo database with sample subjects.")

# Start server in thread
app = create_app()
server_port = 8877
config = uvicorn.Config(app=app, host="127.0.0.1", port=server_port, log_level="warning")
server = uvicorn.Server(config)

server_thread = threading.Thread(target=server.run, daemon=True)
server_thread.start()
time.sleep(1.5)

print(f"ContractHub server running on port {server_port}")

# Screenshot 1: Web Studio Overview
studio_png = IMAGES_DIR / "studio_overview.png"
print(f"Capturing Web Studio screenshot to {studio_png}...")

cmd = [
    EDGE_PATH,
    "--headless=new",
    "--window-size=1440,960",
    "--virtual-time-budget=3500",
    f"--screenshot={studio_png.resolve()}",
    f"http://127.0.0.1:{server_port}/studio",
]
res = subprocess.run(cmd, capture_output=True, text=True, check=False)
print("Edge studio capture return code:", res.returncode)

# Stop server
server.should_exit = True
time.sleep(0.5)

# Screenshot 2: CLI Diff Terminal
from rich.console import Console

from contracthub.core.comparator import SchemaComparator
from contracthub.core.models import CompatibilityMode, SchemaType
from contracthub.tui.diff_viewer import render_diff_table

rec_console = Console(record=True, width=110)
import contracthub.tui.diff_viewer as dv

dv.console = rec_console

base_content = (BASE_DIR / "examples" / "order_v1.proto").read_text(encoding="utf-8")
candidate_content = (BASE_DIR / "examples" / "order_v2_breaking.proto").read_text(encoding="utf-8")

rec_console.print("[bold green]$[/bold green] [bold white]contracthub diff examples/order_v1.proto examples/order_v2_breaking.proto --mode FULL[/bold white]")
diff_res = SchemaComparator.compare_strings(base_content, candidate_content, schema_type=SchemaType.PROTOBUF, mode=CompatibilityMode.FULL)
render_diff_table(diff_res, "order_v1.proto", "order_v2_breaking.proto")

html_body = rec_console.export_html(inline_styles=True)

terminal_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: #090d13;
      padding: 30px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }}
    .window {{
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 10px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.6);
      width: 1000px;
      overflow: hidden;
    }}
    .titlebar {{
      background: #161b22;
      border-bottom: 1px solid #30363d;
      padding: 10px 16px;
      display: flex;
      align-items: center;
    }}
    .dots {{
      display: flex;
      gap: 7px;
    }}
    .dot {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }}
    .dot-red {{ background: #ff5f56; }}
    .dot-yellow {{ background: #ffbd2e; }}
    .dot-green {{ background: #27c93f; }}
    .title {{
      margin-left: auto;
      margin-right: auto;
      color: #8b949e;
      font-size: 13px;
      font-weight: 500;
    }}
    .terminal-content {{
      padding: 24px 24px 28px 24px;
      overflow: hidden;
    }}
    pre {{
      font-family: "JetBrains Mono", "Fira Code", Consolas, Menlo, monospace !important;
      font-size: 13px !important;
      line-height: 1.45 !important;
    }}
  </style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="dots">
        <div class="dot dot-red"></div>
        <div class="dot dot-yellow"></div>
        <div class="dot dot-green"></div>
      </div>
      <div class="title">Terminal &mdash; contracthub diff (Proto3 Breaking Change)</div>
    </div>
    <div class="terminal-content">
      {html_body}
    </div>
  </div>
</body>
</html>"""

temp_term = BASE_DIR / "scripts" / "temp_cli.html"
temp_term.write_text(terminal_html, encoding="utf-8")

cli_png = IMAGES_DIR / "cli_diff.png"
print(f"Capturing CLI diff screenshot to {cli_png}...")
cmd_cli = [
    EDGE_PATH,
    "--headless=new",
    "--window-size=1120,860",
    f"--screenshot={cli_png.resolve()}",
    temp_term.resolve().as_uri(),
]
subprocess.run(cmd_cli, check=True)
temp_term.unlink(missing_ok=True)
print("CLI diff screenshot saved successfully!")

# Screenshot 3: CLI Scan (Monorepo Scanner)
from contracthub.core.models import Severity, Violation
from contracthub.core.scanner import FileScanResult, ScanSummary
from contracthub.tui.diff_viewer import render_scan_table

rec_console_scan = Console(record=True, width=110)
dv.console = rec_console_scan

rec_console_scan.print("[bold green]$[/bold green] [bold white]contracthub scan --base-ref origin/main --mode BACKWARD[/bold white]")

fake_results = [
    FileScanResult(
        path="proto/order.proto",
        is_compatible=False,
        violations=[
            Violation(code="PROTO_FIELD_REMOVED", severity=Severity.BREAKING, path="OrderEvent.customer_id", message="Field 'customer_id' (tag 2) was deleted without marking as reserved.")
        ],
        total_checks=12,
    ),
    FileScanResult(
        path="avro/inventory.avsc",
        is_compatible=True,
        total_checks=8,
    ),
    FileScanResult(
        path="openapi/payments.yaml",
        is_compatible=True,
        total_checks=15,
    ),
    FileScanResult(
        path="schemas/user_profile.json",
        is_new_file=True,
        is_compatible=True,
        total_checks=5,
    ),
]
summary = ScanSummary(
    target_ref="origin/main",
    mode=CompatibilityMode.BACKWARD,
    total_scanned=4,
    passed_count=3,
    failed_count=1,
    results=fake_results,
)
render_scan_table(summary)

html_scan_body = rec_console_scan.export_html(inline_styles=True)
scan_html = terminal_html.replace(html_body, html_scan_body).replace(
    "contracthub diff (Proto3 Breaking Change)",
    "contracthub scan (Git Monorepo Scanner)"
)

temp_scan = BASE_DIR / "scripts" / "temp_scan.html"
temp_scan.write_text(scan_html, encoding="utf-8")

scan_png = IMAGES_DIR / "cli_scan.png"
print(f"Capturing CLI scan screenshot to {scan_png}...")
cmd_scan = [
    EDGE_PATH,
    "--headless=new",
    "--window-size=1120,540",
    f"--screenshot={scan_png.resolve()}",
    temp_scan.resolve().as_uri(),
]
subprocess.run(cmd_scan, check=True)
temp_scan.unlink(missing_ok=True)
print("CLI scan screenshot saved successfully!")
