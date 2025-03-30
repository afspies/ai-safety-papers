---
title: "Interpretability in Parameter Space: Minimizing Mechanistic Description Length with Attribution-based Parameter Decomposition"
description: "Mechanistic interpretability aims to understand the internal mechanisms learned by neural networks. Despite recent progress toward this goal, it remains unclear how best to decompose neural network pa..."
authors: ["Dan Braun", "Lucius Bushnaq", "Stefan Heimersheim", "Jake Mendel", "Lee Sharkey"]
date: 2025-03-28
paper_url: "https://arxiv.org/pdf/2501.14926.pdf"
---

# Interpretability in Parameter Space: Minimizing Mechanistic Description Length with Attribution-based Parameter Decomposition

## Core Insight
Attribution-based Parameter Decomposition (APD) directly decomposes neural network parameters into faithful, minimal, and simple mechanistic components that optimize for minimal description length, successfully identifying ground truth mechanisms in superposition and cross-layer distributed representations as shown in **Figure 1**.

## Key Contributions
- Introduces a parameter-space approach to mechanistic interpretability that decomposes networks into components that sum to the original parameters (faithful), require minimal components per input (minimal), and are maximally simple **Figure 2**
- Successfully recovers ground truth mechanisms in superposition with near-perfect direction alignment (MMCS ≈ 0.998) as demonstrated in **Figure 3**
- Identifies individual computational mechanisms in models performing compressed computation (computing more functions than neurons) across multiple layers **Figure 6**
- Demonstrates that parameter components are causally responsible for specific computations through ablation studies showing minimal impact when unrelated components are removed **Figure 8**

## Methodology
APD decomposes neural network parameters θ* into components {Pc} that sum to the original parameters (faithfulness loss), while using attributions to identify which components are causally important for each input (minimality loss), and penalizing components for high rank across layers (simplicity loss) as illustrated in **Figure 2** and **Figure 4**. The method uses gradient-based attributions to determine which parameter components are most responsible for network outputs on specific inputs, then trains only the top-k attributed components to reconstruct the network's behavior.

## Critical Findings
- In the Toy Model of Superposition, APD successfully recovers parameter components that correspond to individual features with Mean Max Cosine Similarity of 0.998 ± 0.000 and Mean L2 Ratio of 0.893 ± 0.004 **Figure 3**
- In the Compressed Computation model, APD identifies parameter components that each implement computations for specific input features despite the model computing more functions (100) than it has neurons (50) **Figure 6**
- Ablation experiments show that removing parameter components unrelated to active inputs ("scrubbed" runs) causes minimal performance degradation, while removing relevant components ("anti-scrubbed" runs) significantly increases error **Figure 7** and **Figure 8**

## Limitations & Implications
- Current implementation has high computational cost (potentially O(N²) where N is parameter count) and sensitivity to hyperparameters, limiting application to toy models
- The approach suggests solutions to long-standing problems in mechanistic interpretability including identifying minimal circuits in superposition, providing a conceptual foundation for 'features', and enabling architecture-agnostic neural network decomposition

## Figures

![1](https://assets.afspies.com/figures/1a365128aa7b41478bf5251793a691d8b5d8ff27/fig1.png)

![2](https://assets.afspies.com/figures/1a365128aa7b41478bf5251793a691d8b5d8ff27/fig2.png)

![3](https://assets.afspies.com/figures/1a365128aa7b41478bf5251793a691d8b5d8ff27/fig3.png)

![6](https://assets.afspies.com/figures/1a365128aa7b41478bf5251793a691d8b5d8ff27/fig6.png)

![8](https://assets.afspies.com/figures/1a365128aa7b41478bf5251793a691d8b5d8ff27/fig8.png)

![4](https://assets.afspies.com/figures/1a365128aa7b41478bf5251793a691d8b5d8ff27/fig4.png)

![7](https://assets.afspies.com/figures/1a365128aa7b41478bf5251793a691d8b5d8ff27/fig7.png)

