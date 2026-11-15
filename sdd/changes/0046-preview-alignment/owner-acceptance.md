# Owner acceptance — preview alignment

**Date:** 2026-11-15. The Owner accepted the sample DOCX in desktop Word and the visual direction,
with the two follow-ups below. This records the supplied Owner feedback; it does not claim that
an Implementer performed the Owner's Word test or independently reviewed the implementation.

## What the Owner reviewed

- Hub portal: <http://127.0.0.1:8766/>.
- Template reading site: <http://127.0.0.1:8767/>.
- Sample reading site: <http://127.0.0.1:8768/>, served from the edition-preview artifacts of
  [CI run 43734028505](https://github.com/cesarcastrocuba/handbooks-hub/actions/runs/43734028505).
- The **sample's** edition-preview DOCX from that run, opened in desktop Word: “perfecto”.
  This is acceptance of the sample document, not a claim that Word tested the template follow-up.

## Owner feedback, verbatim

> Me gusta lo que veo, está muy bien buen trabajo, solo una cosa en la home de hub en los botones
> Browse the library y Create your handbook en el hover salen dos flechitas a la derecha, no se ven
> bien por el espaciado, no sé si se puede arreglar o quitar, en la plantilla Review Checklist no
> sale en gris, el libro ejemplo está bastante bien, creo que ha quedado mejor aún la tabla con filas
> de color crema claro porque se observa muy bien inclusive dentro de los boxes. Sobre el word
> perfecto

## Follow-ups

1. **Button hover arrows:** removed the generated button `::after` arrow and its now-unused motion
   tokens/schema entries. Button lift, the visible focus outline, guide-card arrows and the explicit
   “Read handbook →” link remain. The real-browser motion test checks that hovering does not generate
   an arrow while the lift still follows the reduced-motion preference.
2. **Template Review Checklist:** changed its classes to `.callout-note .review`, retaining the exact
   title “Review Checklist — Example Chapter”. HTML and DOCX now choose the neutral role. The PDF
   matcher already searches for the `Review Checklist` substring, so the suffixed title continues
   to select the neutral PDF role without changing the matcher or title. Tests cover the template
   source, rendered HTML and the DOCX review-title style and neutral box shading.

The root CHANGELOG records the template content correction under the unreleased change. Template
version 1.5.1 and its toolkit 0.10.3 pin remain unchanged; the template 1.6.0 release is a later PR.
STATUS and decisions are outside this follow-up's write set and are not edited.

## DOCX acceptance boundary

The accepted sample DOCX is downloaded from `edition-preview-sample` artifact **14169259876** of
run 43734028505. Its SHA-256 is
`744deb27b1837fe64956e69ee1c7464a9e1bfbca7869303a00dc8dba90a56a83`.
A fresh sample build with the follow-up is **byte-for-byte identical** to that accepted file.
The exact comparison and the template DOCX comparison are recorded in evidence.md. No sample manuscript or
DOCX processing code is changed. The template DOCX changes its checklist's callout role from
Important to Review; its wording and the rest of its content are retained. The separate template
export also updates the normal created/modified build timestamps in the DOCX core metadata.

Final follow-up verification: **434 tests passed**, plus fast/full repository validators
(**5/7 checks, zero problems**). The preview servers on 8766/8767 are rebuilt from the pushed
follow-up HEAD; the sample on 8768 is retained. See [evidence.md](evidence.md) and the
[follow-up inspection sheet](owner-followup.webp).
