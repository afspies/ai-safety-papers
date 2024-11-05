---
title: "Dynamic modelling of signalling pathways when ODEs are not feasible"
description: "Motivation Mathematical modelling plays a crucial role in understanding inter- and intracellular signalling processes. Currently, ordinary differential equations (ODEs) are the predominant approach in"
authors: []
date: 2024-11-05
bookcase_cover_src: '/posts/paper_acc3791d6241d168aa1cb932106f46769c05b26a/thumbnail.png'
weight: 1
---

The paper introduces an extension of the retarded transient function (RTF) approach to model dose-dependent dynamics of cellular signaling pathways. The key points are:

- The RTF is a phenomenological modeling approach that describes signaling dynamics using a sustained and transient component, avoiding the need for full mechanistic ordinary differential equation (ODE) models.
- The original time-dependent RTF is extended to incorporate dose-dependencies using Hill equations, allowing it to capture both time- and dose-dependent behaviors.
- The dose-dependent RTF requires fewer parameters than fitting individual RTFs to each dose, and far fewer than ODE models, while still accurately describing experimental data.
- The approach enables statistically rigorous analysis of differences in pathway responses across biological conditions like wild-type and knockdown cells.
- It is applied to model time- and dose-dependent inflammasome activation data in murine dendritic cells, demonstrating its ability to identify significant differences between wild-type and NEK7 knockdown conditions {{< figure src="fig_5_0_fig3.png" >}} *[See Figure 4 in the original paper]*.
- The dose-dependent RTF provides an interpretable, non-mechanistic modeling approach complementary to ODEs for studying cellular signaling dynamics when full mechanistic models are infeasible.

---

[Read the original paper](https://www.biorxiv.org/content/biorxiv/early/2024/04/20/2024.04.18.590024.full.pdf)