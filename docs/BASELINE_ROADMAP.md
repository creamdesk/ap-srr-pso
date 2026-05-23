# Baseline Roadmap

The current implemented baseline set is useful for engineering validation but not sufficient for a strong journal claim by itself.

## Implemented or already planned

- PSO
- PSO-RS
- PSO-AW
- ARPSO-SRR
- DE
- AP-SRR-PSO

## Strong baselines to add or justify

Before a serious SCI journal submission, add at least some stronger baselines or explicitly justify why they are omitted:

- CLPSO
- HPSO-TVAC
- JADE or SHADE
- CMA-ES if implementation cost is acceptable

## Baseline policy

Do not compare only against weak PSO variants. The paper should position AP-SRR-PSO as improving PSO-family behavior while remaining conservative against strong evolutionary optimizers.

## Reporting policy

If AP-SRR-PSO does not beat DE or stronger baselines everywhere, do not hide that. Report function categories separately and discuss robustness, stability, and PSO-family improvement.

## Implementation priority

1. Ensure PSO, PSO-RS, PSO-AW, ARPSO-SRR, DE, and AP-SRR-PSO are stable.
2. Add CLPSO.
3. Add HPSO-TVAC.
4. Add JADE or SHADE.
5. Consider CMA-ES only if dependency and runtime are manageable.
