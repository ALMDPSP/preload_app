"""Bounded XLSX/CSV branch imports with review, atomic commit and stable IDs."""
import csv, hashlib, io, json, re, secrets, sqlite3, time, unicodedata, zipfile
from pathlib import Path
from flask import request, g, jsonify, Response

MAX_ROWS=10000
MAX_FILE=10*1024*1024
FIELDS=['id','code','name','city','uf','active','needs_review']
UFS={'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'}

def normalized(value):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().lower())

ALIASES={
 'code':{'codigo','cod','codfilial','codigofilial','codigodafilial','filial','loja','codloja','codigoloja'},
 'name':{'nome','nomefilial','nomedafilial','nomeloja','nomedaloja','descricao','descricaofilial','descricaodafilial','razaosocial'},
 'city':{'cidade','municipio'},'uf':{'uf','estado'},'active':{'ativo','ativa','status','situacao'}
}

def text_value(value):
    if value is None:return ''
    if isinstance(value,float) and value.is_integer():return str(int(value))
    return str(value).strip()

def file_rows(raw,filename):
    extension=Path(filename).suffix.lower()
    if extension=='.csv':
        try:text=raw.decode('utf-8-sig')
        except UnicodeDecodeError:text=raw.decode('cp1252')
        try:delimiter=csv.Sniffer().sniff(text[:8192],delimiters=';,\t').delimiter
        except csv.Error:delimiter=';'
        return list_limited(csv.reader(io.StringIO(text),delimiter=delimiter)), 'CSV'
    if extension!='.xlsx':raise ValueError('Envie uma planilha .xlsx ou .csv. Arquivos .xls precisam ser salvos como .xlsx.')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos=archive.infolist()
            if len(infos)>500 or sum(i.file_size for i in infos)>80*1024*1024:raise ValueError('Planilha muito grande após descompactar. Use uma planilha simples com até 10 mil filiais.')
        from openpyxl import load_workbook
        book=load_workbook(io.BytesIO(raw),read_only=True,data_only=False,keep_links=False)
        try:
            sheet=book.worksheets[0]
            if sheet.max_column>30 or sheet.max_row>MAX_ROWS+1:raise ValueError('Limite de 10 mil linhas e 30 colunas. Remova linhas/colunas extras ou utilize CSV.')
            rows=[]
            for cells in sheet.iter_rows():
                values=[]
                for cell in cells:
                    if cell.data_type=='f':raise ValueError(f'Fórmula encontrada na célula {cell.coordinate}. Cole os dados como valores antes de importar.')
                    value=cell.value
                    if isinstance(value,(int,float)) and not isinstance(value,bool) and re.fullmatch(r'0{2,30}',cell.number_format or ''):
                        value=str(int(value)).zfill(len(cell.number_format))
                    values.append(value)
                rows.append(values)
            return rows,sheet.title
        finally:book.close()
    except ValueError:raise
    except Exception as exc:raise ValueError('Não foi possível ler o Excel. Confira se é um arquivo .xlsx válido e sem senha.') from exc

def list_limited(reader):
    rows=[]
    try:
        for row in reader:
            if len(rows)>MAX_ROWS:raise ValueError('O arquivo deve ter até 10 mil filiais.')
            if len(row)>30:raise ValueError('O arquivo deve ter até 30 colunas.')
            rows.append(row)
    except csv.Error as exc:raise ValueError('CSV inválido ou com células muito extensas.') from exc
    return rows

