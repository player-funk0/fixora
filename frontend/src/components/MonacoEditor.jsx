import { useEffect, useRef, useState } from "react";

const MONACO_CDN =
  "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs";

// Monaco maps our language slugs to its own language IDs
const LANG_MAP = {
  cpp:        "cpp",
  c:          "c",
  csharp:     "csharp",
  typescript: "typescript",
  rust:       "rust",
  go:         "go",
};
const toMonacoLang = (lang) => LANG_MAP[lang] ?? lang;

export default function MonacoEditor({ value, onChange, language }) {
  const containerRef = useRef(null);
  const editorRef    = useRef(null);
  const monacoRef    = useRef(null);
  const [ready, setReady] = useState(false);

  // ── Boot Monaco from CDN once ───────────────────────────────────────────────
  useEffect(() => {
    if (window.monaco) {
      initEditor();
      return;
    }

    // Prevent double-loading if called concurrently
    if (document.querySelector(`script[data-monaco-loader]`)) return;

    const script = document.createElement("script");
    script.src = `${MONACO_CDN}/loader.min.js`;
    script.dataset.monacoLoader = "1";
    script.onload = () => {
      window.require.config({ paths: { vs: MONACO_CDN } });
      window.require(["vs/editor/editor.main"], (monaco) => {
        window.monaco = monaco;
        initEditor();
      });
    };
    document.head.appendChild(script);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function initEditor() {
    if (editorRef.current || !containerRef.current) return;
    const monaco = window.monaco;
    monacoRef.current = monaco;

    // ── Custom Fixora theme ────────────────────────────────────────────────
    monaco.editor.defineTheme("fixora-dark", {
      base:    "vs-dark",
      inherit: true,
      rules: [
        { token: "comment",  foreground: "4a5568", fontStyle: "italic" },
        { token: "keyword",  foreground: "00ffb4", fontStyle: "bold"   },
        { token: "string",   foreground: "ffd580"                      },
        { token: "number",   foreground: "f093fb"                      },
        { token: "function", foreground: "79c0ff"                      },
        { token: "type",     foreground: "ff9f7e"                      },
      ],
      colors: {
        "editor.background":                  "#080a0f",
        "editor.foreground":                  "#cdd6f4",
        "editor.lineHighlightBackground":     "#0d1117",
        "editorLineNumber.foreground":        "#2d3748",
        "editorLineNumber.activeForeground":  "#00ffb4",
        "editor.selectionBackground":         "#1a3a2a",
        "editorCursor.foreground":            "#00ffb4",
        "editorIndentGuide.background":       "#1a2030",
      },
    });

    editorRef.current = monaco.editor.create(containerRef.current, {
      value:                      value ?? "",
      language:                   toMonacoLang(language),
      theme:                      "fixora-dark",
      fontSize:                   13,
      fontFamily:                 "'JetBrains Mono', 'Fira Code', monospace",
      fontLigatures:              true,
      lineHeight:                 22,
      minimap:                    { enabled: false },
      scrollBeyondLastLine:       false,
      wordWrap:                   "on",
      tabSize:                    2,
      automaticLayout:            true,
      padding:                    { top: 16, bottom: 16 },
      renderLineHighlight:        "gutter",
      smoothScrolling:            true,
      cursorBlinking:             "smooth",
      cursorSmoothCaretAnimation: "on",
    });

    editorRef.current.onDidChangeModelContent(() => {
      onChange?.(editorRef.current.getValue());
    });

    setReady(true);
  }

  // ── Sync language when dropdown changes ────────────────────────────────────
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current) return;
    const model = editorRef.current.getModel();
    if (model) {
      monacoRef.current.editor.setModelLanguage(model, toMonacoLang(language));
    }
  }, [language]);

  // ── Sync value when parent changes it (sample load / file upload) ──────────
  useEffect(() => {
    if (!editorRef.current) return;
    if (editorRef.current.getValue() !== value) {
      editorRef.current.setValue(value ?? "");
    }
  }, [value]);

  return (
    <div style={{ position: "relative", minHeight: 320 }}>
      {!ready && (
        <div className="monaco-loading">LOADING EDITOR…</div>
      )}
      <div ref={containerRef} style={{ height: 340, width: "100%" }} />
    </div>
  );
}
