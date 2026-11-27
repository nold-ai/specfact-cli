## Local evidence

- On protected `dev` at `e46e927c`, the selected CLI test reports the
  missing-await rule on lines 6 and 9. Line 6 calls a synchronous lambda.
- On the reconciled 0.55.19 preview the same test reports only line 9,
  which calls the coroutine without awaiting it.
- The preview retains the exact protected development Requirements workflow.
  The frozen lock refresh changes only the local project version.

## Synchronous loop target regression

- On signed source `6e1b1ae1`, three loop-target cases failed. The scanner
  retained an earlier coroutine when the loop bound the name to a lambda.
- After the fix, the scanner honors the loop target inside each iteration,
  reports a later coroutine rebinding, and still reports a possible
  unawaited coroutine when execution can skip the loop.
- The coroutine iterable control passed before and after the fix. The existing
  hosted Requirements selector and its original evidence retain their bytes.

- On `d64494ca`, two nested-loop cases missed the coroutine binding from a
  previous inner iteration. After applying loop state from outermost to
  innermost, both a direct call and a call through an alias report the
  coroutine. The inner synchronous target control stays clear.

- On `0d1216dd`, four added cases lost a coroutine binding during literal
  unpacking, a tuple swap, or reassignment across loop iterations. The
  synchronous-alias control passed. After the fix, assignments read all
  right-hand bindings before updating their targets, and coroutine bindings
  carry only if they can reach the next iteration. Controls cover an
  unconditional reset and a `continue` that can skip that reset.

- On `07cf8613`, three cases lost coroutine bindings through an intermediate
  function with a `global` or `nonlocal` declaration. The scanner now applies
  enclosing bindings from outermost to innermost, with global writes routed to
  the module and nonlocal writes to the inherited scope. The earlier
  synchronous assignment control stays clear.
