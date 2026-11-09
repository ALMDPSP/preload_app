"""Deployment initializer with visible milestones and non-secret failure diagnostics."""
import time
from release import APP_VERSION

def log(message):print('[inicialização] '+message,flush=True)

def main():
    started=time.monotonic()
    log(f'Versão {APP_VERSION}. Carregando aplicação e validando configuração...')
    try:
        from app import init_db
        init_db(log=log)
    except Exception as exc:
        sqlstate=getattr(exc,'sqlstate',None)
        category=type(exc).__name__+(f' (SQLSTATE {sqlstate})' if sqlstate else '')
        log('Inicialização interrompida: '+category+'. Confira o erro abaixo antes de repetir o deploy.')
        raise
    log(f'Estrutura do banco conferida. Inicialização concluída em {time.monotonic()-started:.2f}s. Iniciando servidor web.')

if __name__=='__main__':main()
