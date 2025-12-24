# Technology-Specific Patterns

Load this file when documenting specific technology stacks.

## React Applications

### Key Files to Analyze

- `src/App.js` or `src/App.tsx`: Main app structure
- `src/pages/` or `pages/`: Page components
- `src/components/`: Reusable components
- `src/hooks/`: Custom hooks (document for advanced users)
- `src/context/`: Context providers

### What to Document

- Component props (if exposed to users via config)
- Routing structure (maps to user navigation)
- Form validations (user needs to know constraints)
- State management (if users interact with it)

### Don't Document

- Internal component implementation
- Redux/Zustand internals (unless user-configurable)
- Build configuration (developer docs)

### Search Patterns

```bash
# Find routes
grep -r "Route path=" --include="*.jsx" --include="*.tsx"
grep -r "export default function.*Page" pages/

# Find forms
grep -r "onSubmit\|useForm\|FormProvider" --include="*.jsx" --include="*.tsx"

# Find user-facing text
grep -r "placeholder=\|label=" --include="*.jsx" --include="*.tsx"
```

## Express/Node.js APIs

### Key Files to Analyze

- `routes/` or `src/routes/`: API endpoints
- `middleware/`: Auth, rate limiting (document for users)
- `models/`: Data structures (for reference)
- `controllers/`: Business logic

### What to Document

- All endpoints with request/response examples
- Authentication flow from user perspective
- Rate limits and quotas
- Error responses with solutions
- Webhook endpoints (if any)

### Search Patterns

```bash
# Find endpoints
grep -r "router\.\(get\|post\|put\|delete\|patch\)" --include="*.js" --include="*.ts"
grep -r "app\.\(get\|post\|put\|delete\|patch\)" --include="*.js" --include="*.ts"

# Find middleware
grep -r "app\.use\|router\.use" --include="*.js" --include="*.ts"

# Find validation
grep -r "Joi\|yup\|zod\|celebrate" --include="*.js" --include="*.ts"
```

## Python Flask/Django

### Key Files to Analyze

- `views.py` or `routes.py`: Endpoints
- `urls.py`: URL patterns
- `models.py`: Data models (for reference)
- `forms.py`: Form validations
- `serializers.py`: API serializers

### What to Document

- URL routes with examples
- Form fields and validation rules
- Admin interface usage (if applicable)
- Management commands (CLI)

### Search Patterns

```bash
# Django routes
grep -r "path(\|re_path(" --include="urls.py"
grep -r "class.*View\|class.*ViewSet" --include="*.py"

# Flask routes
grep -r "@app\.route\|@blueprint\.route" --include="*.py"

# FastAPI routes
grep -r "@app\.\(get\|post\|put\|delete\|patch\)" --include="*.py"

# Find forms
grep -r "class.*Form\(.*\):" --include="*.py"
```

## FastAPI

### Key Files to Analyze

- `main.py`: Entry point and routes
- `routers/`: API routers
- `models/` or `schemas/`: Pydantic models
- `dependencies.py`: Dependency injection

### What to Document

- All endpoints with typed request/response
- Pydantic model schemas
- Dependency injection (auth, database)
- Background tasks

### Search Patterns

```bash
# Find endpoints
grep -r "@app\.\(get\|post\|put\|delete\|patch\)\|@router\." --include="*.py"

# Find Pydantic models
grep -r "class.*\(BaseModel\)" --include="*.py"

# Find dependencies
grep -r "Depends(" --include="*.py"
```

## CLI Tools (Python - Click/Typer)

### Key Files to Analyze

- `cli.py` or `__main__.py`: Command definitions
- `commands/`: Command modules
- `config.py`: Configuration handling

### What to Document

- Every command with full examples
- All options and flags
- Configuration file format
- Common workflows (combining commands)

### Search Patterns

```bash
# Click commands
grep -r "@click\.command\|@click\.group" --include="*.py"
grep -r "@click\.option\|@click\.argument" --include="*.py"

# Typer commands
grep -r "@app\.command\|typer\.Argument\|typer\.Option" --include="*.py"

# Argparse
grep -r "add_argument\|add_subparsers" --include="*.py"
```

## CLI Tools (Node.js - Commander/Yargs)

### Key Files to Analyze

- `cli.js` or `bin/`: Command definitions
- `commands/`: Command modules
- `lib/`: Core functionality

### Search Patterns

```bash
# Commander
grep -r "\.command(\|\.option(\|\.argument(" --include="*.js" --include="*.ts"

# Yargs
grep -r "yargs\.command\|\.positional\|\.option" --include="*.js" --include="*.ts"

# Help text
grep -r "\.description(\|\.help(" --include="*.js" --include="*.ts"
```

## Go CLI (Cobra)

### Key Files to Analyze

- `cmd/`: Command definitions
- `main.go`: Entry point
- `internal/`: Core functionality

### Search Patterns

```bash
# Cobra commands
grep -r "cobra\.Command\|AddCommand" --include="*.go"

# Flags
grep -r "\.Flags()\.\|PersistentFlags()" --include="*.go"
```

## Desktop Applications (Electron)

### Key Files to Analyze

- `main.js`: Main process (window management, menus)
- `preload.js`: IPC communication
- `src/` or `renderer/`: Renderer process (UI)
- Menu definitions

### What to Document

- Installation per platform
- UI navigation
- Keyboard shortcuts
- Settings/preferences
- File operations (open, save, export)
- Auto-update process (if applicable)

### Search Patterns

```bash
# Menu structure
grep -r "Menu\.buildFromTemplate\|new MenuItem" --include="*.js" --include="*.ts"

# IPC communication
grep -r "ipcMain\|ipcRenderer" --include="*.js" --include="*.ts"

# Keyboard shortcuts
grep -r "accelerator:" --include="*.js" --include="*.ts"
```

## Vue Applications

### Key Files to Analyze

- `src/App.vue`: Main app
- `src/views/` or `src/pages/`: Page components
- `src/components/`: Reusable components
- `src/router/`: Router configuration
- `src/store/`: Vuex/Pinia store

### Search Patterns

```bash
# Find routes
grep -r "path:" --include="router.js" --include="*.ts" src/router/

# Find components
ls src/components/

# Find store modules
grep -r "defineStore\|createStore" --include="*.js" --include="*.ts"
```

## Angular Applications

### Key Files to Analyze

- `src/app/`: Application modules
- `src/app/*-routing.module.ts`: Routing modules
- `src/environments/`: Environment configs

### Search Patterns

```bash
# Find routes
grep -r "path:\|Routes" --include="*.routing.ts" --include="*.module.ts"

# Find services
grep -r "@Injectable" --include="*.service.ts"

# Find components
grep -r "@Component" --include="*.component.ts"
```