def parse_rows(rows):
    header=next((i for i,r in enumerate(rows) if any(text_value(v) for v in r)),None)
    if header is None:raise ValueError('O arquivo está vazio.')
    mapping={}
    for i,value in enumerate(rows[header]):
        for field,aliases in ALIASES.items():
            if normalized(value) in aliases:
                if field in mapping:raise ValueError(f'Existem duas colunas para {field}. Use somente uma coluna por campo do modelo.')
                mapping[field]=i
    if not {'code','name'}<=mapping.keys():raise ValueError('O cabeçalho deve conter Código/Filial e Nome/Descrição. Baixe o modelo para conferir as colunas.')
    parsed=[];errors=[];seen={}
    for number,row in enumerate(rows[header+1:],header+2):
        if not any(text_value(v) for v in row):continue
        def val(field):return text_value(row[mapping[field]]) if field in mapping and mapping[field]<len(row) else ''
        code=val('code').upper();name=val('name');city=val('city');uf=val('uf').upper();active_raw=val('active')
        failures=[]
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{1,29}',code):failures.append('Código inválido (2 a 30 caracteres, letras, números, _ ou -).')
        if not name or len(name)>160:failures.append('Nome obrigatório, com até 160 caracteres.')
        if len(city)>100:failures.append('Cidade com mais de 100 caracteres.')
        if uf and uf not in UFS:failures.append('UF inválida. Informe a sigla, como SP.')
        if code in seen:failures.append(f'Código repetido no arquivo; já informado na linha {seen[code]}.')
        else:seen[code]=number
        active=None
        if active_raw:
            active_key=unicodedata.normalize('NFKD',active_raw).encode('ascii','ignore').decode().lower().strip()
            if active_key in {'1','true','sim','s','ativo','ativa'}:active=1
            elif active_key in {'0','false','nao','n','inativo','inativa'}:active=0
            else:failures.append('Situação inválida. Use Ativa/Inativa ou Sim/Não.')
        if failures:errors.append({'line':number,'code':code,'message':' '.join(failures)})
        else:parsed.append({'line':number,'code':code,'name':name,'city':city,'uf':uf,'active':active})
    if not parsed and not errors:raise ValueError('O arquivo contém somente o cabeçalho. Inclua as filiais abaixo dele.')
    return parsed,errors

def fingerprint(row):return {key:row[key] for key in FIELDS}

def plan_import(rows,existing,mode):
    plan=[];errors=[];counts={'new':0,'update':0,'unchanged':0,'ignored':0}
    for record in rows:
        previous=existing.get(record['code'])
        if previous and previous['needs_review']:
            errors.append({'line':record['line'],'code':record['code'],'message':'Este é um vínculo antigo pendente de revisão. Confirme a filial antes de atualizar.'});continue
        current={'code':record['code'],'name':record['name'],'city':record['city'] or (previous['city'] if previous else ''),'uf':record['uf'] or (previous['uf'] if previous else ''),'active':record['active'] if record['active'] is not None else (previous['active'] if previous else 1)}
        if previous and mode=='create_only':action='ignored'
        elif previous:action='unchanged' if all(previous[k]==current[k] for k in ['name','city','uf','active']) else 'update'
        else:action='new'
        counts[action]+=1
        plan.append({**current,'line':record['line'],'action':action,'before':fingerprint(previous) if previous else None})
    return plan,counts,errors

