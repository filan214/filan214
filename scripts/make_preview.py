"""Write an ignored local preview; --static keeps committed art untouched."""
import argparse
import os

from common import DATA, ROOT, read_json, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    target = ROOT / "preview"
    target.mkdir(exist_ok=True)
    prefix = "../"
    if args.static:
        os.environ["STATIC"] = "1"
        from make_ascii_svg import render as portrait
        from make_info_card import render as info
        from make_status_panel import render as processes
        from make_tagline import render as tagline
        from render_commit_log import render as commit
        from render_heatmap_svg import render as heatmap
        from render_languages_svg import render as languages
        from render_status_bar import render as status
        outputs = {
            "contrib-heatmap.svg": heatmap(read_json(DATA / "contributions.json")),
            "commit-log.svg": commit(read_json(DATA / "last-event.json")),
            "filan-ascii.svg": portrait(
                ROOT / "assets" / "portrait-gray.png"
                if (ROOT / "assets" / "portrait-gray.png").exists()
                else ROOT / "assets" / "filan-ascii.jpg"
            ),
            "info-card.svg": info(), "status-panel.svg": processes(),
            "thesis-progress.svg": status(read_json(DATA / "status.json")),
            "languages.svg": languages(read_json(DATA / "languages.json")),
            "tagline.svg": tagline(),
        }
        target = target / "static"
        target.mkdir(exist_ok=True)
        for name, content in outputs.items():
            (target / name).write_text(content, encoding="utf-8")
        prefix = "./"
    readme = (ROOT / "README.md").read_text(encoding="utf-8").replace('src="./', f'src="{prefix}')
    css = '''body{margin:36px auto;max-width:900px;background:#fff;color:#24292f;font:13px Consolas,monospace;color-scheme:light}h3{font-size:13px;font-weight:400;margin:22px 0 14px}img{display:block;max-width:100%;height:auto}table{border-collapse:collapse;table-layout:fixed;max-width:100%}td{padding:0}br{line-height:12px}@media(prefers-color-scheme:dark){body{background:#0d1117;color:#919ba7;color-scheme:dark}}'''
    page = f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>filan214 profile preview</title><style>{css}</style><body>{readme}</body></html>'
    (target / "index.html").write_text(page, encoding="utf-8")
    print(f"Preview: {target / 'index.html'}")


if __name__ == "__main__":
    run(main)
