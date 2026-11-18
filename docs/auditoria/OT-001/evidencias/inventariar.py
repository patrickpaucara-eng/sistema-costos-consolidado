import csv
import json
import pathlib
import re
import subprocess
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

WORK = pathlib.Path('/workspace/work/ot001')
REPO = WORK / 'repo.git'


def git(*args):
    return subprocess.check_output(['git', '--git-dir', str(REPO), *args]).decode('utf-8', errors='replace')


@lru_cache(maxsize=None)
def files(commit):
    result = {}
    for entry in git('ls-tree', '-rz', commit).split('\0'):
        if entry:
            metadata, path = entry.split('\t', 1)
            result[path] = metadata
    return result


def change_kind(paths):
    counts = Counter()
    for path in paths:
        if path.endswith(('.zip', '.xlsx', '.xlsm', '.xlsb', '.pdf', '.pyc')):
            counts['artefactos'] += 1
        elif path.endswith(('.md', '.txt', '.mmd', '.rst')):
            counts['documentacion'] += 1
        elif path.startswith(('casos/', 'pruebas/', 'kit/pruebas/')) or '/test_' in path or '/prueba_' in path:
            counts['pruebas_casos'] += 1
        elif path.startswith(('kit/', 'fuente/', '.dsh/', '.github/')):
            counts['fuente_herramientas'] += 1
        else:
            counts['otros'] += 1
    return dict(sorted(counts.items()))


refs = [row.split('\t', 4) for row in git('for-each-ref', '--format=%(refname)%09%(objectname)%09%(*objectname)%(tree)%09%(committerdate:iso-strict)%09%(subject)', 'refs/heads').splitlines()]
tips = defaultdict(list)
trees = defaultdict(list)
for ref, sha, tree, date, subject in refs:
    tips[sha].append(ref)
    trees[tree].append(ref)
main = next(r[1] for r in refs if r[0] == 'refs/heads/main')
main_files = files(main)


def describe(row):
    ref, sha, tree, date, subject = row
    bases = git('merge-base', '--all', main, sha).splitlines()
    if len(bases) != 1:
        raise RuntimeError(f'{ref}: {bases}')
    base = bases[0]
    diverg = git('rev-list', '--left-right', f'{main}...{sha}').splitlines()
    ahead_shas = [commit[1:] for commit in diverg if commit.startswith('>')]
    behind = sum(commit.startswith('<') for commit in diverg)
    base_files = files(base)
    head_files = files(sha)
    changed = {p for p in base_files.keys() | head_files.keys() if base_files.get(p) != head_files.get(p)}
    same = {p for p in changed if main_files.get(p) == head_files.get(p)}
    distinct = changed - same
    added_missing = {p for p in distinct if p not in base_files and p not in main_files}
    removed_main_retains = {p for p in distinct if p not in head_files}
    removed_in_main = {p for p in distinct if p in base_files and p not in main_files}
    modified_different = distinct - added_missing - removed_main_retains - removed_in_main
    ext = git('cherry', main, sha).splitlines() if ahead_shas else []
    cherry = Counter(line[0] for line in ext)
    return {
        'ref': ref, 'sha': sha, 'arbol': tree, 'fecha_commit': date, 'asunto_punta': subject,
        'base': base, 'ahead': len(ahead_shas), 'behind': behind,
        'commits_fuera_main': ahead_shas,
        'parches_exactos_en_main': cherry['-'], 'parches_sin_misma_firma': cherry['+'],
        'cambios_rama': sorted(changed), 'cambios_identicos_en_main': sorted(same),
        'diferentes_en_main': sorted(distinct), 'archivos_nuevos_ausentes_en_main': sorted(added_missing),
        'archivos_que_rama_elimina_y_main_conserva': sorted(removed_main_retains),
        'archivos_que_rama_edita_y_main_elimina': sorted(removed_in_main),
        'archivos_en_main_con_contenido_distinto': sorted(modified_different),
        'rutas_tip_distintas_de_main': sum(head_files.get(p) != main_files.get(p) for p in head_files.keys() | main_files.keys()),
        'composicion_diferencias': change_kind(distinct),
    }


with ThreadPoolExecutor(max_workers=12) as pool:
    entries = list(pool.map(describe, refs))

commit_tips = defaultdict(set)
for entry in entries:
    for commit in entry['commits_fuera_main']:
        commit_tips[commit].add(entry['sha'])


