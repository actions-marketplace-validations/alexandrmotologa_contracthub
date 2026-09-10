import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

BASE_DIR = Path(__file__).parent.parent.resolve()
IMAGES_DIR = BASE_DIR / "docs" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def create_terminal_window(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
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
      <div class="title">{title}</div>
    </div>
    <div class="terminal-content">
      {body_html}
    </div>
  </div>
</body>
</html>"""

def render_semver_screenshot():
    console = Console(record=True, width=110)
    console.print("[bold green]$[/bold green] [bold white]contracthub semver examples/order_v1.proto examples/order_v2_breaking.proto --current 1.0.0[/bold white]\n")

    t = Table(title="SEMVER RECOMMENDATION: MAJOR BUMP", border_style="red", title_style="bold red", show_header=False)
    t.add_column("Prop", style="cyan", width=22)
    t.add_column("Val", style="white")
    t.add_row("Current Version:", "1.0.0")
    t.add_row("Recommended Version:", "[bold red]2.0.0 (MAJOR)[/bold red]")
    t.add_row("Base Schema:", "examples/order_v1.proto")
    t.add_row("Candidate Schema:", "examples/order_v2_breaking.proto")
    t.add_row("Impact Analysis:", "[bold yellow]4 breaking changes detected (e.g. PROTO_TYPE_CHANGED, PROTO_TAG_MUTATED)[/bold yellow]")
    console.print(t)

    html = create_terminal_window("Terminal — contracthub semver (Automated Version Bump)", console.export_html(inline_styles=True))
    tmp = BASE_DIR / "scripts" / "temp_semver.html"
    tmp.write_text(html, encoding="utf-8")
    out_png = IMAGES_DIR / "cli_semver.png"
    subprocess.run([EDGE_PATH, "--headless=new", "--window-size=1120,520", f"--screenshot={out_png.resolve()}", tmp.resolve().as_uri()], check=True)
    tmp.unlink()
    print("✓ Created cli_semver.png")

if __name__ == "__main__":
    render_semver_screenshot()
