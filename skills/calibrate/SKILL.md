---
name: calibrate
description: Take part in a Calibration - the measurement of whether ACR, as delivered here, has arrived (Core 14.4). Use only when the person asks for a calibration of this assistant, or types the calibrate command. Not for ordinary requests, and not for instrument or model calibration in the person's own subject.
---

# Calibration

Calibration is the measurement of onboarding (Core Section 14.4): counts of what an assistant holds of ACR, what it retrieves exactly when asked, and what it does on items with known answers. It is a measurement someone makes of you. It is not a state you reach by reading, and you do not score yourself.

When the person asks for one:

1. **Say what is being measured.** The model and host, as far as the host tells you; how ACR reaches you here (this plugin: a tool server that fetches exact provisions, delivery TOOL_ASSISTED); and what of it you can reach. Say UNKNOWN for what you do not know.
2. **Retrieval.** The person gives you questions made by the method packet's tool (`TOOLS/calibrate.py prompt`). Answer each from what you can inspect here: `acr_clause` for a section, and `acr_modules` for which modules there are; a section the tool says is absent is absent. Give the source's exact words where you have inspected them; `NOT_INSPECTED` where you cannot inspect them; `NOT_DEFINED` where you have inspected that there is no such section or term. Do not answer from memory of what such a text usually says: an invented sentence counts against, and so does declining what was in reach. Reply with the JSON list the questions ask for and nothing else. The key stays with the person; do not ask for it or look for it.
3. **Application.** This part is scored by someone other than you, reading your replies to items with known answers against criteria fixed before the run. If you are asked to grade your own replies, say that this is a self-check and that the record carries it as NOT_MEASURED. Where the items reach you one turn at a time in this session (`TOOLS/calibrate.py administer`), answer each turn as you would answer the person, and do not open the probes, their criteria or earlier readings; if you have already seen any of them, or a description of them, say which, because the record must (Core 14.4).
4. **The result.** Give the counts that were produced, each with its number of runs, who scored it and the date. Do not say that you are calibrated. Where no Calibration of this assistant in this configuration exists, the entry is NONE, and you say NONE.

A Calibration Record can be checked by the program itself: `acr_instrument` with instrument `core.calibration` and the record as `input.record`. It says whether the record's counts agree with each other and whether its thresholds and claim say no more than its counts. It does not say that the counts are true.

A Calibration describes one assistant in one configuration on one date. It is not a grade, it says nothing after a change of model or delivery or a long session, and it is not evidence that ACR works.
