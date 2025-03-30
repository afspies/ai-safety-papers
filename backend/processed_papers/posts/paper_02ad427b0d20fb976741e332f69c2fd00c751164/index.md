---
title: "Identifying Functionally Important Features with End-to-End Sparse Dictionary Learning"
description: "Identifying the features learned by neural networks is a core challenge in mechanistic interpretability. Sparse autoencoders (SAEs), which learn a sparse, overcomplete dictionary that reconstructs a n..."
authors: ["Dan Braun", "Jordan K. Taylor", "Nicholas Goldowsky-Dill", "Lee Sharkey"]
date: 2025-03-28
paper_url: "https://arxiv.org/pdf/2405.12241.pdf"
---

# Identifying Functionally Important Features with End-to-End Sparse Dictionary Learning

### Core Insight
Standard sparse autoencoders may learn dataset structure rather than functionally important network features; this paper introduces end-to-end sparse dictionary learning that optimizes for functional importance by minimizing KL divergence between original and SAE-modified model outputs, achieving better performance with fewer features (

**Figure 1**

![Figure 1.a](https://assets.afspies.com/figures/02ad427b0d20fb976741e332f69c2fd00c751164/fig1_a.png)

![Figure 1.b](https://assets.afspies.com/figures/02ad427b0d20fb976741e332f69c2fd00c751164/fig1_b.png)

).

### Key Contributions
- End-to-end SAEs (e2e SAEs) require less than 45% of the features per datapoint compared to standard SAEs for the same level of performance explained (**Figure 1**, **Figure 4**).
- E2e SAEs with downstream reconstruction (SAEe2e+ds) maintain similar pathways through the network as the original model, unlike pure e2e SAEs (**Figure 2**).
- E2e SAEs require fewer total features (alive dictionary elements) over the entire dataset while maintaining similar or better interpretability scores (**Figure 1**, **Figure 9**).
- E2e SAE features are more orthogonal than standard SAE features, suggesting less feature splitting (

**Figure 3**

![Figure 3.a](https://assets.afspies.com/figures/02ad427b0d20fb976741e332f69c2fd00c751164/fig3_a.png)

![Figure 3.b](https://assets.afspies.com/figures/02ad427b0d20fb976741e332f69c2fd00c751164/fig3_b.png)

![Figure 3.c](https://assets.afspies.com/figures/02ad427b0d20fb976741e332f69c2fd00c751164/fig3_c.png)

, **Figure 7**).

### Methodology
The authors introduce three SAE training approaches: SAElocal (standard approach minimizing reconstruction error), SAEe2e (minimizing KL divergence between original and SAE-modified outputs), and SAEe2e+ds (adding downstream reconstruction loss to SAEe2e) (**Figure 1**). Experiments were conducted on GPT2-small and Tinystories-1M models, evaluating performance using CE loss increase, L0 (features per datapoint), and number of alive dictionary elements.

### Critical Findings
- For the same level of performance explained, SAElocal requires activating more than twice as many features per datapoint compared to SAEe2e+ds and SAEe2e (**Figure 1**, **Figure 4**).
- SAEe2e+ds features are more interpretable than SAElocal features in layers 2 (p=0.0053) and 6 (p=0.0005) with no significant difference in layer 10 (**Figure 9**).
- SAEe2e features take different computational pathways through the network compared to SAElocal, while SAEe2e+ds maintains similar pathways to the original model in later layers (**Figure 2**).

### Limitations & Implications
- E2e SAEs require 2-3.5 times longer training time compared to standard SAEs, though this can be mitigated by using fewer training samples or smaller dictionary sizes (**Figure 16**, **Figure 17**).
- The approach brings us closer to methods that can explain network behavior concisely and accurately, with potential applications in mechanistic interpretability for understanding and improving neural networks.

## Figures

![2](https://assets.afspies.com/figures/02ad427b0d20fb976741e332f69c2fd00c751164/fig2.png)

