# SYNCOPaiD Landing Page

This is the product landing page for SYNCOPaiD, built with clean HTML, CSS, and vanilla JavaScript.

## Structure

```
www/
├── index.html          # Main landing page
├── styles.css          # All styling
├── script.js           # Interactive features
├── assets/
│   ├── logo.svg        # SYNCOPaiD banner logo
│   └── icon.svg        # Stopwatch pictogram icon
└── README.md           # This file
```

## Features

- **Responsive Design**: Works on all screen sizes (desktop, tablet, mobile)
- **Modern UI**: Clean, professional design with gradient accents
- **Smooth Animations**: Scroll-based animations and transitions
- **SEO Friendly**: Proper meta tags and semantic HTML
- **Fast Loading**: No external dependencies, pure vanilla code

## Color Scheme

The design uses colors inspired by the SYNCOPaiD branding:
- **Gold**: `#c9a855` (primary color from logo gradient)
- **Navy Blue**: `#000080` (secondary color from logo)
- **Light Gold**: `#e8d9a0` (accent color)
- **Dark Gold**: `#8b7332` (darker accent)

## Sections

1. **Hero** - Main call-to-action with download button
2. **Features** - 6 key features in a grid layout
3. **How It Works** - 3-step process explanation
4. **Pricing** - 3 pricing tiers (Free Trial, Pro, Lifetime)
5. **Download** - Secondary call-to-action
6. **Footer** - Links and legal information

## Usage

### Local Development

Simply open `index.html` in a web browser:

```bash
# Windows
start index.html

# Or use a local server (recommended)
python -m http.server 8000
# Then visit http://localhost:8000
```

### Deployment

Upload all files to your web hosting:
- index.html
- styles.css
- script.js
- assets/ folder with both SVG files

### Customization

**Update Content:**
- Edit `index.html` to change text, headings, and pricing
- Modify feature descriptions in the features section
- Update pricing tiers and amounts

**Change Colors:**
- Edit CSS variables in `styles.css` (`:root` section)
- Main colors: `--primary-color`, `--secondary-color`

**Add Analytics:**
- Add your tracking code before the closing `</body>` tag in `index.html`

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Notes

- All assets are SVG format for crisp display on all screens
- No external dependencies or frameworks required
- Fully responsive and mobile-friendly
- Smooth scroll and animations enhance user experience
