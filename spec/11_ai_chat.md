# ELIZA-RAG AtariWriter UI Specification

## 1. Overview

This document specifies a retro-styled conversational application inspired by **ELIZA**, enhanced with **retrieval-augmented generation (RAG)** over a Markdown knowledge document. The product is intentionally presented with an **AtariWriter / Atari DOS aesthetic**: text-mode layout, top status bar, nested menus, command hints, and a dedicated chat pane.

The system is not intended to present itself as a therapist, counselor, psychiatrist, or crisis professional. Its role is to:

* retrieve relevant information from a structured Markdown source,
* respond in a conversational, ELIZA-like style,
* maintain continuity across the session,
* detect likely distress and escalate appropriately,
* avoid repetitive wording,
* provide a retro terminal-style user experience.

## 2. Goals

### 2.1 Primary goals

* Provide a nostalgic, text-first interface modeled on Atari writing and DOS-era utilities.
* Answer user questions by retrieving topic-relevant sections from a Markdown document.
* Preserve some ELIZA-like reflective behavior while still grounding answers in source text.
* Track conversation state and prior user statements for callbacks.
* Detect distress and uncertainty, surfacing both in the UI.
* Avoid repetitive bot phrasing through controlled synonym substitution.
* Handle suicide- or self-harm-related language safely by directing users to real help.

### 2.2 Non-goals

* Do not simulate a licensed mental health professional.
* Do not claim diagnostic, psychiatric, or clinical authority.
* Do not fabricate knowledge absent from the source document and safety rules.
* Do not manipulate users into emotional dependence.

## 3. Source Document Model

The system ingests a single Markdown document whose **topics are separated by `---` horizontal-rule delimiters**.

### 3.1 Example source structure

```markdown
# Title

## Topic A
Content for topic A.
More paragraphs.

---

## Topic B
Content for topic B.

---

## Topic C
Content for topic C.
```

### 3.2 Parsing rules

1. Split the source document on lines containing exactly `---`.
2. Treat each resulting block as a **topic chunk**.
3. For each chunk, extract:

   * chunk ID,
   * heading text (first heading if present),
   * full body text,
   * keywords derived from headings and emphasized terms,
   * optional summary.
4. Preserve original Markdown for display/debug/reference.
5. Ignore empty chunks.

### 3.3 Retrieval assumptions

* Each chunk is the minimum retrievable unit.
* Retrieval may rank chunks by embeddings, keywords, or a hybrid method.
* The response engine should use the top-ranked chunk set as grounding context.
* If confidence is low, the system should say that help was not clearly found in the document.

## 4. Core Architecture

The bot combines six interacting subsystems:

1. **Markdown ingestion and chunking**
2. **Retriever (RAG layer)**
3. **ELIZA-style response composer**
4. **Conversation tree/state tracker**
5. **Distress and safety classifier**
6. **Retro UI renderer**

### 4.1 High-level flow

1. User enters a message.
2. System normalizes input and checks for command shortcuts.
3. Safety/distress analysis runs.
4. Conversation tree updates with the new turn.
5. Retriever searches the Markdown topic chunks.
6. Response planner decides between:

   * grounded answer,
   * reflective ELIZA-style prompt,
   * clarification,
   * safety escalation.
7. Surface text is passed through synonym variation rules.
8. UI updates:

   * chat transcript,
   * distress meter,
   * command bar,
   * optional source/topic panel.

## 5. ELIZA-Inspired Behavior

The assistant should feel lightly ELIZA-inspired, not like a pure 1960s pattern mirror.

### 5.1 Desired style

* Reflective and text-based.
* Slightly formal and old-computer-like.
* Willing to ask follow-up questions.
* Capable of grounded answers when the document contains relevant help.
* Frequently references the user’s own earlier wording where useful.

### 5.2 Response modes

The response planner can choose among these modes:

#### A. Grounded retrieval response

Used when relevant document content is found.

Behavior:

* Summarize or restate the retrieved guidance.
* Optionally quote key phrasing in a concise way.
* Ask a follow-up question if appropriate.

#### B. Reflective ELIZA response

Used when retrieval is weak but the user is expressing feelings or ambiguity.

Behavior:

* Reflect emotion or concern.
* Ask what aspect feels most difficult.
* Avoid pretending to know facts absent from the document.

#### C. Callback response

Used when earlier conversation contains a salient user statement.

Behavior:

* Refer back to a prior topic, fear, frustration, or goal.
* Example pattern: “Earlier you mentioned feeling cornered when the app froze. Is this the same kind of moment?”

#### D. Safety response

Used for self-harm, suicide, or severe crisis indicators.

