"""
Stylesheet shared by the HTML and EPUB file creators.
It sticks to properties e-readers support and leaves fonts and sizes to the reader's own settings.
"""
EREADER_CSS = """
body { margin: 0 2%; line-height: 1.45; overflow-wrap: break-word; }
a { overflow-wrap: anywhere; }
h1, h2, h3, h4, h5, h6 { line-height: 1.2; page-break-after: avoid; }
h1.article-title { margin: 0 0 0.4em 0; }
h1.article-title a { text-decoration: none; color: inherit; }
p { margin: 0 0 0.8em 0; }
p.byline { font-size: 0.85em; font-style: italic; margin-bottom: 1.4em; }
p.note { font-size: 0.85em; border: 1px solid #888; padding: 0.4em; }
p.article-nav, p.source-link { font-size: 0.85em; margin-top: 1.5em; }
img { max-width: 100%; height: auto; }
figure { margin: 1em 0; text-align: center; page-break-inside: avoid; }
figcaption { font-size: 0.8em; font-style: italic; }
blockquote { margin: 1em 1.5em; font-style: italic; }
pre { white-space: pre-wrap; font-size: 0.85em; }
table { border-collapse: collapse; margin: 1em 0; }
th, td { border: 1px solid #888; padding: 0.2em 0.4em; vertical-align: top; }
section.article { page-break-before: always; }
ol.contents li { margin-bottom: 0.5em; }
ol.contents .meta { font-size: 0.8em; }
"""
