# "Compliance-checked" badge

The doc's Section 6 growth idea: a badge maintainers of *other* agent projects can add to their own README once they've integrated AIActGuard — the same viral-distribution loop as CI/coverage badges. Anyone who adds it is advertising AIActGuard in their own repo, for free.

This is static badge markdown only — there's no verification server behind it (that's a separate, much bigger project: someone could add the badge without actually integrating AIActGuard). Treat it the same way "Built with X" badges work elsewhere: an honor-system signal, not a certification. If that ever needs to become a real verified badge, it'd need a backend that checks the claiming repo actually imports/calls AIActGuard — out of scope for now.

## Markdown snippet (for projects that integrate AIActGuard)

```markdown
[![AIActGuard](https://img.shields.io/badge/EU%20AI%20Act-compliance--checked-blue)](https://github.com/NavikkumarModi/AIActGuard)
```

Renders as a blue "EU AI Act | compliance-checked" badge linking back to this repo.

## Where to surface this

- Add a "Badge" section to the main README once the project has its first few real integrators — showing it on day one with zero adopters looks hollow.
- Mention it in the Show HN / blog post launch copy as something integrators can add (see [show_hn_post.md](show_hn_post.md), [blog_post.md](blog_post.md)).
- Consider a short line in `CONTRIBUTING.md` inviting integrators to add it once they've wired up a real gate/audit trail.
