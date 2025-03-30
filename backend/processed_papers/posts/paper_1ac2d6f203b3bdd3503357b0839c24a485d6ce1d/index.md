---
title: "Bilinear MLPs enable weight-based mechanistic interpretability"
description: "A mechanistic understanding of how MLPs do computation in deep neural networks remains elusive. Current interpretability work can extract features from hidden activations over an input dataset but gen..."
authors: ["Michael T. Pearce", "Thomas Dooms", "Alice Rigg", "José Oramas", "Lee Sharkey"]
date: 2025-03-28
paper_url: "https://arxiv.org/pdf/2410.08417.pdf"
---

# Bilinear MLPs enable weight-based mechanistic interpretability

## Core Insight
Bilinear MLPs enable weight-based mechanistic interpretability by replacing element-wise nonlinearities with tensor-based linear operations that reveal interpretable low-rank structure through eigendecomposition, as demonstrated by the digit-specific patterns in <FIGURE_ID>2.A</FIGURE_ID> and sentiment negation circuits in **Figure 8**.

## Key Contributions
- Introduced methods to analyze bilinear MLPs through eigendecomposition that decomposes weights into interpretable eigenvectors explaining outputs along specific directions (**Figure 1**)
- Demonstrated that bilinear MLP weights have interpretable low-rank structure across image classification tasks, with eigenvectors functioning as edge detectors (<FIGURE_ID>2.B</FIGURE_ID>) that remain consistent across model sizes (<FIGURE_ID>5.A</FIGURE_ID>)
- Identified a sentiment negation circuit directly from weights in language models, showing how negation tokens flip sentiment through quadratic interactions (**Figure 8**)
- Showed that 69% of output features in language models have high correlation (>0.75) with low-rank approximations using just two eigenvectors (<FIGURE_ID>9.B</FIGURE_ID>)

## Methodology
Bilinear MLPs replace element-wise nonlinearities with the form g(x) = (Wx) ⊙ (Vx), which can be expressed as a third-order tensor B with elements baij = waivaj (**Figure 1**). This tensor can be analyzed through eigendecomposition of interaction matrices Q = u·outB for specific output directions, revealing orthogonal eigenvectors that diagonalize the computation (**Figure 1**).

## Critical Findings
- Eigenvectors of bilinear MLPs trained on image classification tasks reveal interpretable patterns specific to each class, with only a small fraction of eigenvalues having non-negligible magnitude (**Figure 3**)
- Models trained with Gaussian noise regularization produce more interpretable eigenvectors with lower-rank eigenvalue spectra while maintaining competitive accuracy (97.2-98.1%) (**Figure 4**)
- Truncating all but the top few eigenvectors (per digit) preserves classification accuracy across model sizes, with minimal accuracy drops (0.01%) when retaining only a handful of eigenvectors (<FIGURE_ID>5.B</FIGURE_ID>)

## Limitations & Implications
- Application of the methods typically relies on having meaningful output directions available, which may require dataset-dependent sparse autoencoders for deeper models
- While eigenvalue spectra are often low-rank, there are no guarantees the eigenvectors will be monosemantic, and orthogonality constraints between eigenvectors may limit interpretability for high-rank spectra

## Figures

![8](https://assets.afspies.com/figures/1ac2d6f203b3bdd3503357b0839c24a485d6ce1d/fig8.png)

![1](https://assets.afspies.com/figures/1ac2d6f203b3bdd3503357b0839c24a485d6ce1d/fig1.png)

![3](https://assets.afspies.com/figures/1ac2d6f203b3bdd3503357b0839c24a485d6ce1d/fig3.png)

![4](https://assets.afspies.com/figures/1ac2d6f203b3bdd3503357b0839c24a485d6ce1d/fig4.png)

