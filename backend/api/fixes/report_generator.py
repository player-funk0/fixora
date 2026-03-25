"""
api/fixes/report_generator.py
────────────────────────────────────────────────────────────────────────────
Report generator: converts raw issues list into the final user-facing response.

Responsibility:
  • Build the human-readable summary sentence
  • Choose corrected code (original / commented / template)
  • Provide learning-mode hints per language

Single responsibility: ONLY report generation. Nothing else.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from ..analyzers.constants import LANG_LABELS, COMMENT_PREFIX


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Report Generator
# ══════════════════════════════════════════════════════════════════════════════

_CLEAN_TEMPLATES: dict[str, str] = {
    "python": """\
# Corrected Python
def calculate_average(numbers):
    if not numbers:
        return 0
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

nums = [10, 20, 30, 40, 50]
print("Average:", calculate_average(nums))""",

    "javascript": """\
// Corrected JavaScript
async function fetchUser(userId) {
  const response = await fetch('/api/users/' + userId);
  const data = await response.json();
  if (data.status === 'active') {
    console.log('User:', data.name);
    return data;
  }
}""",

    "typescript": """\
// Corrected TypeScript
async function getUser(id: number): Promise<User | undefined> {
  const res = await fetch(`/api/users/${id}`);
  const data: User = await res.json();
  if (data.active === true) {
    console.log(data.name);
  }
  return data;
}""",

    "cpp": """\
// Corrected C++
#include <iostream>
int main() {
    int nums[] = {1, 2, 3, 4, 5};
    int sum = 0;
    for (int i = 0; i < 5; i++) {
        sum += nums[i];
    }
    std::cout << "Sum: " << sum << std::endl;
    return 0;
}""",

    "c": """\
// Corrected C
#include <stdio.h>
int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int sum = 0;
    for (int i = 0; i < 5; i++) {
        sum += arr[i];
    }
    printf("Sum: %d\\n", sum);
    return 0;
}""",

    "java": """\
// Corrected Java
public class Main {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3, 4, 5};
        int sum = 0;
        for (int i = 0; i < arr.length; i++) {
            sum += arr[i];
        }
        System.out.println("Sum: " + sum);
    }
}""",

    "go": """\
// Corrected Go
package main
import "fmt"
func main() {
    nums := []int{1, 2, 3, 4, 5}
    sum := 0
    for i := 0; i < len(nums); i++ {
        sum += nums[i]
    }
    fmt.Println("Sum:", sum)
}""",

    "rust": """\
// Corrected Rust
fn main() {
    let nums = vec![1, 2, 3, 4, 5];
    let mut sum = 0;
    for i in 0..nums.len() {
        sum += nums[i];
    }
    println!("Sum: {}", sum);
}""",

    "html": """\
<!-- Corrected HTML -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Page Title</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <h1>Hello World</h1>
    <img src="photo.jpg" alt="Descriptive caption" />
    <a href="https://example.com" target="_blank" rel="noopener noreferrer">
      Visit Example
    </a>
  </body>
</html>""",

    "css": """\
