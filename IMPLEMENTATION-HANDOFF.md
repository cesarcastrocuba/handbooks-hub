# Handbook platform: implementation handoff

## Goal and constraints
Build a reusable, agent-neutral open handbook platform. Start clean in `~/github/handbooks-hub` and `~/github/handbook-sample-01`. Treat `~/github/solutions-architecture-handbook` as read-only reference; defer any migration until a separate owner decision. Work in English. Owner approves editorial gates and releases. Keep Codex usage low: use OpenCode implementers through Herdr, separate reviewer from implementer, narrow tasks, concise evidence, no continuous polling. Never self-review. Preserve attribution/licensing and use conventional commits.

## Architecture
Independent book repositories own canonical Quarto sources and accept community PRs. Hub owns static categorized portal, shared versioned Python toolkit under `tools/`, schemas, common profiles, template, documentation, and agent-neutral editorial instructions. Books install pinned toolkit versions; do not import a parent checkout or copy shared scripts. Hub tools also validate catalog and publication. Book-specific tests stay in book; shared tests in toolkit. Both repos have a full verify command that runs applicable tests and validations; distinguish fast checks from full artifact checks.

## Editorial contract
Use lightweight SDD (`sdd/changes/<id>/` for substantive work and decisions), concise AGENTS.md roles, durable Git/PR evidence, and optional agent adapters/skills. Define book brief and outline, obtain owner approval, write and approve one pilot section, then expand. Standard profile takes lessons from the existing book: When to Use This Chapter, Key Takeaway, Definition, Purpose, What it includes, Why it is needed, Example, Common Pitfall, Decision & Trade-off, checklist and Further Reading as appropriate; allow explicit profiles and exceptions. Preserve proportional readable diagrams and adaptive table widths; explicit cross-references rather than indiscriminate term links.

## Publication
Target HTML, PDF, DOCX, source bundle, manifest and checksums. Build once from approved commit, verify and publish identical artifacts; book Pages serves reading, Releases holds downloads. Hub catalog references approved releases. Default content CC BY-SA 4.0 and code MIT, with notices and third-party rights review. Pin versions and avoid committing generated artifacts.

## Phases
1. Inspect existing handbook read-only, document contracts and decisions; scaffold both repositories, AGENTS, docs and basic CI.
2. Build minimum shared toolkit, standard profile and template with deterministic validators and meaningful tests.
3. Create sample book 'Handbook Authoring and Publishing'; approve brief, outline and pilot before writing remaining chapters.
4. Build catalog and Pages/release publication, verify end to end.
5. Add editorial agent adapters and automate catalog integration; stabilize on clean clones.
6. Evaluate migration of existing handbook separately with owner approval.

## First milestone
Initialize local repositories and create reviewable scaffolds and a concrete phased plan. Delegate separate non-overlapping hub and sample tasks to distinct OpenCode sessions via Herdr. Codex orchestrates and independently reviews; do not merge or release without owner approval. Start with small useful vertical slice, not all features in one batch. The previous conversation contains the fuller design; Engram project `solutions-architecture-handbook` has handoff summary #6795. Verify details against source and record assumptions; this short handoff is not a verbatim copy of the full prior plan.
