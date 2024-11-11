---
title: "Bilinear MLPs enable weight-based mechanistic interpretability"
description: "A mechanistic understanding of how MLPs do computation in deep neural networks remains elusive. Current interpretability work can extract features from hidden activations over an input dataset but gen"
authors: ["Michael T. Pearce", "Thomas Dooms", "Alice Rigg", "José Oramas", "Lee Sharkey"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2410.08417.pdf"
abstract: "A mechanistic understanding of how MLPs do computation in deep neural networks remains elusive. Current interpretability work can extract features from hidden activations over an input dataset but generally cannot explain how MLP weights construct features. One challenge is that element-wise nonlinearities introduce higher-order interactions and make it difficult to trace computations through the MLP layer. In this paper, we analyze bilinear MLPs, a type of Gated Linear Unit (GLU) without any element-wise nonlinearity that nevertheless achieves competitive performance. Bilinear MLPs can be fully expressed in terms of linear operations using a third-order tensor, allowing flexible analysis of the weights. Analyzing the spectra of bilinear MLP weights using eigendecomposition reveals interpretable low-rank structure across toy tasks, image classification, and language modeling. We use this understanding to craft adversarial examples, uncover overfitting, and identify small language model circuits directly from the weights alone. Our results demonstrate that bilinear layers serve as an interpretable drop-in replacement for current activation functions and that weight-based interpretability is viable for understanding deep-learning models."
tldr: "The results demonstrate that bilinear layers serve as an interpretable drop-in replacement for current activation functions and that weight-based interpretability is viable for understanding deep-learning models."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_1ac2d6f203b3bdd3503357b0839c24a485d6ce1d/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper introduces an important advancement in neural network interpretability by analyzing bilinear MLPs, which are a variant of Gated Linear Units (GLUs) without element-wise nonlinearity. The authors demonstrate that these bilinear MLPs can achieve competitive performance while being significantly more interpretable than traditional MLPs. Key contributions: 

1. **Theoretical Framework** The authors show that bilinear MLPs can be fully expressed using linear operations with a third-order tensor, making them amenable to mathematical analysis. 

{{< figure src="fig1.png" caption="**Figure 1:** A) Two ways to represent a bilinear layer, via an elementwise product or the bilinear tensor. B) Diagram of the eigendecomposition technique. Multiplying the bilinear tensor by a desired output direction \ ${\\mathbf{u}}\ $ produces an interaction matrix \ ${\\mathbf{Q}}\ $ that can be decomposed into a set of eigenvectors \ ${\\mathbf{v}}\ $ and associated eigenvalues \ $\\lambda_{i}.\$" >}}

Figure 1 illustrates how bilinear layers can be represented either through elementwise products or using the bilinear tensor. 

2. **Eigendecomposition Analysis** A major contribution is the introduction of eigendecomposition techniques to analyze bilinear MLP weights. 

*[See Figure 2 in the original paper]*

 demonstrates how eigenvector activations work and shows examples of interpretable patterns learned for image classification tasks. The eigenvectors often correspond to meaningful features like edge detectors or class-specific patterns. 

3. **Image Classification Insights** The authors apply their methods to MNIST and Fashion-MNIST classification tasks, revealing that: - Models learn interpretable low-rank structure - Regularization improves feature interpretability - Top eigenvectors capture meaningful patterns 

{{< figure src="fig3.png" caption="**Figure 3:** The top four positive (top) and negative (bottom) eigenvectors for the digit 5, ordered from left to right by importance. Their eigenvalues are highlighted on the left. Only 20 positive and 20 negative eigenvalues (out of 512) are shown on the left images. Eigenvectors tend to represent semantically and spatially coherent structures." >}}

Figure 3 shows how different eigenvalues contribute to digit classification. 

4. **Language Model Analysis** The researchers analyze a 6-layer transformer with bilinear MLPs trained on TinyStories. 

{{< figure src="fig8.png" caption="**Figure 8:** The sentiment negation circuit for computing the not-good and not-bad output features. A) The interaction submatrix containing the top 15 interactions. B) The top interacting features projected onto the top positive and negative eigenvectors using cosine similarity, with the symbols for different clusters matching the labels in A. Clusters coincide with the projection of meaningful directions such as the difference in “bad” vs “good” token unembeddings and the MLP’s input activations for input tokens “[BOS] not”. C) The not-good feature activation compared to its approximation by the top two eigenvectors." >}}

Figure 8 demonstrates a discovered sentiment negation circuit, showing how the model learns to flip sentiment based on negation words. 

{{< figure src="fig9.png" caption="**Figure 9:** Activation correlations with low-rank approximations. A) Average correlation over output features computed over all inputs before the SAE’s non-linearity (TopK) is applied or only on inputs where the feature is active. B) The distribution of active-only correlations for approximations using the top two eigenvectors. C) Scatter plots for a random set of nine output features. Approximations use the top two eigenvectors." >}}

Figure 9 shows that many output features can be well-approximated by low-rank matrices. Key findings: 

1. Bilinear MLPs offer similar performance to traditional MLPs while being more interpretable 

2. The eigendecomposition reveals interpretable low-rank structure across different tasks 

3. The method enables direct analysis of model weights without requiring input data 

4. The approach can identify specific computational circuits in language models The paper demonstrates that bilinear MLPs could serve as a drop-in replacement for traditional MLPs in many applications, offering improved interpretability without significant performance trade-offs. The authors also provide practical guidance for implementing and analyzing bilinear layers. The work opens new possibilities for mechanistic interpretability by showing how model weights can be directly analyzed without relying on activation patterns from specific inputs. This could lead to more robust and generalizable interpretability methods for deep learning models.