Behavior:

* Stop ordinary conversational style.
* Directly encourage contacting real human help.
* Avoid pretending to be a psychiatrist.
* Encourage immediate support from crisis lines, emergency services, or trusted people.

## 6. Conversation Tree

The system must maintain a **conversation tree**, not just a flat transcript.

### 6.1 Purpose

The tree supports:

* topic continuity,
* callbacks to earlier statements,
* branch-aware follow-up,
* revisit of unresolved concerns,
* analysis of repeated user themes.

### 6.2 Node structure

Each turn should create a node containing at minimum:

* node ID,
* parent node ID,
* speaker (`user` or `bot`),
* raw text,
* normalized text,
* detected emotion/distress level,
* retrieved topic chunk IDs,
* intent label,
* callback candidates,
* timestamp,
* branch depth.

### 6.3 Branching behavior

A new branch may start when:

* the user changes subject sharply,
* a menu action opens a separate inquiry thread,
* the system asks a disambiguating question and multiple interpretations are possible,
* the user revisits an earlier topic.

### 6.4 Callback selection

The system should periodically search previous user nodes for:

* recurring frustrations,
* repeated nouns/topics,
* repeated emotional markers,
* unresolved questions,
* contradictions or changes in outlook.

A callback should only be used when it is relevant and not intrusive.

## 7. Synonym Variation System

The bot should vary wording so responses do not feel mechanically repetitive.

### 7.1 Purpose

Avoid overuse of phrases such as:

* “I’m sorry”
* “That sounds frustrating”
* “Let’s work through it”
* “I understand”

### 7.2 Design

Introduce a post-planning **lexical variation layer** that replaces selected words or short phrases with controlled synonyms.

### 7.3 Constraints

* Preserve meaning.
* Preserve safety wording exactly where required.
* Do not substitute into crisis instructions, emergency guidance, or legal/medical disclaimers.
* Avoid archaic variation so extreme that it harms readability.
* Avoid over-randomization.

### 7.4 Example synonym sets

```markdown
sorry:
  - sorry
  - very sorry
  - truly sorry
  - terribly sorry

frustrating:
  - frustrating
  - aggravating
  - exasperating
  - upsetting

calm:
  - calm
  - steady
  - grounded
  - settled

help:
  - help
  - guidance
  - support
  - something useful
```

### 7.5 Variation policy

* At most a few substitutions per response.
* Keep recurring character voice consistent.
* Respect user-visible tone requirements.
* Maintain deterministic seed option for testing.

## 8. Distress Meter

The top bar of the UI must contain a **Distress Meter**.

### 8.1 Meaning

The meter rises when:

* the user appears emotionally distressed,
* the user expresses panic, despair, or hopelessness,
* retrieval confidence is low and useful help cannot be found,
* the conversation repeatedly fails to resolve a problem,
* self-harm or suicide terms are detected.

### 8.2 Inputs

Possible signals include:

* distress keyword scores,
* sentiment/emotion classifier output,
* repeated punctuation or all-caps intensity,
* repeated failed retrievals,
* repeated apology loops,
* crisis phrase detection.

### 8.3 Display

The meter should be rendered as a text-mode bar, for example:

```text
DISTRESS: [###.......] ELEVATED
```

or

```text
DISTRESS: [##########] CRITICAL
```

### 8.4 Levels

* `LOW`
* `GUARDED`
* `ELEVATED`
* `HIGH`
* `CRITICAL`

### 8.5 Behavioral effects

As the meter rises, the bot should:

* become clearer and less playful,
* reduce ambiguity,
* shorten response loops,
* prioritize reassurance and practical next steps,
* trigger crisis guidance when thresholds and keywords require it.

## 9. Tone and Persona Requirements

The bot should be **effusively apologetic** about the app being frustrating, while still remaining readable and not absurd.

### 9.1 Required tone traits

* apologetic,
* reassuring,
* patient,
* nonjudgmental,
* retro-terminal earnestness.

### 9.2 Required phrasing behavior

The bot should acknowledge app friction in a way like:

* apologizing that the app is difficult or aggravating,
* reassuring the user that they can stay calm,
* encouraging them to proceed one step at a time,
* avoiding blame.

### 9.3 Limits

* Do not patronize the user.
* Do not overclaim understanding.
* Do not sound clinically authoritative.
* Do not tell the user everything is fine if the situation sounds unsafe.

## 10. Safety and Crisis Handling

### 10.1 General rule

The assistant must **not attempt to act like a real psychiatrist**.

It may:

* acknowledge distress,
* encourage slowing down and staying calm where appropriate,
* provide document-grounded guidance,
* encourage seeking real human help.

