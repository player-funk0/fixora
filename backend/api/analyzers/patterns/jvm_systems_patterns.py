"""
api/analyzers/patterns/jvm_systems_patterns.py
────────────────────────────────────────────────
Pattern rules for: Java, Go, Rust, C#, Ruby.
Each exported as PATTERNS_<LANG>.
"""

# ── Java ──────────────────────────────────────────────────────────────────────
PATTERNS_JAVA: list[tuple] = [
    ("=<",                 "error",
     "Invalid operator `=<` — did you mean `<=`?",
     "Java has no `=<` operator. Less-than-or-equal is `<=` (less-than first, then equals)."),

    ('== "',               "error",
     "Use `.equals()` for String comparison, not `==`",
     "`==` compares object references in Java, not values. "
     "Two `String` objects with the same text are `!=` with `==`. "
     "Use `str1.equals(str2)` or `Objects.equals(a, b)`."),

    ('!= "',               "error",
     "Use `!str.equals(...)` instead of `!=` for String comparison",
     "`!=` compares references, not values. Use `!str1.equals(str2)` for string inequality."),

    ("NullPointerException","warning",
     "NullPointerException risk",
     "Check objects for null before calling methods. "
     "Use `Objects.requireNonNull()` or `Optional<T>` for cleaner null handling."),

    (".get(0)",             "warning",
     "Check list is not empty before `.get(0)`",
     "Calling `.get(0)` on an empty list throws `IndexOutOfBoundsException`. "
     "Check with `if (!list.isEmpty())` first."),

    ("ArrayList(",         "warning",
     "Specify generic type for ArrayList",
     "Raw `ArrayList` loses compile-time type safety. "
     "Use `ArrayList<String>()` or `new ArrayList<>()` with the generic inferred."),

    ("HashMap(",           "warning",
     "Specify generic types for HashMap",
     "Use `HashMap<String, Integer>()` instead of raw `HashMap()` for type safety."),

    ("Vector(",            "warning",
     "Prefer `ArrayList` over `Vector`",
     "`Vector` is synchronized on every operation — slow for single-threaded code. "
     "Use `ArrayList` (or `CopyOnWriteArrayList` if thread-safety is needed)."),

    ("catch (Exception",   "warning",
     "Avoid catching base `Exception`",
     "Catching `Exception` swallows all errors. "
     "Catch specific exceptions you can actually handle."),

    ("catch (Throwable",   "error",
     "Never catch `Throwable`",
     "`Throwable` includes `Error` subclasses like `OutOfMemoryError`. "
     "These are JVM-level failures that cannot be handled gracefully. "
     "Catch `Exception` at most."),

    ("e.printStackTrace(", "warning",
     "Avoid `e.printStackTrace()` in production",
     "`printStackTrace()` writes to stderr and may expose internal stack traces. "
     "Use a proper logger: `logger.error(\"message\", e)`."),

    ("System.exit(",       "warning",
     "Avoid `System.exit()` in library code",
     "`System.exit()` terminates the entire JVM and prevents cleanup. "
     "Throw an exception or return an error code instead."),

    ("synchronized(",      "warning",
     "Review synchronisation scope",
     "Over-synchronisation causes deadlocks and performance issues. "
     "Synchronise only the minimum required section, "
     "or use `java.util.concurrent` utilities."),

    ("Integer.parseInt(",  "warning",
     "Wrap `Integer.parseInt()` in try-catch for `NumberFormatException`",
     "`parseInt()` throws `NumberFormatException` on invalid input. "
     "Always validate or wrap in try-catch."),
]

# ── Go ────────────────────────────────────────────────────────────────────────
PATTERNS_GO: list[tuple] = [
    ("=<",                 "error",
     "Invalid operator `=<` — did you mean `<=`?",
     "Go's less-than-or-equal is `<=`. `=<` is a compile error."),

    (", err :=",           "warning",
     "Check the returned error value",
     "Ignoring returned errors hides failures. "
     "Always check: `if err != nil { return fmt.Errorf(\"context: %w\", err) }`."),

    ("_ = err",            "error",
     "Explicitly discarding error with `_ = err`",
     "Assigning an error to `_` deliberately ignores it. "
     "This hides failures and should almost never be done."),

    ("go func()",          "warning",
     "Goroutine may leak — ensure it terminates",
     "Goroutines that run forever or lack a stop mechanism are a common memory leak. "
     "Use a `context.Context` with cancellation to control goroutine lifetime."),

    ("time.Sleep(",        "warning",
     "Avoid `time.Sleep` in goroutines — use channels or context",
     "`time.Sleep` blocks the goroutine and makes it unresponsive to cancellation. "
     "Use `select { case <-ctx.Done(): ... case <-time.After(d): ... }` instead."),

    ("ioutil.",            "warning",
     "`ioutil` is deprecated since Go 1.16",
     "Replace: `ioutil.ReadAll` → `io.ReadAll`, `ioutil.ReadFile` → `os.ReadFile`, "
     "`ioutil.WriteFile` → `os.WriteFile`."),

    ("panic(",             "warning",
     "Avoid `panic()` in production code",
     "`panic` crashes the program. Return an `error` value instead. "
     "Reserve `panic` for truly unrecoverable programmer errors."),

    ("defer ",             "warning",
     "Check `defer` is not inside a loop",
     "`defer` inside a loop doesn't execute until the function returns — not each iteration. "
     "Move the deferred call into a helper function called inside the loop."),

    ("append(",            "warning",
     "Capture `append` result — it may return a new slice",
     "`append` may allocate a new backing array. "
     "Always use: `slice = append(slice, item)` — never discard the return value."),
]

