---
name: adopt
description: Put ACR in use in this project without starting a review. Use only when the person types this command. A request in their own words to review something is handled by the review skill.
---

# Adopt

What they typed with the command, if anything: $ARGUMENTS

The person typed this command. The host records the adoption itself, as the person's own act, from what they typed, and says so above or below this text. Do not record it again and do not call `acr_adopt`.

1. Call `acr_status` and read it. Report what it shows. If it does not show ACR in use, say that plainly; do not say ACR is in use because the command was typed.
2. Call `acr_kernel`, read what it returns in full and follow it. Record that you hold it: `acr_submit` kind `DELIVERY_STATE`, body `{"agent": "<your label, as acr_status shows it>", "event": "DELIVER", "text": "b8d509386caf0330150673d2da70f0daf1039d4410ed755571dd826fd8b0148a"}`.
3. Tell the person, in one or two plain sentences, that ACR is in use in this project and that nothing is under review yet. Ask what they want reviewed.
4. Commission nothing and commit no gate until they say what to review. Ordinary work stays ordinary: ACR being in use adds no review to a request that did not ask for one (Core 1.2).

They can stop ACR at any time by saying so.

Your participant label is `assistant` unless `acr_status` shows another under DELIVERY or the tool's answer names another. It is a label of the record, not your model's name.
