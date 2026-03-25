"""
api/analyzers/python_analyzer.py
────────────────────────────────────────────────────────────────────────────
Real Python analysis using the built-in `ast` module.

Responsibility:
  • Parse Python code with the real Python parser (syntax errors → exact line)
  • Walk the AST to detect logic & style issues (semantics, not substrings)
  • Token-level checks (mixed indentation)
  • Line-level checks (TODO/secrets)

Single responsibility: ONLY Python analysis. Nothing else.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import ast as _ast
import io as _io
import re
import tokenize as _tokenize

from .base import make_issue_list


def _parse_python(code: str) -> list[dict]:
    """
    Real Python analysis using the built-in `ast` module.
    Catches actual syntax errors with exact line numbers,
    then walks the AST to detect logic & style issues.
    """
    issues, add = make_issue_list()
    lines = code.splitlines()

    # ── Syntax check ──────────────────────────────────────────────────────────
    try:
        tree = _ast.parse(code)
    except SyntaxError as e:
        lineno = e.lineno or 1
        msg    = e.msg or "Syntax error"
        _FRIENDLY = {
            "invalid syntax":
                "Python can't understand this line. Check for missing colons `:`, "
                "mismatched brackets, or incorrect operators.",
            "expected ':'":
                "A colon `:` is missing. Python requires `:` at the end of "
                "`def`, `class`, `if`, `for`, `while`, `with`, and `try` lines.",
            "unexpected EOF while parsing":
                "The code ends unexpectedly. A bracket `(`, `[`, or `{` was opened but never closed.",
            "EOL while scanning string literal":
                "A string quote `'` or `\"` was opened but never closed on the same line.",
            "cannot assign to literal":
                "You tried to assign to a value like `1 = x`. The variable must be on the left.",
            "cannot assign to function call":
                "You tried to assign to a function call like `foo() = x`. This is not valid Python.",
            "positional argument follows keyword argument":
                "In a function call, positional arguments must come BEFORE keyword arguments.",
            "duplicate argument":
                "A function has a duplicate parameter name. Each parameter must be unique.",
            "non-default argument follows default argument":
                "Parameters with default values must come AFTER parameters without defaults.",
        }
        explanation = _FRIENDLY.get(
            msg.lower(),
            f"Python raised a SyntaxError: {msg}. Check the highlighted line carefully."
        )
        add(lineno, "error", f"Syntax error: {msg}", explanation)
        return issues  # can't walk AST without a valid parse

    # ── AST walk ──────────────────────────────────────────────────────────────

    for node in _ast.walk(tree):

        # Mutable default arguments: def foo(x=[], y={})
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            for default in (node.args.defaults +
                            [d for d in node.args.kw_defaults if d is not None]):
                if isinstance(default, (_ast.List, _ast.Dict, _ast.Set)):
                    kind = type(default).__name__.lower()
                    add(node.lineno, "error",
                        "Mutable default argument",
                        f"Using a `{kind}` as a default argument is a classic Python bug. "
                        f"The SAME `{kind}` object is shared across ALL calls to `{node.name}()`. "
                        f"Use `None` as default:\n"
                        f"    def {node.name}(x=None):\n        if x is None: x = {kind[0:4]}()")

        # Division → possible ZeroDivisionError
        # Only warn when the right operand is a variable/call (not a literal number)
        # and the expression is NOT a pathlib-style path join (left operand is Path-like)
        if isinstance(node, _ast.BinOp) and isinstance(node.op, (_ast.Div, _ast.FloorDiv)):
            right = node.right
            left  = node.left
            # Skip literal denominators (x / 2 cannot divide by zero)
            if isinstance(right, _ast.Constant) and isinstance(right.value, (int, float)):
                pass
            # Skip pathlib path joins: self.path / filename
            elif isinstance(left, _ast.Attribute) and left.attr in (
                    "path", "base", "root", "dir", "parent"):
                pass
            elif isinstance(left, _ast.Name) and left.id in ("path", "base", "root"):
                pass
            else:
                add(node.lineno, "warning",
                    "Possible division by zero",
                    "If the denominator can be zero at runtime, Python raises `ZeroDivisionError`. "
                    "Guard with: `if denominator != 0:` before dividing.")

        # Bare except:
        if isinstance(node, _ast.ExceptHandler) and node.type is None:
            add(node.lineno, "warning",
                "Bare `except:` catches everything",
                "Using `except:` with no type silently catches ALL exceptions "
                "including `KeyboardInterrupt`. "
                "Use `except Exception:` or a specific exception type.")

        # Comparison to None with == or !=
        if isinstance(node, _ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(comp, _ast.Constant) and comp.value is None:
                    if isinstance(op, _ast.Eq):
                        add(node.lineno, "warning",
                            "Use `is None` instead of `== None`",
                            "The correct Python idiom is `if x is None:`. "
                            "`==` can be overridden by custom `__eq__` methods.")
                    elif isinstance(op, _ast.NotEq):
                        add(node.lineno, "warning",
                            "Use `is not None` instead of `!= None`",
                            "The correct idiom is `if x is not None:`.")

        # Comparison to True / False
        if isinstance(node, _ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(comp, _ast.Constant):
                    if comp.value is True and isinstance(op, _ast.Eq):
                        add(node.lineno, "warning",
                            "Redundant comparison to `True`",
                            "`if x == True:` is redundant. Just write `if x:`.")
                    elif comp.value is False and isinstance(op, _ast.Eq):
                        add(node.lineno, "warning",
                            "Redundant comparison to `False`",
                            "`if x == False:` is redundant. Write `if not x:` instead.")

        # assert (condition, message) tuple — always True
        if isinstance(node, _ast.Assert) and isinstance(node.test, _ast.Tuple):
            add(node.lineno, "error",
                "`assert (condition, message)` — tuple is always True",
                "A non-empty tuple is ALWAYS truthy. This assertion never fails. "
                "You meant: `assert condition, message` (no parentheses around both).")

        # Global variable
        if isinstance(node, _ast.Global):
            add(node.lineno, "warning",
                "Use of `global` keyword",
                "Modifying globals inside functions makes code hard to test. "
                "Pass the value as a parameter and return the modified result.")

        # Shadowing builtins
        _BUILTINS = {
            "list","dict","set","tuple","str","int","float","bool","type",
            "len","range","print","input","open","sum","min","max","abs",
            "map","filter","zip","enumerate","sorted","reversed","any","all",
        }
        if isinstance(node, _ast.Assign):
            for target in node.targets:
                if isinstance(target, _ast.Name) and target.id in _BUILTINS:
                    add(node.lineno, "warning",
                        f"Shadowing built-in `{target.id}`",
                        f"Assigning to `{target.id}` hides Python's built-in. "
                        "Choose a different variable name to avoid confusing errors.")

        # String += in loop → O(n²)
        if isinstance(node, (_ast.For, _ast.While)):
            for child in _ast.walk(node):
                if (isinstance(child, _ast.AugAssign) and
                        isinstance(child.op, _ast.Add) and
                        isinstance(child.value, _ast.Constant) and
                        isinstance(child.value.value, str)):
                    add(child.lineno, "warning",
                        "String `+=` inside a loop — O(n²) performance",
                        "Each `+=` creates a new string object. For many iterations this is slow. "
                        "Collect parts in a list:\n"
                        "    parts = []\n    for ...: parts.append(x)\n    result = ''.join(parts)")
                    break

        # Unused loop variable
        if isinstance(node, _ast.For) and isinstance(node.target, _ast.Name):
            var = node.target.id
            if var != "_" and hasattr(_ast, "unparse"):
                body_src = _ast.unparse(node)
                if body_src.count(var) == 1:  # only in target declaration
                    add(node.lineno, "warning",
                        f"Loop variable `{var}` unused in body",
                        f"`{var}` is declared in `for {var} in ...` but never used. "
                        f"Rename to `_` if intentional.")

    # ── Token-level: mixed indentation ────────────────────────────────────────
    try:
        tokens = list(_tokenize.generate_tokens(_io.StringIO(code).readline))
        indent_types: set[str] = set()
        for tok in tokens:
            if tok.type == _tokenize.INDENT:
                if "\t" in tok.string: indent_types.add("tab")
                if " "  in tok.string: indent_types.add("space")
        if len(indent_types) == 2:
            add(1, "error",
                "Mixed tabs and spaces",
                "Python 3 forbids mixing tabs and spaces. This causes `TabError` at runtime. "
                "Use spaces only — PEP 8 recommends 4 spaces per level.")
    except Exception:
        pass

    # ── Line-level: TODO/FIXME, hardcoded secrets ─────────────────────────────
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#") and any(k in stripped.upper()
                                            for k in ("TODO","FIXME","HACK","XXX")):
            add(lineno, "warning", "Unresolved TODO/FIXME",
                "A TODO or FIXME comment was found. Make sure this is not forgotten work.")
            break
    for lineno, line in enumerate(lines, start=1):
        if re.search(r"(password|secret|api_key|token)\s*=\s*['\"]", line, re.I):
            add(lineno, "warning", "Possible hardcoded credential",
                "A secret-looking variable is assigned a string literal. "
                "Use environment variables or a `.env` file instead.")
            break

    return issues


