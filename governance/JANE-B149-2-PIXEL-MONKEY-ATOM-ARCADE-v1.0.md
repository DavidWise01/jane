# B149.2 — Pixel Monkey Atom Arcade

Supersedes the **visual treatment** of B149 without changing the B149 transition kernel or its evidence policy.

Inspired by the visual vocabulary of retro, low-resolution pixel-art TV animation, **not copied artwork**. Original pixel monkey coder sprites work at three laboratory consoles while a procedurally projected 3D atomic nucleus and five orbital / sphere visual registers rotate in an integer-resolution Canvas game scene.

- 320×200 canvas, crisp nearest-neighbor CSS scaling, original procedural monkey sprite matrices, dark teal/orange/violet pixel UI.
- Atom mode: projected 3D orbital paths, five animated electron points, stylized nucleus.
- Sphere mode: five separate signed *visual* rings, perspective projection and selectable S1–S5 registers.
- Controls: keyboard arrows rotate/tilt; 1–5 select; Space pause; P probe; pointer drag orbit. Speed slider, run/pause, uncertain/conflict demo, session JSON export.
- One shadow fold `{-1,+1}>1`; **five subsequent signed sphere registers are not shadows**. Four field labels and six XYZ directions preserved.
- Independent witness ids a1/b1/c1. Synthetic crossings are **SIMULATED_CROSSING**, uncertain or inconsistent crossings **HOLD**, and no record promotes empirical physics. The log is session-only. Reference spheres remain unassigned to visual slots.

This is software-perspective projection rendered in Canvas2D, **not** a Three.js WebGL scene. The atom visual is conceptual and does not model true quantum electron orbitals. The previous 3D/WebGL variant remains accessible in commit history, and the node transition kernel is unchanged.

Source: `b149/index.html`; intended Pages route `https://davidwise01.github.io/jane/b149/`. Syntax checked locally using Node; live browser deployment not independently verified.
