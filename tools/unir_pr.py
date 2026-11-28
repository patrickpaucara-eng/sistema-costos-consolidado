"""Une PRs de Codex en desarrollo/mono, como lo hace el coordinador. Uso:
    python tools/unir_pr.py 56 57 58
Pasos: trae origin, une cada rama del PR en orden; si hay conflicto solo en .csv o .md lo resuelve
uniendo ambos lados (sin duplicar líneas); si el conflicto está en código (.py, .html, …) se detiene
y lo deja para revisión humana. Luego corre la compuerta completa; solo si es VERDE publica y cierra
los PRs (API REST: GraphQL está bloqueado en estas sesiones). Nunca toca main.
Requiere: gh autenticado y estar en la rama desarrollo/mono sin cambios pendientes."""
import json, re, subprocess, sys
from pathlib import Path

REPO = "patrickpaucara-eng/sistema-costos-consolidado"
RAMA = "desarrollo/mono"
CO = ("Co-Authored-By: Claude <noreply@anthropic.com>")


def sh(*a, ok=False):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode and not ok:
        sys.exit(f"Falló: {' '.join(a)}\n{r.stdout}\n{r.stderr}")
    return r


def unir_lados(p):
    s = Path(p).read_text(encoding="utf-8")
    patron = r"<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n"
    s = re.sub(patron, lambda m: m.group(1) + "".join(l + "\n" for l in m.group(2).splitlines()
                                                   if l + "\n" not in m.group(1)), s, flags=re.S)
    Path(p).write_text(s, encoding="utf-8")


def main(prs):
    if sh("git", "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != RAMA:
        sys.exit(f"Cámbiate a {RAMA} primero.")
    if sh("git", "status", "--porcelain").stdout.strip():
        sys.exit("Hay cambios sin guardar; guárdalos o descártalos antes de unir.")
    sh("git", "fetch", "-q", "origin")
    sh("git", "merge", "-q", "--ff-only", f"origin/{RAMA}", ok=True)
    for n in prs:
        pr = json.loads(sh("gh", "api", f"repos/{REPO}/pulls/{n}").stdout)
        rama = pr["head"]["ref"]
        if pr["base"]["ref"] != RAMA:
            sys.exit(f"PR #{n} no apunta a {RAMA} (apunta a {pr['base']['ref']}); no se une.")
        r = sh("git", "merge", "-q", "--no-edit", f"origin/{rama}", ok=True)
        if r.returncode:
            conflictos = sh("git", "diff", "--name-only", "--diff-filter=U").stdout.split()
            codigo = [c for c in conflictos if not c.endswith((".csv", ".md"))]
            if codigo:
                sys.exit(f"PR #{n}: conflicto en código {codigo}. Resuélvelo a mano (o pide a Codex que rebase) y vuelve a correr.")
            for c in conflictos:
                unir_lados(c)
            sh("git", "add", *conflictos)
            sh("git", "commit", "-qm", f"Unir {rama} (#{n})\n\n{CO}")
        print(f"#{n} {rama}: unido")
    print("Corriendo la compuerta completa (≈15 min)…")
    g = sh(sys.executable, "tools/verificar.py", ok=True)
    print(g.stdout[-600:])
    if "COMPUERTA: VERDE" not in g.stdout:
        sys.exit("Compuerta ROJA: no se publica. Revisa el error; para deshacer: git reset --hard origin/" + RAMA)
    sh("git", "push", "-q", "origin", RAMA)
    for n in prs:
        sh("gh", "api", "-X", "PATCH", f"repos/{REPO}/pulls/{n}", "-f", "state=closed")
    print("Publicado y PRs cerrados:", ", ".join(f"#{n}" for n in prs))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
