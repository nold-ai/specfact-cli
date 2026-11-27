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
