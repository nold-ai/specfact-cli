## Local evidence

- On protected `dev` at `e46e927c`, the selected CLI test reports the
  missing-await rule on lines 6 and 9. Line 6 calls a synchronous lambda.
- On the reconciled 0.55.19 preview the same test reports only line 9,
  which calls the coroutine without awaiting it.
- The preview retains the exact protected development Requirements workflow.
  The frozen lock refresh changes only the local project version.
