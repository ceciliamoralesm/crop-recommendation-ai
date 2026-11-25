# GitHub: ramas, Pull Requests y revisión con Qodo Merge

**Cómo se trabaja:** las acciones de GitHub (crear el repo, configurar, abrir y fusionar PR, instalar Qodo) se hacen en **la interfaz web**. Todo lo demás se hace con **comandos `git`**. No hace falta `gh`.

| Rama | Para qué |
|---|---|
| `main` | Versión estable que se presenta el 23/11 |
| `develop` | Integración: recibe los PR de las ramas de cambios |
| `feature/...` | Una rama por cada cambio nuevo, que vuelve a `develop` mediante un PR |

---

## Parte 1: crear el repositorio (web)

1. Entra a **https://github.com** con tu cuenta.
2. Arriba a la derecha, pulsa **+ → New repository**.
3. Rellena:
   - **Repository name:** `crop-recommendation-ai`
   - **Description:** `Recomendador de cultivos con IA (CRISP-ML(Q)) · FastAPI + PostgreSQL + React`
   - **Public**
   - **NO** marques *Add a README file*, *.gitignore* ni *license*. El proyecto ya los tiene y, si los marcas, el primer push choca.
4. Pulsa **Create repository**.
5. Copia la URL HTTPS que aparece, por ejemplo `https://github.com/TU_USUARIO/crop-recommendation-ai.git`.

## Parte 2: subir `main` y crear `develop` (comandos)

Abre PowerShell en la carpeta del proyecto:

```powershell
cd C:\Universidad\TallerDeSistemasInteligentes\EvaluacionFinalChachi

# Solo la primera vez en este equipo
git config --global user.name  "Tu Nombre"
git config --global user.email "tu-correo@ejemplo.com"

git init -b main
git add README.md .gitignore docker-compose.yml data/
git commit -m "chore: estructura inicial del proyecto y dataset"
git remote add origin https://github.com/TU_USUARIO/crop-recommendation-ai.git
git push -u origin main
```

En el primer `push` se abre una ventana de **Git Credential Manager**. Elige **Sign in with your browser**, autoriza y listo: no vuelve a pedirlo.

```powershell
git checkout -b develop
git push -u origin develop
```

## Parte 3: configurar el repositorio (web)

1. **Rama por defecto = `develop`**: **Settings → General → Default branch** → icono ⇄ → elige `develop` → **Update** → confirma.
2. **(Opcional) Proteger las ramas**: **Settings → Rules → Rulesets → New ruleset → New branch ruleset**.
   - Nombre: `proteccion`. Enforcement status: **Active**.
   - Target branches → **Add target → Include by pattern**: `main` y también `develop`.
   - Marca **Require a pull request before merging** → **Create**.

## Parte 4: instalar Qodo Merge (web)

1. Entra a **https://github.com/marketplace** y busca **Qodo Merge**. También puedes ir a **https://www.qodo.ai → Qodo Merge → Get started**.
2. Pulsa **Install** o **Set up a plan**, elige el plan gratuito si te lo ofrece y luego **Install it for free**.
3. Elige **Only select repositories** → `crop-recommendation-ai` → **Install**.
4. Para comprobarlo: **Settings → GitHub Apps** (en *Integrations*) debe mostrar Qodo Merge.

## Parte 5: una rama por cambio (comandos) + su PR (web)

### 5.1 Crear la rama y subir el cambio (comandos)

```powershell
# Notebook y modelo
git checkout develop
git pull
git checkout -b feature/notebook-modelo
git add notebooks/
git commit -m "feat(modelo): EDA, comparación de 7 modelos y Random Forest (F1 0.9955)"
git push -u origin feature/notebook-modelo
```

### 5.2 Abrir el Pull Request (web)

1. Entra al repositorio. Aparece un aviso amarillo, *feature/notebook-modelo had recent pushes*, con el botón **Compare & pull request**. Si no aparece, ve a la pestaña **Pull requests → New pull request**.
2. Comprueba arriba: **base: `develop`** ← **compare: `feature/notebook-modelo`**.
3. Título: `feat: notebook de entrenamiento CRISP-ML(Q)`. Descripción: qué incluye.
4. **Create pull request**.

### 5.3 Revisión con Qodo Merge (web)

En el PR, pestaña **Conversation**: Qodo suele comentar solo en uno o dos minutos. Si no, escribe en el cuadro de comentarios y pulsa **Comment**:

| Comentario | Qué hace |
|---|---|
| `/describe` | Genera el resumen del PR |
| `/review` | Revisión: posibles bugs, seguridad, si hay tests y el esfuerzo estimado |
| `/improve` | Sugerencias de código concretas |

**Haz capturas** de esas respuestas y guárdalas en `docs/evidencias/`.

Si aplicas alguna sugerencia, edita el archivo en tu PC y súbelo **a la misma rama**. El PR se actualiza solo:
```powershell
git add .
git commit -m "fix: aplica sugerencia de Qodo Merge"
git push
```

### 5.4 Fusionar (web)

1. Baja al final del PR → **Merge pull request** → **Confirm merge**.
2. Pulsa **Delete branch**.

### 5.5 Repetir con las demás partes

```powershell
# Servicio de IA (API + BD)
git checkout develop
git pull
git checkout -b feature/api-backend
git add backend/
git commit -m "feat(api): servicio FastAPI con PostgreSQL, re-entrenamiento y versionado"
git push -u origin feature/api-backend
```
```powershell
# Cliente web
git checkout develop
git pull
git checkout -b feature/frontend
git add frontend/
git commit -m "feat(web): cliente React que consume todos los endpoints"
git push -u origin feature/frontend
```
```powershell
# Documentación y entregables
git checkout develop
git pull
git checkout -b feature/documentacion
git add docs/ entrega/
git commit -m "docs: documento CRISP-ML(Q), diagrama de BD, Swagger y checklist"
git push -u origin feature/documentacion
```
Después de cada `push`, repite **5.2 → 5.3 → 5.4** en la web.

> **Importante:** antes de crear cada rama haz `git checkout develop` y `git pull`, para que la rama nueva parta de lo que ya fusionaste.

## Parte 6: versión final en `main`

**Web:** **Pull requests → New pull request** → **base: `main`** ← **compare: `develop`** → título `release: versión 1.0 para la presentación` → **Create pull request** → (puedes comentar `/review`) → **Merge pull request** → **Confirm merge**. **No** borres `develop`.

**Comandos** (actualizar tu PC y etiquetar la versión):
```powershell
git checkout main
git pull
git tag v1.0
git push origin v1.0
```

## Evidencias que conviene guardar

- [ ] **Pull requests → Closed**: la lista de PR fusionados
- [ ] Un comentario `/review` de Qodo Merge
- [ ] Un `/improve` y el commit que aplica alguna sugerencia
- [ ] **Insights → Network**: el gráfico de las ramas main, develop y feature
- [ ] La URL del repositorio en las portadas y en la sección 9.2 del documento 01

## Problemas comunes

| Mensaje | Solución |
|---|---|
| `rejected ... fetch first` en el primer push | Marcaste "Add a README" al crear el repo. Ejecuta `git pull origin main --allow-unrelated-histories` y luego `git push` |
| `src refspec main does not match any` | Falta el commit: revisa que `git commit` se ejecutó bien |
| `Author identity unknown` | Ejecuta los dos `git config --global` del Paso 2 |
| No aparece **Compare & pull request** | Ve a **Pull requests → New pull request** y elige las ramas a mano |
