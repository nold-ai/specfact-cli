# Capability Delta: documentation-alignment (handoff conversion)

Core handoff pages are converted from full duplicate content to thin summaries with canonical links.

## Scenarios

### Scenario: Handoff page contains summary and canonical link

Given a core docs page that was previously a full duplicate of module content
When the page is converted to a handoff redirect
Then it contains a 1-2 paragraph summary of what the guide covers
And it contains a prominent canonical link to the modules site URL
And it does NOT contain the full guide content

### Scenario: Old URLs are preserved via redirect

Given a handoff page at its original URL
When a user visits the original URL
Then the page loads (not 404) and displays the summary with canonical link

### Scenario: Each handoff page maps to a valid modules target

Given the 20 identified handoff pages
When each is converted
Then each canonical link points to a page that exists on modules.specfact.io