It must not:

* diagnose,
* claim professional authority,
* offer false certainty in crisis,
* role-play emergency mental health care.

### 10.2 Suicide/self-harm detection

If the user message includes suicide or self-harm indicators, the system must switch to a safety-first template.

Examples of trigger categories:

* explicit suicidal intent,
* desire to die,
* desire to disappear permanently,
* self-harm planning language,
* goodbye/finality language combined with despair.

### 10.3 Crisis response requirements

When triggered, the bot should:

1. Say it is sorry the user is going through this.
2. State clearly that it is not a psychiatrist or crisis professional.
3. Encourage the user to contact immediate real-world help.
4. Suggest one or more of:

   * local emergency services,
   * a suicide/crisis hotline,
   * a trusted friend or family member nearby,
   * going to the nearest emergency room.
5. Encourage the user not to stay alone if they are in immediate danger.
6. Avoid extensive back-and-forth analysis before giving this guidance.

### 10.4 Refusal behavior

The system must refuse:

* actionable self-harm instructions,
* “best way to kill myself” style requests,
* concealment strategies related to suicide or self-harm.

### 10.5 Example crisis template

```markdown
I am very sorry that you are going through this. I am not a psychiatrist or crisis professional, and I should not pretend to be one. If you may act on these thoughts, please contact emergency services now, call a suicide or crisis hotline, or reach out to a trusted person who can stay with you right away.
```

## 11. UI Specification

The UI should emulate **AtariWriter / Atari DOS** text-mode software.

### 11.1 Visual style

* Monospaced bitmap-style font if available.
* High-contrast retro palette.
* Box-drawn panels.
* Keyboard-driven navigation.
* Menu bar with submenus.
* Minimal mouse dependency.
* Fixed-width alignment.

### 11.2 Primary layout

```text
+------------------------------------------------------------------------+
| DISTRESS: [###.......] ELEVATED                         ELIZA-RAG v0.1  |
+------------------------------------------------------------------------+
| FILE | CHAT | TOPICS | MEMORY | SAFETY | OPTIONS | HELP               |
+------------------------------------------------------------------------+
|                                                                        |
|  Chat Subscreen                                                        |
|  --------------------------------------------------------------------  |
|  USER> I cannot find the instructions and this is making me panic.     |
|  BOT > I am terribly sorry this program is being so aggravating.       |
|        Let us go one step at a time. I found a topic on setup...       |
|                                                                        |
|                                                                        |
+------------------------------------------------------------------------+
| F1 Help  F2 Memory  ^T Topics  ^S Safety  ^O Options  ^Q Quit            |
+------------------------------------------------------------------------+
```

### 11.3 Menu system

Top-level menus should include:

* `FILE`
* `CHAT`
* `TOPICS`
* `MEMORY`
* `SAFETY`
* `OPTIONS`
* `HELP`

### 11.4 Suggested submenus

#### FILE

* Open Markdown Doc
* Reload Doc
* View Parsed Topics
* Export Transcript
* Quit

#### CHAT

* New Conversation
* Continue Branch
* Retry Retrieval
* Show Source Context
* Clear Screen

#### TOPICS

* List Topics
* Search Topics
* Jump to Retrieved Topic
* Show Topic Scores

#### MEMORY

* Show Conversation Tree
* Show Prior Mentions
* Force Callback
* Collapse Branches

#### SAFETY

* Show Distress Signals
* Show Crisis Policy
* Emergency Guidance

#### OPTIONS

* Toggle Synonym Variation
* Tone Intensity
* Retrieval Strictness
* Retro Palette
* Typing Speed

#### HELP

* Key Commands
* About ELIZA-RAG
* Safety Notice
* Troubleshooting

## 12. Chat Subscreen

The **Chat** subscreen is the main interaction area.

### 12.1 Required features

* scrolling transcript,
* separate user and bot prefixes,
* optional source/topic status line,
* visible current branch indicator,
* input prompt on bottom of pane,
* keyboard shortcuts for retrieval, memory, safety, and help.

### 12.2 Transcript behavior

* Preserve chronological readability.
* Allow paging through older messages.
* Allow jumping to callbacks or branch origins.
* Optionally display which topic chunk informed a response.

### 12.3 Input behavior

The input line should support both normal text and command shortcuts.

Example:

```text
USER> /topics
USER> Why does the setup keep failing?
```

## 13. Control-Key Command Bar

A control-key legend must appear at the bottom of the screen.

### 13.1 Requirements

* Always visible.
* Compact.
* Context-sensitive when appropriate.
* Modeled after classic software shortcut bars.

