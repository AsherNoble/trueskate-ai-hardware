# BOM diff from rollback checkpoint 800ba4a

| Change | Reference(s) | Details |
|---|---|---|
| Added | D1 | 1N4742A 12V; Hand |
| Changed | J31 | C7588156 → C160405; SM06B-SRSS-TB; Hand |
| Changed | J32 | C7588156 → C160405; SM06B-SRSS-TB; Hand |
| Changed | J33 | C7588156 → C160405; SM06B-SRSS-TB; Hand |
| Changed | J34 | C7588156 → C160405; SM06B-SRSS-TB; Hand |
| Changed | J35 | C7588156 → C160405; SM06B-SRSS-TB; Hand |
| Changed | J36 | C7588156 → C160405; SM06B-SRSS-TB; Hand |
| Added | Q1 | IRF4905PBF; Hand |
| Added | R2 | 10k gate pull-down; Hand |

This pass adds Q1 (Infineon IRF4905PbF, C2564), D1 (ST(Semtech) 1N4742A 12V, C2545), and R2 (TyoHM RD1/4W10KJT/BA1, C433778), one each. All three are hand-soldered through-hole. No removals or footprint/placement changes. J31-J36 change supplier code and assembly to Hand. F1 remains one complete Keystone 3557-2; fuse rated to the connected supply. Q1 needs no heat sink below ~5 A continuous; 12 A is copper sizing only. J31-J36 use stocked JST lead-free/tin supplier code C160405 in place of C7588156, without footprint/placement changes.