def classify(e):
    if e['ref'] == 'refs/heads/main':
        return 'base_integrada'
    if e['arbol'] == entries_by_ref['refs/heads/main']['arbol']:
        return 'arbol_identico_a_main'
    if not e['ahead']:
        return 'hito_congelado_integrado' if e['ref'].startswith(('refs/heads/version/', 'refs/heads/prototipo/')) else 'antecesora_de_main'
    if e['ref'].startswith('refs/heads/estudio/'):
        return 'estudio_aislado'
    if not e['diferentes_en_main']:
        return 'delta_de_rama_ya_presente_en_main'
    if re.search(r'bloqueo|devuelta|descart', e['ref'], flags=re.I) or e['asunto_punta'].startswith('BLOQUEO'):
        return 'bloqueo_o_iteracion_a_revisar'
    if e['ref'] in {'refs/heads/arq/documentos-finales', 'refs/heads/desarrollo/ola1', 'refs/heads/desarrollo/deuda', 'refs/heads/desarrollo/I-9'}:
        return 'candidata_para_recuperacion_selectiva'
    if e['ref'] in {
        'refs/heads/obrera/deuda-cuadre', 'refs/heads/obrera/vol-seis-meses',
        'refs/heads/obrera/proteccion-diseno', 'refs/heads/obrera/ola1-umbral',
        'refs/heads/verif/ola1',
    }:
        return 'aportacion_incluida_en_candidata'
    if e['ref'].startswith(('refs/heads/desarrollo/', 'refs/heads/obrera/', 'refs/heads/verif/', 'refs/heads/prueba/')):
        return 'desarrollo_o_verificacion_a_contrastar'
    if set(e['composicion_diferencias']) <= {'documentacion', 'artefactos'}:
        return 'documentacion_o_artefactos_a_contrastar'
    return 'divergencia_historica_a_contrastar'


entries_by_ref = {e['ref']: e for e in entries}
for e in entries:
    e['commits_exclusivos_punta'] = [c for c in e['commits_fuera_main'] if commit_tips[c] == {e['sha']}]
    e['grupo_sha'] = tips[e['sha']]
    e['grupo_arbol'] = trees[e['arbol']]
    e['clasificacion'] = classify(e)

fields = [
    'ref', 'sha', 'arbol', 'fecha_commit', 'asunto_punta', 'ancestro_comun_main',
    'ahead_main', 'behind_main', 'commits_exclusivos_punta', 'parches_exactos_en_main',
    'parches_sin_misma_firma', 'commits_fuera_main_sin_parche_comparable',
    'rutas_cambiadas_desde_ancestro', 'rutas_ya_identicas_en_main',
    'rutas_delta_distintas_en_main', 'rutas_nuevas_rama_ausentes_main',
    'rutas_rama_elimina_main_conserva', 'rutas_rama_edita_main_elimina',
    'rutas_delta_contenido_distinto_main', 'rutas_punta_distintas_main',
    'n_refs_mismo_sha', 'refs_mismo_sha', 'n_refs_mismo_arbol', 'refs_mismo_arbol',
    'composicion_diferencias', 'clasificacion', 'sha_commits_exclusivos_punta',
    'rutas_delta_distintas', 'rutas_delta_nuevas_ausentes_main',
]
with (WORK / 'INVENTARIO_RAMAS.csv').open('w', encoding='utf-8-sig', newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(fields)
    for e in entries:
        writer.writerow([
            e['ref'], e['sha'], e['arbol'], e['fecha_commit'], e['asunto_punta'], e['base'],
            e['ahead'], e['behind'], len(e['commits_exclusivos_punta']), e['parches_exactos_en_main'],
            e['parches_sin_misma_firma'], e['ahead'] - e['parches_exactos_en_main'] - e['parches_sin_misma_firma'],
            len(e['cambios_rama']), len(e['cambios_identicos_en_main']), len(e['diferentes_en_main']),
            len(e['archivos_nuevos_ausentes_en_main']), len(e['archivos_que_rama_elimina_y_main_conserva']),
            len(e['archivos_que_rama_edita_y_main_elimina']), len(e['archivos_en_main_con_contenido_distinto']),
            e['rutas_tip_distintas_de_main'], len(e['grupo_sha']), ' | '.join(e['grupo_sha']),
            len(e['grupo_arbol']), ' | '.join(e['grupo_arbol']),
            ' | '.join(f'{k}={v}' for k, v in e['composicion_diferencias'].items()), e['clasificacion'],
            ' | '.join(e['commits_exclusivos_punta']), ' | '.join(e['diferentes_en_main']),
            ' | '.join(e['archivos_nuevos_ausentes_en_main']),
        ])

(WORK / 'analisis_refs.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2))
print(f'{len(refs)} refs, {len(tips)} puntas, {len(trees)} árboles, {len(commit_tips)} commits fuera de main')
print(Counter(e['clasificacion'] for e in entries))
print('Alias SHA:')
for sha, group in sorted(tips.items()):
    if len(group) > 1:
        print(sha[:8], group)
print('Árbol compartido entre puntas diferentes:')
for e in entries:
    if e['ref'] == e['grupo_arbol'][0] and set(e['grupo_arbol']) != set(e['grupo_sha']):
        print(e['arbol'][:8], e['grupo_arbol'])