/* Corrected CSS */
body {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  margin: 0;
  padding: 0;
}
h1 { font-size: 2rem; margin: 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 1rem; }""",
}

_LEARNING_HINTS: dict[str, list[str]] = {
    "python": [
        "Run the code — Python's error message tells you the exact line and what's wrong.",
        "Does every `def`, `for`, `while`, `if`, and `class` line end with `:`?",
        "Are you comparing with `== None`? Python prefers `is None` and `is not None`.",
    ],
    "javascript": [
        "Which functions are `async`? Every async call inside them needs `await`.",
        "In `if(...)` conditions, use `===` — what does `=` do differently?",
        "What does `fetch()` return before it is awaited?",
    ],
    "typescript": [
        "Where are you using `any`? What specific type could replace it?",
        "Are all async calls properly awaited?",
        "Is `!` hiding a null check that should be written explicitly?",
    ],
    "cpp": [
        "Array of N elements: valid indices 0 to N-1. Does your loop use `<` or `<=`?",
        "Does every statement end with `;`? Does every `{` have a `}`?",
        "Are you managing memory with raw `new`? Consider `unique_ptr`.",
    ],
    "c": [
        "Array of N: indices 0 to N-1. Does your loop condition use `<` or `<=`?",
        "For every `malloc()`, is there a matching `free()`?",
        "Are you using `gets()`? It was removed in C11 — use `fgets()`.",
    ],
    "java": [
        "Java: `=<` or `<=` — which is the correct less-than-or-equal operator?",
        "Should you use `==` or `.equals()` to compare Strings?",
        "Is every array access in the valid index range (0 to length-1)?",
    ],
    "go": [
        "Go: `=<` or `<=` — which is valid syntax?",
        "After every function call, are you checking `if err != nil`?",
        "Does every `(` have a matching `)`?",
    ],
    "rust": [
        "Rust: `0..n` excludes n; `0..=n` includes n. Which is safe for indexing?",
        "Every `.unwrap()` can panic — can you use `?` or `match` instead?",
        "Can you borrow (`&`) instead of `.clone()` to avoid copying data?",
    ],
    "html": [
        "Do all `<img>` tags have an `alt` attribute?",
        "Are you using deprecated `<center>` or `<font>` tags? What CSS replaces them?",
        "Does `<html>` have `lang=\"en\"`? Does `<head>` have a viewport meta tag?",
    ],
    "css": [
        "Are you using `!important`? Can specificity be fixed without it?",
        "Are font sizes in `px`? What would `rem` give you instead?",
        "Does `font-family` end with a generic fallback like `sans-serif`?",
    ],
    "csharp": [
        "Are you catching base `Exception`? Can you catch a more specific type?",
        "Are you using `Thread.Sleep()`? Replace with `await Task.Delay()`.",
        "Are string comparisons culture-aware?",
    ],
    "ruby": [
        "Are you using `== nil` or the idiomatic `.nil?` method?",
        "Are you rescuing `Exception` or the safer `StandardError`?",
        "Any `puts` statements left from debugging?",
    ],
}

_GENERIC_HINTS = [
    "Read each line — does every statement end correctly for this language?",
    "Trace your loop variable — what value does it have on the last iteration?",
    "Are comparison operators (`==`, `<=`) used where you meant to compare, not assign?",
]


def _generate_corrected_code(code: str, language: str, issues: list[dict]) -> str:
    """
    Return corrected code.
    - No issues → return original code unchanged.
    - Warnings only → return original code (it runs fine, just needs improvement).
    - Errors exist → return the language template (shows correct version).
    """
    if not issues:
        return code
    has_errors = any(i["type"] == "error" for i in issues)
    if not has_errors:
        # Code is runnable — return original with a note prepended
        prefix = COMMENT_PREFIX.get(language, "#")
        return f"{prefix} Fixora: code runs but has warnings — see suggestions above.\n{code}"
    template = _CLEAN_TEMPLATES.get(language)
    if template:
        return template
    prefix = COMMENT_PREFIX.get(language, "#")
    return f"{prefix} Fixora: fix the errors above before running.\n{code}"


def _generate_summary(language: str, issues: list[dict]) -> str:
    lang     = LANG_LABELS.get(language, language.capitalize())
    err_cnt  = sum(1 for i in issues if i["type"] == "error")
    warn_cnt = sum(1 for i in issues if i["type"] == "warning")
    total    = err_cnt + warn_cnt
    if total == 0:
        return f"{lang} code looks clean — no errors or warnings detected. Great work!"
    if err_cnt == 0:
        return (f"{lang} code has {warn_cnt} warning{'s' if warn_cnt != 1 else ''} "
                "to review — it should still run, but these are worth fixing.")
    if warn_cnt == 0:
        return (f"{lang} code contains {err_cnt} error{'s' if err_cnt != 1 else ''} "
                "that will prevent it from running correctly.")
    return (f"{lang} code contains {err_cnt} error{'s' if err_cnt != 1 else ''} "
            f"and {warn_cnt} warning{'s' if warn_cnt != 1 else ''}.")


