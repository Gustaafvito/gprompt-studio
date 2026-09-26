# Download section for gustaafvito.com — English version

The Spanish version is in [`WEB-descarga.md`](WEB-descarga.md). Same blocks,
same order, same warning-before-the-button rule.

**Why English matters more here than on the rest of the site:** the audience
for this tool is mostly English-speaking — the `#use-cases` forum on
OpenAI's Discord, r/StableDiffusion, the ComfyUI Discords. That's where the
announcement lands. Those visitors click through to GitHub (already in
English) and then to the site. A Spanish-only page loses exactly the person
who arrived interested.

Your social brand stays Spanish. It's **this page** that needs English, not
the whole site. A `hreflang` pair or a simple ES/EN toggle on the tool page
is enough.

**Already live** since 18 Sep 2026 at `gustaafvito-web/gprompt-studio.html`.
This file is the source of the copy: change something here and carry it over
to that page, and the other way round. It sat written but unpublished for
nine days, which is the silliest way to waste the work.

---

## Block 1 — Download

> ### Download G-Prompt Studio
>
> Windows 10 or 11 (64-bit). No Python, no dependencies.
>
> **[⬇ Download the installer (188 MB)]**
> ← link to the GitHub release asset
>
> Would rather not install anything? [Single-file portable build (187 MB)]
>
> To get started you only need a **free API key** from
> [Gemini](https://aistudio.google.com/apikey) or
> [Groq](https://console.groq.com/keys). Both are free, no card required, and
> either one runs the whole app.

---

## Block 2 — The Windows warning

Put this right under the button, visible without expanding anything.

> ### ⚠️ Windows will show a warning when you open it
>
> You'll see a blue screen saying **"Windows protected your PC"**. This is
> expected.
>
> **To open it:** click *More info*, then *Run anyway*.
>
> **Why it happens.** Windows warns about any program that isn't signed with
> a code-signing certificate. Those cost around €300 a year, and Microsoft
> only sells them to companies in the US and Canada or with three years of
> verifiable history. G-Prompt Studio is a one-person project.
>
> The warning **does not say the program is dangerous**. It says Windows
> doesn't know who signed it. It's the same screen you get with almost any
> independent tool.
>
> **You don't have to take my word for it.** Every download publishes its
> SHA-256 fingerprint on
> [the release page](https://github.com/Gustaafvito/gprompt-studio/releases).
> Check it matches the file you downloaded and you know it's exactly what I
> published, untampered:
>
> ```powershell
> Get-FileHash .\GPromptStudio-Setup-1.1.0.exe -Algorithm SHA256
> ```
>
> ```
> 4104cb2257165e4c4819e1ee4e3be8970f98b712ca270b684889fd6e2f4e3aba  GPromptStudio-Setup-1.1.0.exe
> 0ae8f89a69b83f069c689325ef74d250b81a0f39e4fe7a9dcaf215da49d4622b  GPromptStudio-Portable-Onefile.exe
> ```
>
> And if you like reading code, all of it is
> [on GitHub](https://github.com/Gustaafvito/gprompt-studio) under the
> Apache 2.0 licence.

---

## Block 3 — VirusTotal

> **Scanned on VirusTotal — here's the whole result**
>
> - **Installer:** [0 of 67 engines](https://www.virustotal.com/gui/file/4104cb2257165e4c4819e1ee4e3be8970f98b712ca270b684889fd6e2f4e3aba) — clean
> - **Single-file portable:** [2 of 68](https://www.virustotal.com/gui/file/0ae8f89a69b83f069c689325ef74d250b81a0f39e4fe7a9dcaf215da49d4622b) — Bkav Pro and Zillya
>
> **Microsoft Defender flags neither of them.**
>
> **Neither detection finds malicious code**, which matters more than the
> count. Bkav Pro gives a label derived from the file itself
> (`W32.Malware.C1C732E6`); and Zillya names XWorm, a real piece of malware
> that is also packaged with PyInstaller, the tool this program is built
> with.
>
> What antivirus engines score is the **packaging**, not the program. The
> proof is inside 1.1.0 itself: the installer carries the very same program
> and nobody flags it. Same software, different wrapper, different verdict.
>
> **If your antivirus complains about one option, try the other** — it's the
> same program. And check the hash either way.

---

## Block 4 — Questions and support

> ### Questions, or something not working?
>
> - **Bugs:** [open an issue on
>   GitHub](https://github.com/Gustaafvito/gprompt-studio/issues) and attach
>   the log from `%USERPROFILE%\.arquitecto_prompts\logs\gprompt.log`
> - **Questions and ideas:**
>   [Discussions](https://github.com/Gustaafvito/gprompt-studio/discussions)
> - **Follow along:**
>   [Instagram](https://www.instagram.com/gustaafvito.creador.ia) ·
>   [TikTok](https://www.tiktok.com/@gustaafvito.creador.ia) ·
>   [YouTube](https://www.youtube.com/@GustaafvitocreadorIA)
>
> The app's interface is bilingual Spanish/English and follows your Windows
> language.

Note for you: the social links go to Spanish-language accounts. Say so, or
English-speaking visitors will follow them and bounce. Something like
*"(content in Spanish)"* after them is enough and saves the surprise.

---

<!--
## Reminders

- **Hashes change with every build.** Regenerate the `.exe` and you must
  update both language versions of the page and the release.
  `build_release.py` prints them and warns when the release text is stale.
- **Point the buttons at the GitHub release assets.** Don't host 285 MB
  yourself — GitHub serves them free, with no bandwidth cap.
- Keep both languages in sync. Two download pages that disagree on the size,
  the hash or the VirusTotal result are worse than one.
-->
