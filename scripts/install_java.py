"""Garante um JDK 21 disponivel para o r5py, sem depender de instalacao do sistema.

O R5 (via r5py/jpype) exige uma JVM Java 21. Esta maquina nao tem Java no PATH, entao
baixamos o Temurin 21 (Eclipse Adoptium) e extraimos em Dados/java/ (git-ignorado, mesma
convencao de Dados/osm/ e Dados/r5/). Os modulos que usam r5py devem chamar garantir_java()
e setar os.environ['JAVA_HOME'] ANTES de `import r5py` -- o jpype resolve a JVM no import.

Equivalente ao fluxo em R (rJavaEnv::java_quick_install(21)) usado em outros projetos, mas
sem trazer R/renv para este repo.

Uso:
    python src/install_java.py --check     # so reporta o que ja existe
    python src/install_java.py             # baixa/instala se necessario
"""
from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
JAVA_ROOT = ROOT / 'Dados' / 'java'
JAVA_VERSION = 21

ADOPTIUM_API = (
    'https://api.adoptium.net/v3/binary/latest/{version}/ga/{os}/{arch}/jdk/hotspot/normal/eclipse'
)


def _plataforma() -> tuple[str, str]:
    """Mapeia a plataforma atual para os nomes usados pela API do Adoptium."""
    sistema = {'Windows': 'windows', 'Linux': 'linux', 'Darwin': 'mac'}[platform.system()]
    maquina = platform.machine().lower()
    arch = 'x64' if maquina in ('amd64', 'x86_64') else 'aarch64'
    return sistema, arch


def java_home() -> Path | None:
    """Retorna o JAVA_HOME de um JDK ja extraido em Dados/java/, ou None se nao houver."""
    if not JAVA_ROOT.exists():
        return None
    for candidato in sorted(JAVA_ROOT.glob('jdk-*')):
        java_exe = candidato / 'bin' / ('java.exe' if platform.system() == 'Windows' else 'java')
        if java_exe.exists():
            return candidato
    return None


def _versao_instalada(home: Path) -> str | None:
    java_exe = home / 'bin' / ('java.exe' if platform.system() == 'Windows' else 'java')
    try:
        saida = subprocess.run([str(java_exe), '-version'], capture_output=True, text=True, timeout=15)
        return (saida.stderr or saida.stdout).splitlines()[0] if saida.stderr or saida.stdout else None
    except Exception:
        return None


def baixar_jdk(destino: Path = JAVA_ROOT, versao: int = JAVA_VERSION) -> Path:
    """Baixa e extrai o Temurin `versao` para destino/jdk-<versao>/, retornando o JAVA_HOME."""
    sistema, arch = _plataforma()
    url = ADOPTIUM_API.format(version=versao, os=sistema, arch=arch)
    destino.mkdir(parents=True, exist_ok=True)

    print(f'Baixando Temurin {versao} ({sistema}/{arch}) de {url} ...')
    with requests.get(url, stream=True, timeout=(10, 300)) as resp:
        resp.raise_for_status()
        pacote = destino / f'temurin-{versao}.zip'
        total = int(resp.headers.get('content-length', 0))
        baixado = 0
        with open(pacote, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                baixado += len(chunk)
                if total:
                    print(f'\r  {baixado / 1e6:.0f} / {total / 1e6:.0f} MB', end='')
        print()

    print('Extraindo...')
    extracao_tmp = destino / f'_extract_{versao}'
    if extracao_tmp.exists():
        shutil.rmtree(extracao_tmp, ignore_errors=True)
    with zipfile.ZipFile(pacote) as zf:
        zf.extractall(extracao_tmp)
    pacote.unlink()

    # o zip do Adoptium contem uma unica pasta raiz tipo jdk-21.0.12+8
    (raiz_extraida,) = [p for p in extracao_tmp.iterdir() if p.is_dir()]
    alvo = destino / f'jdk-{versao}'
    if alvo.exists():
        shutil.rmtree(alvo)
    # shutil.move (nao Path.rename): no Windows o rename entre pastas pode falhar com
    # PermissionError se algo (ex.: antivirus) ainda segura um handle na pasta recem-extraida.
    shutil.move(str(raiz_extraida), str(alvo))
    shutil.rmtree(extracao_tmp, ignore_errors=True)

    print(f'JDK {versao} instalado em {alvo}')
    return alvo


def garantir_java(versao: int = JAVA_VERSION) -> Path:
    """Garante um JAVA_HOME utilizavel, baixando o Temurin se necessario. Nao seta env var."""
    home = java_home()
    if home is not None:
        return home
    return baixar_jdk(versao=versao)


def main() -> None:
    parser = argparse.ArgumentParser(description='Garante um JDK 21 local para o r5py.')
    parser.add_argument('--check', action='store_true', help='so reporta o estado atual, nao instala')
    args = parser.parse_args()

    home = java_home()
    if home is not None:
        print(f'JAVA_HOME: {home}')
        versao = _versao_instalada(home)
        print(versao or '(nao foi possivel executar java -version)')
        return

    if args.check:
        print('Nenhum JDK encontrado em Dados/java/. Rode sem --check para instalar.')
        sys.exit(1)

    home = garantir_java()
    versao = _versao_instalada(home)
    print(versao or '(instalado, mas java -version falhou)')


if __name__ == '__main__':
    main()
