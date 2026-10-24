---
name: release
description: Cut a versioned release of Quick Image Search for Anki, end to end - check the AnkiWeb listing, finalize CHANGELOG.md, bump VERSION, tag v<version>, watch GitHub Actions publish the .ankiaddon as a GitHub Release, then upload it to AnkiWeb (add-on 183246496) through the user's browser. Use when asked to release, ship, publish, cut, or tag a new version, or to update the add-on or its description on AnkiWeb.
argument-hint: "[version | patch | minor | major]"
disable-model-invocation: true
---

# Release Quick Image Search for Anki

A release has two destinations, and it isn't done until both have the new
version:

1. **GitHub Release**, driven entirely by a git tag. Pushing `v<version>`
   makes `.github/workflows/build.yml` build the add-on and publish it, with
   the version's `CHANGELOG.md` section as the notes.
2. **AnkiWeb**, where most Anki users get add-ons (id `183246496`). AnkiWeb
   has no upload API, so the `.ankiaddon` goes up through its web form, in
   the user's own logged-in browser.

The `VERSION` file is the single source of truth for the version. `build.py`
writes it into the manifest's `human_version`, and the workflow refuses a tag
that doesn't equal `v` + that version, or that has no `## [<version>]`
changelog section. (Anki itself never compares versions; it offers updates by
upload time. The version is for people: release names, the changelog, and
error reports.)

Two files describe the AnkiWeb listing, so nothing about it is invented at
release time:

- `ankiweb_description.html`: the listing's description, pasted into the form.
- `ankiweb.json`: the add-on id and the other form fields.

## 1. Preflight

Run these checks before changing anything. Releasing from a messy state ships
something other than what's on `main`, so stop and tell the user if a check
fails rather than working around it.

```bash
git fetch --tags origin
git branch --show-current                  # must be main
git status --porcelain                     # must be empty
git rev-list --left-right --count main...origin/main   # must be "0	0"
gh auth status
```

Then gather what you need to pick the version. Versions 1.0.0 and 1.1.0 were
released before tagging started, so until the first tag exists, the last
release is the last commit that changed `VERSION`:

```bash
cat VERSION                                # current version
base="$(git describe --tags --abbrev=0 2>/dev/null || git log -1 --format=%H -- VERSION)"
echo "$base"
git log --oneline "$base"..HEAD
```

If there are no commits since `base`, there is nothing to release; say so and
stop.

Read the `## [Unreleased]` section of `CHANGELOG.md`. It should already
describe the changes in those commits. If it's empty or misses something
user-visible, draft the missing entries from the commits now; you'll show
them to the user with the version in the next step.

Also check for open pull requests (`gh pr list`). If one is waiting that the
user might want in this release, mention it; don't merge it on your own.

## 2. Check the AnkiWeb listing

The listing makes claims that drift as the code changes, and fixing them now
means the fixes ride along in the release commit instead of needing a
follow-up. Read `ankiweb_description.html` and `ankiweb.json` and check them
against the code being released:

- **Features:** the features listed match what `__init__.py` does (the
  toolbar button, the field fallback, the Google domains in `ConfigDialog`,
  the keyboard shortcut).
- **Config:** the settings described match `config.json`, with the same
  defaults. `README.md`'s configuration table should agree too.
- **Minimum Anki:** `min_anki_version` matches `min_point_version` in
  `build.py` (`50` is `2.1.50`; newer values are `YYMMPP`, so `231000` is
  `23.10`).
- **Tested Anki:** `max_anki_version_tested` is the newest Anki this release
  was tested on. The user's installed version is in the folder name of
  `~/Library/Application Support/AnkiProgramFiles/.venv/lib/python3.*/site-packages/aqt-*.dist-info`;
  AnkiWeb writes `25.9.4` as `25.09.4`. Only raise it if the user has run
  this release on that version.
- **Encoding:** the description must stay ASCII (use `&rarr;`, `&mdash;`
  and similar entities), because a non-ASCII arrow was once garbled into
  `â†’` on AnkiWeb. Check with `LC_ALL=C grep -n '[^ -~]' ankiweb_description.html`,
  which prints nothing when the file is clean.
