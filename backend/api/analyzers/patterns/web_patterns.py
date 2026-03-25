"""
api/analyzers/patterns/web_patterns.py
────────────────────────────────────────
Pattern rules for HTML and CSS.
"""

# ── HTML ──────────────────────────────────────────────────────────────────────
PATTERNS_HTML: list[tuple] = [
    ("<img ",              "error",
     "Missing `alt` attribute on `<img>`",
     "Every `<img>` must have `alt` for accessibility and SEO. "
     "Use `alt=\"\"` for purely decorative images."),

    ("style=\"",           "warning",
     "Avoid inline styles",
     "Inline `style=` mixes presentation with markup, is hard to override, and "
     "prevents caching. Move styles to an external CSS file or `<style>` block."),

    ("<html>",             "warning",
     "Missing `lang` attribute on `<html>`",
     "Declare the page language: `<html lang=\"en\">`. "
     "Required for screen readers and search engines."),

    ("<head>",             "warning",
     "Check `<head>` has viewport and charset meta tags",
     "A well-formed `<head>` needs at minimum:\n"
     "`<meta charset=\"UTF-8\">` and "
     "`<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">`"),

    ("<center",            "error",
     "Deprecated `<center>` tag",
     "`<center>` was removed in HTML5. Use CSS `text-align: center` instead."),

    ("<font ",             "error",
     "Deprecated `<font>` tag",
     "`<font>` was removed in HTML5. Use CSS `font-size`, `color`, `font-family`."),

    ("<marquee",           "error",
     "Deprecated `<marquee>` tag",
     "`<marquee>` was removed in HTML5. Use CSS animations instead."),

    ("<blink",             "error",
     "Deprecated `<blink>` tag",
     "`<blink>` was never standard and is not supported. Use CSS animations."),

    ('target="_blank"',    "warning",
     "Add `rel=\"noopener\"` to `target=\"_blank\"` links",
     "Links opening new tabs without `rel=\"noopener noreferrer\"` expose your page "
     "to tab-napping attacks. Always add both attributes."),

    ('href="#"',           "warning",
     "Avoid `href=\"#\"` as a placeholder",
     "`href=\"#\"` causes the page to jump to the top on click. "
     "Use a `<button>` element for click-only actions."),

    ("<table",             "warning",
     "Avoid `<table>` for layout",
     "Tables are for tabular data, not page layout. "
     "Use CSS Flexbox or Grid for responsive layouts."),

    ("<br><br>",           "warning",
     "Use `<p>` instead of `<br><br>` for paragraph spacing",
     "Double `<br>` is a common mistake. Use `<p>` tags for paragraphs "
     "and control spacing with CSS `margin`."),

    ("onclick=\"",         "warning",
     "Avoid inline event handlers — use `addEventListener`",
     "Inline `onclick=` mixes behaviour with markup. "
     "Use `element.addEventListener('click', handler)` in a separate JS file instead."),
]

# ── CSS ───────────────────────────────────────────────────────────────────────
PATTERNS_CSS: list[tuple] = [
    ("!important",         "warning",
     "Avoid overusing `!important`",
     "`!important` overrides all other styles and makes debugging painful. "
     "Fix specificity at the selector level instead."),

    (": 0px",              "warning",
     "Unnecessary unit on zero value",
     "`margin: 0` is cleaner than `margin: 0px`. CSS zero never needs a unit."),

    ("* {",                "warning",
     "Universal selector `*` can hurt performance",
     "The `*` selector matches every element. "
     "Scope it: `*, *::before, *::after { box-sizing: border-box; }` is acceptable."),

    ("font-family:",       "warning",
     "Add a generic font-family fallback",
     "Always end the font stack with a generic family: "
     "`font-family: 'Roboto', sans-serif`. "
     "This ensures readable text if custom fonts fail to load."),

    ("font-size:",         "warning",
     "Consider `rem` or `em` instead of `px` for font sizes",
     "`px` font sizes don't scale with the user's browser accessibility settings. "
     "Use `rem` (relative to root) or `em` (relative to parent) for accessibility."),

    ("color: white",       "warning",
     "Check colour contrast ratio",
     "White text needs a dark enough background. "
     "WCAG AA requires a contrast ratio of at least 4.5:1 for normal text. "
     "Test at webaim.org/resources/contrastchecker."),

    ("float: ",            "warning",
     "Prefer Flexbox or Grid over `float` for layout",
     "`float` was designed for text wrapping around images, not layout. "
     "Use `display: flex` or `display: grid` for modern, predictable layouts."),

    ("position: absolute", "warning",
     "Check `position: absolute` has a positioned parent",
     "`position: absolute` is relative to the nearest positioned ancestor. "
     "Make sure the parent has `position: relative` (or another non-static value)."),

    ("z-index:",           "warning",
     "Avoid arbitrary high `z-index` values",
     "Using `z-index: 9999` creates a z-index race. "
     "Use a stacking context strategy with small, documented values (1–10)."),

    ("@import ",           "warning",
     "Avoid CSS `@import` — it blocks rendering",
     "`@import` loads stylesheets sequentially, blocking page rendering. "
     "Use `<link>` tags in HTML or a build tool to bundle CSS instead."),
]