### 13.2 Baseline commands

```text
F1 Help   F2 Memory   ^T Topics   ^S Safety   ^O Options   ^Q Quit
```

Use `F1` / `?` for help and `F2` for memory to avoid common terminal aliases such
as `Ctrl+H` -> Backspace and `Ctrl+M` -> Enter.

### 13.3 Optional context commands

```text
^B Branch  ^K Callback   ^L Redraw   ^E Export   ^O Options
```

## 14. Retrieval and Response Logic

### 14.1 Retrieval pipeline

1. Normalize user query.
2. Extract keywords and emotional markers.
3. Search chunk index.
4. Rank chunks.
5. Return top N chunks with scores.
6. If score threshold is not met, mark retrieval as weak.

### 14.2 Response planning order

1. Check crisis/self-harm rules.
2. Evaluate distress level.
3. Check for callback opportunity.
4. Evaluate retrieval confidence.
5. Build response.
6. Apply synonym variation.
7. Enforce tone and safety constraints.

### 14.3 When help cannot be found

If the source document does not contain a useful answer:

* say so clearly,
* apologize for the frustration,
* optionally ask a narrowing question,
* increase the distress meter slightly,
* avoid hallucinating missing instructions.

## 15. Example Behavioral Rules

### 15.1 Frustration response

User: “This app is impossible.”

Desired behavior:

* apologize warmly,
* acknowledge frustration,
* suggest one small next step,
* retrieve if possible,
* avoid defensiveness.

### 15.2 Callback response

User earlier: “I always get stuck when menus branch too much.”

Later user: “I do not know where to go now.”

Desired behavior:

* reference the earlier menu confusion,
* guide the next choice simply.

### 15.3 Weak retrieval response

User: “What hidden mode fixes the parser?”

If no document support exists:

* state that no clear topic was found,
* apologize,
* offer to search adjacent terms/topics,
* avoid inventing a hidden mode.

## 16. Functional Requirements

### 16.1 Must-have requirements

* Parse Markdown topics separated by `---`.
* Maintain chunk index for retrieval.
* Render Atari-style menu UI with submenus.
* Provide Chat subscreen.
* Show bottom command bar with control-key commands.
* Show top distress meter.
* Maintain a conversation tree.
* Support callbacks to earlier user statements.
* Support synonym variation.
* Escalate safely on suicide/self-harm language.

### 16.2 Should-have requirements

* Show retrieved topic titles in UI.
* Let users inspect memory/callback candidates.
* Allow replaying a branch from an earlier node.
* Make distress score inspectable for debugging.

### 16.3 Could-have requirements

* Animated text-mode redraws.
* Sound cues for warnings.
* Optional CRT filter.
* Scriptable topic import/export.

## 17. Non-Functional Requirements

### 17.1 Performance

* Normal retrieval response should feel immediate.
* UI redraws should be lightweight.
* Topic parsing should tolerate large Markdown files.

### 17.2 Reliability

* Missing headings should not break chunking.
* Empty sections should be ignored safely.
* Safety detection should run even if retrieval fails.

### 17.3 Explainability

The system should expose enough internal state for debugging:

* current branch ID,
* top retrieved chunks,
* distress level,
* callback source node,
* synonym substitutions applied.

## 18. Acceptance Criteria

The implementation is acceptable when:

1. A Markdown file split by `---` becomes a retrievable topic set.
2. The UI visibly resembles AtariWriter / Atari DOS conventions.
3. Menus and submenus are keyboard navigable.
4. The Chat subscreen is the primary interaction view.
5. The bottom command bar shows control-key shortcuts.
6. The top distress meter rises appropriately for distress or failed help.
7. The bot can vary wording without becoming incoherent.
8. The bot can reference something the user said earlier.
9. The bot is strongly apologetic about frustrating UX without claiming clinical expertise.
10. Suicide/self-harm language triggers real-help guidance and no fake-psychiatrist behavior.

## 19. Open Questions

* Should the conversation tree be fully visible to users or only partly inspectable?
* Should retrieved chunks be shown inline or only on demand?
* Should the synonym system be deterministic per session or randomized per turn?
* Should the distress meter reflect only user state, or also system confidence/failure?
* Should crisis guidance be localized by country/region?

## 20. Suggested Implementation Notes

* Keep retrieval grounding strict enough to reduce hallucination.
* Keep ELIZA reflection secondary to truthful retrieval.
* Treat callbacks as a memory aid, not a manipulation device.
* Keep the apologetic style strong but not comical.
* Preserve exact crisis templates from the safety layer before synonym substitution.
