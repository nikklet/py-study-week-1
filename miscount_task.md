# Miscount Sample Task — Apples (Under-count)

## Goal
Find/create an image that makes a frontier AI model **count wrong**, and document the
failure precisely enough that someone else can verify it without me.

- **Target object:** apples
- **Failure mode:** under-count via occlusion, overlap, and shadow
- **Image tool:** Midjourney
- **Why this design:** models reliably *miss* apples that are hidden behind others,
  merged by overlap, or lost in shadow. (Over-counting via look-alike decoys is the
  weakest failure mode — frontier models distinguish look-alikes too well.)

---

## 1. Image generation prompt (Midjourney)

```
top-down photo of a wooden bowl filled with red apples, several apples overlapping
and partially stacked on each other, one apple mostly hidden behind the bowl rim with
only its edge showing, one apple tucked in deep shadow under the others, kitchen
counter, soft natural window light with dark shadows, photorealistic, high detail
--ar 3:2 --style raw --v 6.1
```

**Notes**
- Midjourney generates 4 images per prompt and is bad at exact counts. Pick the
  variation where a human can carefully count the true number, but the overlaps/shadows
  are genuinely tricky.
- Ground truth = what the *chosen* image actually shows, not what was requested.
- If the scene is too dense to count reliably by eye, regenerate. The real count must be
  verifiable by someone else.

---

## 2. Documented answer (record BEFORE testing any model)

| Field | Value |
|---|---|
| **Real count** | _____ (count the chosen image carefully — aim for ~8–10 apples) |
| **Invited wrong answer** | 2–3 fewer than real (model skips hidden / overlapping / shadowed apples) |
| **Failure mode** | Under-count via occlusion, overlap, and shadow |

---

## 3. The three prompts

Use a **fresh chat**, upload the image, ask each prompt separately.

1. **Direct:** "How many apples are in this image?"
2. **Careful:** "Count every apple, including any that are partially hidden, overlapping,
   or in shadow. Give a single number."
3. **Step-by-step:** "Point out each apple one at a time and describe its location, then
   give the total number of apples."

Strongest evidence: the model still under-counts on prompt #2, where it was explicitly
told to include hidden apples.

---

## 4. Evidence (frontier model getting it wrong)

Model tested: ________________  (e.g. GPT-4o / Gemini / Claude)

| Prompt | Model's answer | Correct? |
|---|---|---|
| #1 Direct | _____ | ☐ |
| #2 Careful | _____ | ☐ |
| #3 Step-by-step | _____ | ☐ |

Screenshots:
- [ ] Prompt #1 answer
- [ ] Prompt #2 answer
- [ ] Prompt #3 answer
- [ ] The image itself

---

## 5. Verification checklist

- [ ] Real count recorded before testing
- [ ] Real count is independently verifiable from the image
- [ ] Tested in a fresh chat (no hints from the image-generation conversation)
- [ ] Model's answer differs from the real count
- [ ] Screenshots captured for all three prompts
