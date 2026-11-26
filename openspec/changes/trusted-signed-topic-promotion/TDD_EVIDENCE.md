# Signed topic provenance

Before implementation, the topic fixture could not obtain a promotion
attestation because the verifier had no topic evidence input. The updated
verification accepts the exact signed, merge-ready source and rejects stale
refs, unsigned commits, wrong trees, lookalike topics, fork sources and extra
parents. The workflow tests cover the existing direct promotion path and all
three independent validation stages.
