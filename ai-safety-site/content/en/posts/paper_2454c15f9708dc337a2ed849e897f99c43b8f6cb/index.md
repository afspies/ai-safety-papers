---
title: "Llama Scope: Extracting Millions of Features from Llama-3.1-8B with Sparse Autoencoders"
description: "Sparse Autoencoders (SAEs) have emerged as a powerful unsupervised method for extracting sparse representations from language models, yet scalable training remains a significant challenge. We introduc"
authors: ["Zhengfu He", "Wentao Shu", "Xuyang Ge", "Lingjie Chen", "Junxuan Wang", "Yunhua Zhou", "Frances Liu", "Qipeng Guo", "Xuanjing Huang", "Zuxuan Wu", "Yu-Gang Jiang", "Xipeng Qiu"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2410.20526.pdf"
abstract: "Sparse Autoencoders (SAEs) have emerged as a powerful unsupervised method for extracting sparse representations from language models, yet scalable training remains a significant challenge. We introduce a suite of 256 SAEs, trained on each layer and sublayer of the Llama-3.1-8B-Base model, with 32K and 128K features. Modifications to a state-of-the-art SAE variant, Top-K SAEs, are evaluated across multiple dimensions. In particular, we assess the generalizability of SAEs trained on base models to longer contexts and fine-tuned models. Additionally, we analyze the geometry of learned SAE latents, confirming that \\emph{feature splitting} enables the discovery of new features. The Llama Scope SAE checkpoints are publicly available at~\\url{https://huggingface.co/fnlp/Llama-Scope}, alongside our scalable training, interpretation, and visualization tools at \\url{https://github.com/OpenMOSS/Language-Model-SAEs}. These contributions aim to advance the open-source Sparse Autoencoder ecosystem and support mechanistic interpretability research by reducing the need for redundant SAE training."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_2454c15f9708dc337a2ed849e897f99c43b8f6cb/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper introduces Llama Scope, a comprehensive suite of 256 Sparse Autoencoders (SAEs) trained on the Llama-3.1-8B language model. The work represents a significant advancement in mechanistic interpretability research by providing ready-to-use, open-source SAE models that can help researchers understand the internal representations of large language models. Key aspects of the work include: 

1. **Architecture and Training Position** 

{{< figure src="fig1.png" caption="**Figure 1:** Four potential training positions in one Transformer Block." >}}

Figure 1 The authors train SAEs at four different positions within each transformer block: - Post-MLP Residual Stream (R) - Attention Output (A) - MLP Output (M) - Transcoder (TC) 

2. **Technical Improvements** The authors introduce several modifications to the TopK SAE architecture: - Incorporation of decoder column 2-norm into TopK computation - Post-processing to JumpReLU variants - K-annealing training schedule - Mixed parallelism approach for efficient training 

3. **Evaluation Results** 

{{< figure src="fig2.png" caption="**Figure 2:** Explained Variance (upper) and Delta LM loss (lower) over L0 sparsity for SAEs trained on L7R, L15R and L23R." >}}

Figure 2 The results show that: - TopK SAEs consistently outperform vanilla SAEs in sparsity-fidelity trade-offs - Wider SAEs (32x) achieve better reconstruction while maintaining similar sparsity - The approach generalizes well to longer contexts and instruction-tuned models 

4. **Feature Analysis** 

{{< figure src="fig7.png" caption="**Figure 7:** Feature geometry of L15R-8x-Vanilla, L15R-8x-TopK and L15R-32x-TopK SAEs." >}}

Figure 7 The authors conduct an in-depth analysis of feature geometry, demonstrating how different SAEs learn related but distinct features. They show that wider SAEs don't just learn combinations of existing features but discover entirely new ones. The visualization of the "Threats-to-Humanity" cluster provides a compelling example of how features organize themselves semantically. 

5. **Comprehensive Evaluation** 

{{< figure src="fig10.png" caption="**Figure 10:** All 256 SAEs are evaluated on L0 sparsity (upper), explained variance (middle) and Delta LM loss (lower)." >}}

Figure 10 The paper includes extensive evaluation across all 256 SAEs, measuring L0 sparsity, explained variance, and Delta LM loss across different layers and positions. The work makes several significant contributions to the field: - Provides the first comprehensive suite of SAEs for a large language model - Introduces practical improvements to SAE training and architecture - Demonstrates scalability and generalization capabilities - Offers insights into feature organization and discovery The authors make all models and tools publicly available, which should significantly accelerate research in mechanistic interpretability by reducing the need for redundant SAE training. The paper's technical depth combined with practical utility makes it a valuable contribution to both the theoretical understanding of language models and the practical tools available to researchers in the field.