- **Title:** under 80 characters, ASCII.

Collect any corrections; you'll show them with the version and apply them in
step 5.

## 3. Choose the version

The argument may be an explicit version (`1.2.0`, `1.2.0-beta.1`), a bump
keyword (`patch`, `minor`, `major`), or absent.

- **Keyword:** apply it to the current `VERSION`.
- **Absent:** propose a version from the commits since `base`, using semver
  as it applies to this add-on's users:
  - **major** — something a user must act on: a config key that no longer
    works, a removed feature, or a raised minimum Anki version.
  - **minor** — new capability: a new feature, config option or search
    provider.
  - **patch** — fixes, listing and docs changes, CI, internal refactors.

The current `VERSION` has normally already been released, so the new version
must be higher than it. It must also be valid semver and its tag must not
exist yet (`git tag -l v<version>` and `git ls-remote --tags origin v<version>`
both empty). A hyphenated version like `1.2.0-beta.1` is published as a
prerelease on GitHub. AnkiWeb has no prereleases, so skip the AnkiWeb step
for those and say so.

**Confirm with the user before going further**, unless they gave an explicit
version in this request and neither the changelog nor the listing needed
changes. Show the proposed version and why, the commits it covers, the
release notes (including any entries you drafted), and any listing
corrections. Pushing a tag publishes a release that anyone can see.

## 4. Local sanity check

CI builds everything anyway, but catching a broken build before tagging
avoids a failed run and a dangling tag:

```bash
python3 -m py_compile __init__.py
python3 build.py
```

## 5. Update the changelog and listing

Edit `CHANGELOG.md` in Keep a Changelog style:

- Rename `## [Unreleased]` to `## [<version>] - <YYYY-MM-DD>` (today's
  date), and put a new, empty `## [Unreleased]` above it. Keep the brackets:
  the workflow finds the release notes by them.
- Write entries for users, not as a commit log. Use the standard groups:
  Added, Changed, Deprecated, Removed, Fixed, Security. Leave out changes
  users can't notice, such as CI, refactors, and maintainer docs.
- Update the link references at the bottom:
  `[Unreleased]: https://github.com/bappelt/anki-quick-image-search/compare/v<version>...HEAD`,
  and add one for the new version. If the previous version has a tag, use
  `[<version>]: https://github.com/bappelt/anki-quick-image-search/compare/v<previous>...v<version>`;
  if it doesn't (the first tagged release, after the untagged 1.1.0), use
  `[<version>]: https://github.com/bappelt/anki-quick-image-search/releases/tag/v<version>`.

Apply the listing corrections from step 2 to `ankiweb_description.html` and
`ankiweb.json`.

## 6. Bump, commit, tag, push

```bash
printf '%s\n' "<version>" > VERSION
git add VERSION CHANGELOG.md ankiweb_description.html ankiweb.json
git commit -m "Release v<version>"     # plus any attribution trailer this session requires
git tag -a v<version> -m "v<version>"
git push origin main
git push origin v<version>
```

Push `main` before the tag so the tagged commit is on `main`. If `main` is
protected and the push is rejected, stop and ask the user how they want to
land the release commit (for example a PR, then tag the merged commit).

## 7. Watch the workflow

The tag push starts a run whose branch is the tag name:

```bash
run_id=$(gh run list --workflow build.yml --branch v<version> --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$run_id" --exit-status
```

The run may take a few seconds to appear after the push; retry the
`gh run list` briefly if it comes back empty.

## 8. Verify the GitHub Release

```bash
gh release view v<version> --json url,isPrerelease,assets,body --jq '{url, isPrerelease, assets: [.assets[].name], body}'
```

It should list exactly one asset, `quick_image_search-<version>.ankiaddon`,
and its notes should match the changelog section (and nothing from older
sections).

## 9. Publish to AnkiWeb

Upload the exact file from the GitHub Release, not a local rebuild, so
AnkiWeb and GitHub serve the same build:

```bash
rm -rf dist/ankiweb && gh release download v<version> -p '*.ankiaddon' -D dist/ankiweb
```

