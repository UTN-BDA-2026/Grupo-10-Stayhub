# Guía rápida: uv

`uv` es un gestor de paquetes y entornos virtuales para Python, escrito en Rust. Es significativamente más rápido que `pip` y reemplaza al mismo tiempo a `pip`, `venv` y `pip-tools` en un solo comando.

> **Nota:** esta guía es solo para quienes quieran trabajar en el backend fuera de Docker. Si usás Docker directamente, `uv` ya está integrado en el `Dockerfile` y no necesitás instalarlo.

---

## Instalación

**Ubuntu / Linux / macOS**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Luego reiniciá la terminal o ejecutá `source ~/.bashrc` (o `~/.zshrc` si usás zsh).

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Luego cerrá y volvé a abrir la terminal.

**Verificar instalación**
```bash
uv --version
```

---

## Comandos esenciales

### Crear el entorno virtual e instalar dependencias
Desde la carpeta `backend/`:
```bash
uv sync
```
Esto lee el `pyproject.toml`, crea un entorno virtual en `.venv/` e instala todas las dependencias. Es el equivalente a `python -m venv .venv && pip install -r requirements.txt`.

### Agregar una nueva dependencia
```bash
uv add nombre-del-paquete
```
Actualiza el `pyproject.toml` y el `uv.lock` automáticamente.
```bash
# Ejemplo
uv add httpx
```

### Eliminar una dependencia
```bash
uv remove nombre-del-paquete
```

### Ejecutar un comando dentro del entorno virtual
```bash
uv run python script.py
uv run uvicorn app.main:app --reload
```
No hace falta activar el entorno virtual manualmente.

### Actualizar todas las dependencias
```bash
uv sync --upgrade
```

---

## Flujo de trabajo en equipo

Cuando alguien agrega o elimina una dependencia, commitea los cambios en `pyproject.toml` y `uv.lock`. El resto del equipo solo necesita ejecutar:
```bash
uv sync
```
Esto garantiza que todos tengan exactamente las mismas versiones instaladas.

---

## Diferencias con pip

| Tarea | pip (antes) | uv (ahora) |
|---|---|---|
| Instalar dependencias | `pip install -r requirements.txt` | `uv sync` |
| Agregar paquete | editar `requirements.txt` + `pip install` | `uv add paquete` |
| Crear entorno virtual | `python -m venv .venv` | automático con `uv sync` |
| Ejecutar código | activar `.venv` + `python` | `uv run python` |
