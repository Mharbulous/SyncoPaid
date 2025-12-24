# Skill Troubleshooting

Common issues when running this skill and how to resolve them.

## Skill Execution Problems

### Can't Detect Project Type

**Symptoms**: Skill can't determine if it's a web app, API, CLI, etc.

**Solutions**:

1. **Ask user directly**:
   ```
   I couldn't automatically detect the application type.
   What type of application is this?
   - Web application
   - REST/GraphQL API
   - CLI tool
   - Desktop application
   - Other
   ```

2. **Request path to main entry point**:
   ```
   Where is the main entry point file for this application?
   ```

3. **Generate generic structure**:
   - Create a generic documentation structure
   - Refine based on user feedback

### Missing Configuration Information

**Symptoms**: Can't find config defaults, options, or format.

**Solutions**:

1. **Check for example configs**:
   ```bash
   ls -la | grep -E "(\.env\.example|config\.example|\.sample)"
   ```

2. **Search for default values**:
   ```bash
   grep -r "defaultConfig\|DEFAULT_\|defaults:" --include="*.{js,ts,py,json}"
   ```

3. **Ask user**:
   ```
   I couldn't find configuration documentation. Do you have:
   - A config.example file?
   - Environment variable documentation?
   - A default configuration I should reference?
   ```

### Unclear User Workflows

**Symptoms**: Can't determine how users interact with the application.

**Solutions**:

1. **Ask user to describe use cases**:
   ```
   Describe the 3 main tasks users perform with this application:
   1.
   2.
   3.
   ```

2. **Analyze routing/URL structure**:
   - Web apps: Look at routes for user-facing pages
   - APIs: Look at endpoint naming patterns
   - CLI: Look at command names

3. **Check test files for usage patterns**:
   ```bash
   grep -r "describe\|it(\|test(" tests/ spec/
   ```

## Content Generation Issues

### Hallucinating Features

**Symptoms**: Generating documentation for features that don't exist.

**Prevention**:

1. **Mark confidence levels**:
   - High: Verified against code
   - Medium: Inferred from patterns
   - Low: Needs verification

2. **Use TODO markers liberally**:
   ```markdown
   > **TODO**: Verify this feature exists and works as described.
   ```

3. **Stick to observable patterns**:
   - Only document what you can find in code
   - When uncertain, describe what code does rather than inferring intent

### Too Technical for End Users

**Symptoms**: Using developer jargon, implementation details.

**Solutions**:

1. **Focus on "what" and "why"**:
   - What the user can do
   - Why they would do it
   - NOT how it's implemented

2. **Use analogies**:
   - "Think of it like a..."
   - "Similar to how you would..."

3. **Add glossary**:
   ```markdown
   ## Glossary

   **API Key**: A unique code that identifies your account...
   **Endpoint**: A URL where the API receives requests...
   ```

### Examples Don't Work

**Symptoms**: Code samples are incorrect or incomplete.

**Solutions**:

1. **Extract from test files**:
   - Test files often have working examples
   - Use these as templates

2. **Mark for verification**:
   ```markdown
   > **Verify this example**: This code sample was auto-generated
   > and may need adjustment.
   ```

3. **Use placeholder format**:
   ```bash
   # Replace [YOUR_VALUE] with your actual value
   command --option [YOUR_VALUE]
   ```

## SSG Setup Issues

### Build Errors

**Symptoms**: Static site generator fails to build.

**Solutions**:

1. **Verify all files present**:
   - Check required config files exist
   - Check all referenced pages exist

2. **Check configuration syntax**:
   - YAML: Proper indentation
   - JSON: Valid JSON (no trailing commas)
   - JS: Valid JavaScript

3. **Run verbose build**:
   ```bash
   # MkDocs
   mkdocs build --verbose

   # Docusaurus
   npm run build -- --verbose

   # VitePress
   npm run docs:build -- --debug
   ```

4. **Fallback to plain Markdown**:
   - If SSG keeps failing, offer plain Markdown alternative
   - Can always add SSG later

### Broken Links

**Symptoms**: Internal links don't work in built site.

**Solutions**:

1. **Check link formats**:
   - MkDocs: Relative paths from current file
   - Docusaurus: From docs root
   - VitePress: From docs root

2. **Run link checker**:
   ```bash
   # MkDocs
   mkdocs build --strict

   # Docusaurus
   npm run build  # Reports broken links
   ```

3. **Use consistent extension**:
   - Some SSGs want `.md`, others don't
   - Check SSG documentation

### Navigation Not Showing

**Symptoms**: Sidebar/nav missing or incomplete.

**Solutions**:

1. **Verify nav configuration**:
   - MkDocs: Check `nav:` in mkdocs.yml
   - Docusaurus: Check sidebars.js
   - VitePress: Check sidebar in config

2. **Check file paths match**:
   - Paths in config must match actual file locations
   - Case-sensitive on Linux

## Performance Issues

### Skill Taking Too Long

**Symptoms**: Documentation generation is very slow.

**Solutions**:

1. **Reduce scope**:
   - Start with "Quick start only" depth
   - Add more content incrementally

2. **Skip advanced features**:
   - Don't set up versioning initially
   - Don't configure multi-language
   - Add these later if needed

3. **Generate in phases**:
   - Phase 1: Core docs only
   - Phase 2: Reference sections
   - Phase 3: Advanced features

## Common Mistakes

### Generating Too Much Content

**Problem**: Creating 50+ pages of mediocre content.

**Solution**:
- Better to have 10-15 excellent pages
- Focus on most common user tasks
- Add more later based on user feedback

### Ignoring Existing Documentation

**Problem**: Not incorporating existing README or docs.

**Solution**:
1. Read existing docs first
2. Incorporate good content
3. Improve structure/format

### Skipping Local Testing

**Problem**: Delivering docs that don't build.

**Solution**:
- Always run local preview before declaring complete
- Fix all build errors
- Check key pages render correctly
