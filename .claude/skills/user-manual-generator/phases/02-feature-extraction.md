# Phase 2: Feature Extraction

Extract user-facing features from the codebase based on the application type identified in Phase 1.

## For Web Applications

### Extract Routes and Navigation

```bash
# React Router / Next.js
grep -r "Route path=" --include="*.jsx" --include="*.tsx"
grep -r "export default function.*Page" app/ pages/

# Vue Router
grep -r "path:" --include="router.js" --include="*.route.js"

# Angular
grep -r "path:" --include="*.routing.ts"
```

### Identify User-Facing Components

Use `Grep` to find:
- Form components: Search for `<form`, `onSubmit`, `FormProvider`, `useForm`
- Interactive elements: `onClick`, `onChange`, `@click`, `@change`
- Modal/dialog components: `Dialog`, `Modal`, `Popup`
- Navigation: `Navbar`, `Sidebar`, `Menu`, `Header`

### Extract UI Features

Read key component files to understand:
- Input validation rules (for documenting constraints)
- Error messages (for troubleshooting section)
- Success messages (for expected outcomes)
- Button labels and actions (for task documentation)

## For Backend APIs

### Extract Endpoints

```bash
# Express/Fastify
grep -r "router\.\(get\|post\|put\|delete\|patch\)" --include="*.js" --include="*.ts"
grep -r "app\.\(get\|post\|put\|delete\|patch\)" --include="*.js" --include="*.ts"

# Django/Flask
grep -r "@app\.route\|path(" --include="*.py"
grep -r "class.*ViewSet\|class.*APIView" --include="*.py"

# FastAPI
grep -r "@app\.\(get\|post\|put\|delete\|patch\)" --include="*.py"
```

### Find Authentication Patterns

```bash
# Look for auth middleware/decorators
grep -r "authenticate\|authorize\|@login_required\|requireAuth" --include="*.{js,ts,py}"

# Look for API key handling
grep -r "API_KEY\|apiKey\|x-api-key\|Authorization" --include="*.{js,ts,py}"
```

### Extract Request/Response Schemas

- Look for TypeScript interfaces/types near API routes
- Find Pydantic models, Joi schemas, Yup validators
- Check for OpenAPI/Swagger annotations

## For CLI Applications

### Extract Commands and Options

```bash
# Node.js (Commander, Yargs)
grep -r "\.command\|\.option\|\.argument" --include="*.js" --include="*.ts"

# Python (argparse, click, typer)
grep -r "add_argument\|@click\.command\|@app\.command" --include="*.py"

# Go (cobra, flag)
grep -r "cobra\.Command\|flag\." --include="*.go"
```

### Find Help Text

Read command definition files to extract:
- Command descriptions
- Argument descriptions
- Option flags and their purposes
- Usage examples (often in help text)

## For Desktop Applications

### Extract Menu Structures

```bash
# Electron
grep -r "Menu\.buildFromTemplate\|new MenuItem" --include="*.js" --include="*.ts"
```

### Find Settings/Preferences

```bash
grep -r "settings\|preferences\|config" --include="*.{js,ts,json}"
```

## Cross-Application Analysis

### Configuration Options

Read these files to document user-configurable settings:
- `.env.example` or `env.sample`
- `config/default.json`, `config.example.js`
- Settings files in user data directories
- Command-line argument parsers

### Error Messages for Troubleshooting

```bash
# Find error messages
grep -r "throw new Error\|raise Exception\|console\.error" --include="*.{js,ts,py}" | head -50

# Find validation messages
grep -r "validation\|validator\|schema" --include="*.{js,ts,py}"
```

### Example Code

Check for:
- `examples/` directory
- `demo/` directory
- Test files that show usage patterns
- README code samples

## Technology-Specific Patterns

For detailed patterns for specific frameworks (React, Express, Django, etc.), read `reference/tech-patterns.md`.

## Next Phase

Once features are extracted, proceed to **Phase 3: Structure Planning** by reading `phases/03-structure-planning.md`.