def register_branch_import(app,core):
    db,error,audit,now=(core[k] for k in ['db','error','audit','now'])
    def allowed():return g.user['role'] in ['admin','manager']

    @app.get('/api/branches/import-template')
    def import_template():
        data='\ufeffcodigo;nome;cidade;uf;ativo\r\nVD266;Shopping Vila Lobos;São Paulo;SP;Ativa\r\nL2621;Nome da loja;Campinas;SP;Ativa\r\n'
        return Response(data,content_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="Modelo_Importacao_Filiais.csv"'})

    @app.post('/api/branches/import/preview')
    def preview_import():
        if not allowed():return error('Somente Administrador ou Gestor pode importar filiais.',403)
        mode=request.form.get('mode','create_only')
        if mode not in ['create_only','upsert']:return error('Modo de importação inválido.')
        upload=request.files.get('file')
        if not upload or not upload.filename:return error('Selecione um arquivo Excel ou CSV.')
        raw=upload.read(MAX_FILE+1)
        if len(raw)>MAX_FILE:return error('Limite de 10 MB por arquivo.',413)
        try:rows,sheet=file_rows(raw,upload.filename);records,errors=parse_rows(rows)
        except (ValueError,UnicodeError) as exc:return error(str(exc))
        total=len(records)+len(errors)
        with db() as c:
            existing={r['code']:dict(r) for r in c.execute('SELECT * FROM ct_branches').fetchall()}
            plan,counts,extra=plan_import(records,existing,mode);errors.extend(extra)
            uid=None
            if not errors and (counts['new']+counts['update']):
                uid=secrets.token_hex(24)
                c.execute('DELETE FROM ct_branch_imports WHERE expires_at<%s AND applied_at IS NULL',(time.time()-86400,))
                c.execute('INSERT INTO ct_branch_imports (id,user_id,payload,mode,expires_at,created_at) VALUES (%s,%s,%s,%s,%s,%s)',(uid,g.user['id'],json.dumps(plan,ensure_ascii=False),mode,time.time()+1200,now()))
        display=[{k:v for k,v in row.items() if k!='before'} for row in plan[:100]]
        return jsonify(import_id=uid,counts=counts,total=total,error_count=len(errors),errors=errors[:200],rows=display,preview_limit=100,sheet=sheet,mode=mode,expires_in=1200)

    @app.post('/api/branches/import/confirm')
    def confirm_import():
        if not allowed():return error('Somente Administrador ou Gestor pode importar filiais.',403)
        uid=(request.get_json() or {}).get('import_id')
        if not isinstance(uid,str):return error('Analise o arquivo antes de confirmar.')
        try:
            with db() as c:
                lock=' FOR UPDATE' if core['DATABASE'] else ''
                staged=c.execute('SELECT * FROM ct_branch_imports WHERE id=%s AND user_id=%s'+lock,(uid,g.user['id'])).fetchone()
                if not staged:return error('Prévia não encontrada. Analise o arquivo novamente.',404)
                if staged['applied_at']:return jsonify(**json.loads(staged['result']),already_applied=True)
                if staged['expires_at']<time.time():return error('A prévia expirou. Analise novamente o arquivo.',409)
                plan=json.loads(staged['payload'])
                existing={r['code']:dict(r) for r in c.execute('SELECT * FROM ct_branches ORDER BY code'+lock).fetchall()}
                writes=[r for r in plan if r['action'] in ['new','update']]
                for r in writes:
                    current=existing.get(r['code'])
                    if (fingerprint(current) if current else None)!=r['before']:return error('O cadastro mudou depois da prévia. Analise o arquivo novamente para evitar sobrescritas.',409)
                created=[(secrets.token_hex(16),r['code'],r['name'],r['city'],r['uf'],r['active'],now()) for r in writes if r['action']=='new']
                updated=[(r['name'],r['city'],r['uf'],r['active'],r['before']['id']) for r in writes if r['action']=='update']
                if created:c.executemany('INSERT INTO ct_branches (id,code,name,city,uf,active,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)',created)
                if updated:c.executemany('UPDATE ct_branches SET name=%s,city=%s,uf=%s,active=%s WHERE id=%s',updated)
                result={'created':len(created),'updated':len(updated),'ignored':sum(r['action']=='ignored' for r in plan),'unchanged':sum(r['action']=='unchanged' for r in plan)}
                audit(c,g.user['email'],'importação de filiais',detail={**result,'import_id':uid,'mode':staged['mode']})
                c.execute('UPDATE ct_branch_imports SET payload=%s,applied_at=%s,result=%s WHERE id=%s',('[]',now(),json.dumps(result),uid))
            return jsonify(**result,already_applied=False)
        except Exception as exc:
            if isinstance(exc,sqlite3.IntegrityError) or getattr(exc,'sqlstate',None)=='23505':return error('Uma filial foi cadastrada simultaneamente. Nenhuma linha desta importação foi gravada. Analise o arquivo novamente.',409)
            raise