Always use the update page for the existing listing,
`https://ankiweb.net/shared/upload?id=183246496` (the `addon_id` in
`ankiweb.json`). The plain `https://ankiweb.net/shared/upload` page would
create a second, duplicate listing.

The same form also handles a description-only update between releases: Save
works with no file attached, and changes just the listing.

### With the Claude in Chrome browser tools

Use these when they're available; load the claude-in-chrome skill first.

1. Open the page in a new tab. If AnkiWeb shows a login page instead of the
   form, stop and ask the user to log in themselves; never type their
   credentials.
2. Fill the form from `ankiweb.json`. The form's fields, top to bottom:
   - **Title**, **Tags**, **Support Page**: text boxes, pre-filled from the
     live listing. Check them against `ankiweb.json` and correct any that
     differ.
   - **Branches**: Branch 1 has two version boxes: the first should be
     `min_anki_version` and the second `max_anki_version_tested`. Don't
     prefix the maximum with `-`; that would block the add-on on newer Anki
     versions rather than marking what it was tested on.
   - **Upload file**: choose Branch 1 in the dropdown, then attach
     `dist/ankiweb/quick_image_search-<version>.ankiaddon` to the file input
     with the file upload tool.
   - **Description**: replace the whole text box with the contents of
     `ankiweb_description.html`. Set it through JavaScript rather than by
     typing: call the native value setter
     (`Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(textarea, text)`),
     then dispatch `input` and `change` events so the page's framework
     notices the change. Do the same for any text box you correct. Read the
     value back afterwards and compare it with the file.
3. **Don't click Save yet.** Take a screenshot and show the user the filled
   form: title, tags, support page, branch versions, the attached file name,
   and that the description is the current listing. Ask for an explicit
   go-ahead. Saving publishes the add-on to every AnkiWeb user, so this is
   the user's call even though they started the release.
4. On a yes, click **Save** by its element reference (get it with `find`),
   not by screen coordinates: the page scrolls after the description box is
   focused, so a coordinate taken from an earlier screenshot can miss.
   AnkiWeb then shows the add-on's info page.
5. Verify on the info page, `https://ankiweb.net/shared/info/183246496`,
   not on the form (the form only shows what you typed): "Updated" shows
   today's date, "Supported Anki versions" shows the branch range, and the
   description renders with arrows and dashes, not `â†’`. If something is
   wrong, tell the user and go back through the update page; don't remove
   the add-on.
6. Close the tab.

### Without browser tools

Give the user a checklist instead: the page to open, every field value from
`ankiweb.json`, the file path in `dist/ankiweb/`, and a reminder to paste in
`ankiweb_description.html` as the description. Ask them to confirm on the
info page afterwards.

## 10. Report

Report the GitHub Release URL, the AnkiWeb info page URL, the version,
whether it's a prerelease, and the asset name.

Remind the user that users who installed from AnkiWeb get the update through
Tools &rarr; Add-ons &rarr; Check for Updates. A copy installed from a
`.ankiaddon` file is a separate add-on to Anki (it lives in
`addons21/quick_image_search/` rather than `addons21/183246496/`), so nobody
should keep both enabled: each copy adds its own Search Images button and
registers the same keyboard shortcut.

## If the workflow fails

No release is created when the build job fails, but the tag and the version
commit are already pushed. Show the user the failing step's log
(`gh run view <run_id> --log-failed`) and explain the cause. Don't upload
anything to AnkiWeb.

Don't delete or move the tag on your own: deleting a pushed tag is
destructive, and someone may already have fetched it. Offer the options and
let the user choose:

- **Fix forward (usually best):** fix the problem, then release the next
  patch version.
- **Retag:** delete the tag (`git push --delete origin v<version>` and
  `git tag -d v<version>`), fix, then tag the fixed commit with the same
  version. Only sensible if nobody could have used the failed tag.

## If the AnkiWeb upload fails

The GitHub Release is already out and stays valid; only AnkiWeb is behind.
Tell the user what AnkiWeb said, and retry from step 9 once it's fixed. A
rejected upload changes nothing on AnkiWeb, so retrying is safe.
