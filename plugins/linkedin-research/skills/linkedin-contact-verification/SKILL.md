---
name: "linkedin-contact-verification"
description: "Check whether a list of contacts still work where your records say, in the role your records say, using the Experience section on LinkedIn through the LinkedIn MCP server — and report each as still there, still there with a new title, left (and where they went), not found or ambiguous, or not checked. Use before outreach to old leads, before a renewal or collections push, after importing a list, or when the user asks \"are these contacts still there\", \"verify these leads\", \"who has left\", \"check titles on LinkedIn\", \"clean this contact list\", \"did [name] leave [company]\". Read-only; never infers employment from other sources."
---

# LinkedIn contact verification

Old contact lists decay fast — in one real check, 4 of 8 contacts on an imported lead list had left their companies.
This skill verifies each contact against LinkedIn before anyone emails them or writes their title into a system.
**Read `${CLAUDE_PLUGIN_ROOT}/references/guardrails.md` first.**

## Inputs

A list with, per contact: name, company, and if available the title on record and a LinkedIn URL. Shared distribution
lists and role mailboxes (accounts payable, billing@, info@) are not people — list them separately as "not a person" and
skip them.

## Rules that matter most

- **Experience decides.** Employment is verified only from the person's LinkedIn Experience section
  (`get_person_profile`, `sections="experience"`): the current role is the one ending "Present".
- **If LinkedIn can't be checked** (tools not connected, login needed, profile private): mark the contact "not
  checked" with the reason. **Never infer employment from email bounces, websites or other data** and report it as
  verified.
- **Volume:** up to 25 lookups per run by default; above that, say how many and ask. One call at a time.
- Never update anyone's records yourself unless the user asks and has a tool for it; this skill reports.

## Steps

1. For each contact, in order:
   - Have a LinkedIn URL? `get_person_profile` with `sections="experience"`.
   - Otherwise `search_people` with "name company" (use the company's numeric id in `current_company` when available; add
     `location` for common names), then read the best match's Experience.
2. Classify:
   - **Still there — title matches**
   - **Still there — title changed** (give the new title and when it changed)
   - **Left** — the role at the company has an end date; give the end month and the new employer and title if shown
   - **Not found / ambiguous** — no confident match, or two candidates (show both)
   - **Not checked** — with the reason
3. Note anything the user should fix in their records: misspelled names, wrong titles, a better LinkedIn URL.

## Output

A table: contact · company on record · title on record · status · current company and title (from LinkedIn) · since ·
profile URL · read date. Then a summary: how many are still there, changed, left, unresolved — and which contacts are
safe to contact now. Departed contacts at a target company are a lead in themselves: suggest checking who replaced them
(`linkedin-company-signals`) and, where the person moved to another relevant company, a new opportunity.
