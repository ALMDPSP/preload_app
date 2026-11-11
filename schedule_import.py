"""Import new schedule rows from the same spreadsheet formats as the branch registry."""
import json
from datetime import date, datetime

from flask import Response, g, jsonify, request

from branch_import import MAX_FILE, file_rows, normalized, text_value
from dashboard import DEFAULT_PDVS, pdv_number
from operations import text, valid_date

COLUMNS = {
    'code': {'filial', 'loja', 'codigo', 'codigofilial', 'codigodafilial'},
    'pdv': {'pdv', 'numeropdv', 'numerodopdv'},
    'owner': {'responsavel', 'responsavelpelopdv', 'executor'},
    'start_date': {'inicio', 'inicioprevisto', 'datainicio', 'datadeinicio'},
    'due_date': {'prazo', 'dataprevista', 'dataprazo', 'prazodeconclusao'},
    'notes': {'observacoes', 'observacao', 'notas'},
}

def spreadsheet_date(value, required=False):
    if isinstance(value, date):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    value = text_value(value)
    if '/' in value:
        try:
            return datetime.strptime(value, '%d/%m/%Y').date().isoformat()
        except ValueError as exc:
            raise ValueError('Use datas no formato DD/MM/AAAA ou AAAA-MM-DD.') from exc
    return valid_date(value, required)

def parse_schedule(rows):
    header = next((i for i, row in enumerate(rows) if any(text_value(cell) for cell in row)), None)
    if header is None:
        raise ValueError('O arquivo está vazio.')
    mapping = {}
    for index, cell in enumerate(rows[header]):
        for field, aliases in COLUMNS.items():
            if normalized(cell) in aliases:
                if field in mapping:
                    raise ValueError('Coluna repetida: ' + text_value(cell))
                mapping[field] = index
    if not {'code', 'pdv', 'owner', 'due_date'} <= mapping.keys():
        raise ValueError('Inclua as colunas Filial, PDV, Responsável e Prazo.')
    prepared, errors, seen = [], [], set()
    total = 0
    for line, row in enumerate(rows[header+1:], header+2):
        if not any(text_value(cell) for cell in row):
            continue
        total += 1
        cells = {key: row[i] if i < len(row) else None for key, i in mapping.items()}
        values = {key: text_value(value) for key, value in cells.items()}
        try:
            code = text(values, 'code', 30, True).upper()
            pdv = pdv_number(values.get('pdv'))
            if not pdv:
                raise ValueError('Informe um número de PDV válido.')
            owner = text(values, 'owner', 120, True)
            start = spreadsheet_date(cells.get('start_date'))
            due = spreadsheet_date(cells.get('due_date'), True)
            notes = text(values, 'notes', 2000)
            if start and start > due:
                raise ValueError('O início deve ser anterior ou igual ao prazo.')
            if (code, pdv) in seen:
                raise ValueError('Filial e PDV repetidos no arquivo.')
            seen.add((code, pdv))
            prepared.append(dict(line=line, code=code, pdv=pdv, owner=owner,
                                 start_date=start, due_date=due, notes=notes))
        except ValueError as exc:
            errors.append(dict(line=line, message=str(exc)))
    if not total:
        raise ValueError('Inclua pelo menos um PDV na planilha.')
    return prepared, errors, total

def check_schedule(c, prepared, errors, lock=False):
    if lock:
        codes = sorted({row['code'] for row in prepared})
        for offset in range(0, len(codes), 400):
            batch = codes[offset:offset+400]
            marks = ','.join(['%s']*len(batch))
            c.execute('SELECT id FROM ct_branches WHERE code IN ('+marks+') ORDER BY code FOR UPDATE', batch).fetchall()
    branches = {
        row['code'].upper(): (row['id'], set(json.loads(row['pdvs']) if row['pdvs'] else DEFAULT_PDVS))
        for row in c.execute('SELECT b.id,b.code,p.pdvs FROM ct_branches b LEFT JOIN ct_branch_pdv_plan p ON p.branch_id=b.id')
    }
    existing = {(row['branch_id'], row['pdv']) for row in c.execute('SELECT branch_id,pdv FROM ct_rollout_schedule')}
    for row in prepared:
        branch = branches.get(row['code'])
        if not branch or row['pdv'] not in branch[1]:
            message = 'Filial não cadastrada.' if not branch else 'PDV fora do plano da filial.'
            errors.append(dict(line=row['line'], message=message))
            row['action'] = 'invalid'
            continue
        row['branch_id'] = branch[0]
        row['action'] = 'existing' if (branch[0], row['pdv']) in existing else 'new'

def register_schedule_import(app, core):
    @app.get('/api/operations/schedule/import-template')
    def schedule_template():
        if g.user['role'] not in {'admin', 'manager'}:
            return core['error']('Somente Administrador ou Gestor pode importar o cronograma.', 403)
        return Response(
            '\ufeffFilial;PDV;Responsável;Início;Prazo;Observações\r\nVD266;01;Equipe de TI;11/11/2026;12/11/2026;Janela confirmada\r\n',
            content_type='text/csv; charset=utf-8',
            headers={'Content-Disposition': 'attachment; filename="Modelo_Cronograma.csv"'},
        )

    @app.post('/api/operations/schedule/import/<action>')
    def schedule_import(action):
        if g.user['role'] not in {'admin', 'manager'}:
            return core['error']('Somente Administrador ou Gestor pode importar o cronograma.', 403)
        if action not in {'preview', 'confirm'}:
            return core['error']('Ação inválida.', 404)
        upload = request.files.get('file')
        if not upload or not upload.filename:
            return core['error']('Selecione uma planilha Excel ou CSV.')
        raw = upload.read(MAX_FILE+1)
        if len(raw) > MAX_FILE:
            return core['error']('Limite de 10 MB por arquivo.', 413)
        try:
            rows, sheet = file_rows(raw, upload.filename)
            prepared, errors, total = parse_schedule(rows)
        except ValueError as exc:
            return core['error'](str(exc))
        confirm = action == 'confirm'
        if confirm:
            g.atomic_write = True
        with core['db']() as c:
            check_schedule(c, prepared, errors, lock=confirm and bool(core['DATABASE']))
            new = [row for row in prepared if row['action'] == 'new']
            existing = sum(row['action'] == 'existing' for row in prepared)
            if not confirm:
                return jsonify(total=total, sheet=sheet, new=len(new), existing=existing,
                               error_count=len(errors), errors=sorted(errors, key=lambda e:e['line'])[:50],
                               rows=prepared[:50])
            if errors:
                return core['error']('A planilha contém erros. Analise novamente antes de importar.')
            created = 0
            timestamp = core['now']()
            for offset in range(0, len(new), 100):
                batch = new[offset:offset+100]
                params = []
                for row in batch:
                    params.extend((row['branch_id'], row['pdv'], row['owner'], row['start_date'],
                                   row['due_date'], row['notes'], timestamp, g.user['email']))
                placeholders = ','.join(['(%s,%s,%s,%s,%s,%s,1,%s,%s)']*len(batch))
                inserted = c.execute(
                    'INSERT INTO ct_rollout_schedule (branch_id,pdv,owner,start_date,due_date,notes,version,updated_at,updated_by) VALUES '
                    + placeholders + ' ON CONFLICT(branch_id,pdv) DO NOTHING RETURNING branch_id', params,
                ).fetchall()
                created += len(inserted)
            if created:
                core['audit'](c, g.user['email'], 'importação de cronograma',
                              detail={'created': created, 'skipped': total-created})
        return jsonify(created=created, skipped=total-created)
