# B155 — [a:122, b:122, c:122 : d: a+b+c :: isa]

The user-defined expression is instantiated as a **minimal instruction-set architecture (ISA)**, not a physics ISA or a proposed processor standard.

```text
[a:122  b:122  c:122 : d: a+b+c :: isa]
   |      |      |         |
 {H/a1} {O/b1} {N/c1}   READ-ONLY 366-address composition
 001-122 123-244 245-366   d is derived: NOT 122 more cells

  each register = [BOX62] + (TOROID60) = 122
  all cells      = 122 + 122 + 122    = 366

  root only: {-1,+1}>1
  signed STEP: + / - within each 122-address ring
```

## Opcodes

| Opcode | Meaning | Source mutation? |
|---|---|---|
| `ADDR global` | Decode global 001–366 to its owning a/b/c register and local position | No |
| `READ register,local` | Inspect the Box/Toroid cell without changing pointers | No |
| `STEP register,sign` | Advance or reverse that register's pointer by one modulo 122 | Pointer only; an audit entry is appended |
| `ASSEMBLE` | Compose derived register d as H+O+N with all 366 global addresses | No |
| `WITNESS register` | Append a distinct, simulated a1/b1/c1 pointer observation | No |
| `CHECK` | Audit aggregate size, pointer bounds and the one-shadow/no-quorum constraints | No |

The ISA has three distinct program counters and one derived d-view; there is no fourth 122-cell storage block. `d` does not add to 366. Forward/reverse signs do not double the cell count. Instruction results are SHA-256 chain-recorded by the Node kernel and exported as session audit data by the browser UI (browser demo checksums are not cryptographic signatures).

The GITHUB PAGES route `/jane/b155/` is a new versioned page preserving the 3D-projected pixel monkey observatory and its B154 traversal panel. B155's ISA console controls can execute instructions, switch register focus, inspect values and export the session instructions.

All H/O/N atom and shell analogies are symbolic simulation constructs. They are **not** measured hydrogen/oxygen/nitrogen electron orbitals, shell occupancies, forces, or material facts. Their associated real-physics interpretations remain HOLD.

Next natural invariant: formal opcode execution traces, interrupt/resume checkpoints and deterministic register-level replay against a reference interpreter; preserve the exact last committed instruction without inventing a result.
