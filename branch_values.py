"""Shared normalization for registry and spreadsheet imports."""
import re,unicodedata

def normalized(value):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().lower())

NAMES=['Acre','Alagoas','Amapá','Amazonas','Bahia','Ceará','Distrito Federal','Espírito Santo','Goiás','Maranhão','Mato Grosso','Mato Grosso do Sul','Minas Gerais','Pará','Paraíba','Paraná','Pernambuco','Piauí','Rio de Janeiro','Rio Grande do Norte','Rio Grande do Sul','Rondônia','Roraima','Santa Catarina','São Paulo','Sergipe','Tocantins']
UFS='AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
STATE_NAMES={normalized(name):uf for name,uf in zip(NAMES,UFS)}
def normalize_uf(value):
    text=str(value or '').strip()
    return STATE_NAMES.get(normalized(text),text.upper())

def parse_status(value):
    key=re.sub(r"[ _]+","",unicodedata.normalize("NFKD",str(value)).encode("ascii","ignore").decode().lower().strip())
    if key in {'1','true','sim','s','ativo','ativa'}:return 1,0
    if key in {'0','false','nao','n','inativo','inativa'}:return 0,0
    if key in {'ainaugurar','inaugurar','lojaainaugurar','emimplantacao','openingsoon','ainauguracao'}:return 1,1
    raise ValueError('Situação inválida. Use Ativa, Inativa ou A inaugurar.')

def branch_status(body):
    if 'status' in body:return parse_status(body['status'])
    if not isinstance(body.get('active',True),bool):raise ValueError('Situação da filial inválida.')
    return int(body.get('active',True)),0
