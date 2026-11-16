# JANE 248 — The Source That Advertised a False Stratum

**Invariant:** Reported Clock Stratum != Verified Time Authority.

The local tested package contains the Python verifier, 35 unit tests, saved synthetic receipts, and an interactive HTML chapter. The verifier checks claimed NTP stratum versus declared upstream lineage: stratum 1 claims cannot name a parent, known secondary strata must increment the upstream stratum, and stratum 0/16, leap 3, cycles, missing parents, and invalid records must not be accepted as independently verified time.

**Results:** 35/35 local tests passed. False-stratum and cycle fixtures are withheld. A consistent fixture is reported as declared claims only. Zero live NTP servers were queried. Zero independent time authorities are proven. Jane's collective choice remains UNRESOLVED, with zero actions executed.

This README and the HTML were published independently of the tested ZIP. The full Python sources and proposed workflow are currently available through the local ZIP; do not infer that they are on GitHub.

**Next JANE 249:** Primary Clock Claim != Verified Reference Clock.