# ── Rust ──────────────────────────────────────────────────────────────────────
PATTERNS_RUST: list[tuple] = [
    ("..=",                "error",
     "Inclusive range may cause index out of bounds",
     "`0..=vec.len()` includes index `len` — past the last valid element. "
     "Use exclusive `0..vec.len()` for safe indexing."),

    ("unwrap()",           "warning",
     "`.unwrap()` will panic on None or Err",
     "Use `?` to propagate, `.expect(\"message\")` for descriptive panics, "
     "or `if let` / `match` for safe handling."),

    ('.expect("")',        "warning",
     "`.expect()` with empty message",
     "Provide a descriptive message: `.expect(\"config file should exist\")`."),

    (".clone()",           "warning",
     "Check if `.clone()` is necessary",
     "Borrow (`&T`) instead of cloning when you don't need ownership."),

    ("to_string()",        "warning",
     "Prefer `to_owned()` or `String::from()` for string literals",
     "`.to_string()` on a string literal goes through `Display`. "
     "`\"literal\".to_owned()` or `String::from(\"literal\")` is faster."),

    ("Rc<",                "warning",
     "Use `Arc<T>` instead of `Rc<T>` in multithreaded code",
     "`Rc<T>` is not `Send` or `Sync` — it cannot cross thread boundaries. "
     "Use `Arc<T>` for shared ownership across threads."),

    ("unsafe {",           "warning",
     "`unsafe` block — review carefully",
     "`unsafe` blocks bypass Rust's memory safety guarantees. "
     "Document exactly which invariants you're upholding and why it's safe."),

    ("as usize",           "warning",
     "Casting to `usize` with `as` may truncate or panic",
     "`as` casts are unchecked. A negative `i32` cast to `usize` wraps to a huge number. "
     "Use `.try_into().unwrap()` or validate the value before casting."),

    ("loop {",             "warning",
     "Ensure `loop` has a reachable `break`",
     "An infinite `loop` without a reachable `break` hangs the program. "
     "Make sure every code path through the loop eventually reaches `break`."),
]

# ── C# ────────────────────────────────────────────────────────────────────────
PATTERNS_CSHARP: list[tuple] = [
    ("Thread.Sleep(",      "warning",
     "Avoid `Thread.Sleep()` in async code",
     "In async methods use `await Task.Delay(ms)` instead of `Thread.Sleep()` "
     "to avoid blocking the thread pool."),

    ("catch (Exception",   "warning",
     "Avoid catching base `Exception`",
     "Catch specific exception types you can handle meaningfully."),

    (".Result",            "warning",
     "Avoid `.Result` on Tasks — causes deadlocks in async contexts",
     "Calling `.Result` on a `Task` blocks the calling thread. "
     "In async code this can deadlock. Use `await` instead."),

    (".Wait()",            "warning",
     "Avoid `.Wait()` on Tasks — causes deadlocks",
     "Same issue as `.Result`. Use `await task` instead of `task.Wait()`."),

    ("new List()",         "warning",
     "Specify generic type for `List`",
     "Use `new List<string>()` or `new List<int>()` for type safety."),

    ("Console.WriteLine(", "warning",
     "Remove debug `Console.WriteLine` before production",
     "Use proper logging (`ILogger`, Serilog, NLog) instead of `Console.WriteLine`."),

    ("GC.Collect()",       "error",
     "Never call `GC.Collect()` manually",
     "Forcing garbage collection usually hurts performance. "
     "The .NET GC is highly optimised — trust it to manage memory."),
]

# ── Ruby ──────────────────────────────────────────────────────────────────────
PATTERNS_RUBY: list[tuple] = [
    ("== nil",             "warning",
     "Use `.nil?` instead of `== nil`",
     "The idiomatic Ruby way is `object.nil?`."),

    ("!= nil",             "warning",
     "Use `!object.nil?` or safe navigation `&.` instead of `!= nil`",
     "For method calls on potentially-nil objects, use `object&.method` (safe navigation)."),

    ("rescue Exception",   "warning",
     "Rescue `StandardError`, not `Exception`",
     "Rescuing `Exception` catches fatal signals like `SignalException` and `NoMemoryError`. "
     "Use `rescue StandardError` or a more specific error class."),

    ("puts ",              "warning",
     "Debug `puts` left in code",
     "Remove `puts` before production. Use `Rails.logger.debug` or a logging gem."),

    ("print ",             "warning",
     "Debug `print` left in code",
     "Remove `print` before production. Use a proper logger."),

    ("p ",                 "warning",
     "Debug `p` statement left in code",
     "`p object` is shorthand for debug inspection. Remove before shipping."),

    ("eval(",              "error",
     "Never use `eval()` — security risk",
     "`eval` executes arbitrary Ruby code. Never pass user input to it."),

    ("send(",              "warning",
     "Audit `send()` — can bypass method visibility",
     "`send` can call private methods and may execute unexpected code. "
     "Use only with trusted, validated method names."),

    ("sleep(",             "warning",
     "Avoid `sleep` in production code",
     "`sleep` blocks the thread. Use background jobs (Sidekiq, DelayedJob) "
     "or non-blocking approaches instead."),
]
