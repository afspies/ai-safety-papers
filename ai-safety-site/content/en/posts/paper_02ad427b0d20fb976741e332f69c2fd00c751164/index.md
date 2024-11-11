---
title: "Identifying Functionally Important Features with End-to-End Sparse Dictionary Learning"
description: "Identifying the features learned by neural networks is a core challenge in mechanistic interpretability. Sparse autoencoders (SAEs), which learn a sparse, overcomplete dictionary that reconstructs a n"
authors: ["Dan Braun", "Jordan K. Taylor", "Nicholas Goldowsky-Dill", "Lee Sharkey"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2405.12241.pdf"
abstract: "Identifying the features learned by neural networks is a core challenge in mechanistic interpretability. Sparse autoencoders (SAEs), which learn a sparse, overcomplete dictionary that reconstructs a network's internal activations, have been used to identify these features. However, SAEs may learn more about the structure of the datatset than the computational structure of the network. There is therefore only indirect reason to believe that the directions found in these dictionaries are functionally important to the network. We propose end-to-end (e2e) sparse dictionary learning, a method for training SAEs that ensures the features learned are functionally important by minimizing the KL divergence between the output distributions of the original model and the model with SAE activations inserted. Compared to standard SAEs, e2e SAEs offer a Pareto improvement: They explain more network performance, require fewer total features, and require fewer simultaneously active features per datapoint, all with no cost to interpretability. We explore geometric and qualitative differences between e2e SAE features and standard SAE features. E2e dictionary learning brings us closer to methods that can explain network behavior concisely and accurately. We release our library for training e2e SAEs and reproducing our analysis at https://github.com/ApolloResearch/e2e_sae"
tldr: "End-to-end (e2e) sparse dictionary learning is proposed, a method for training SAEs that ensures the features learned are functionally important by minimizing the KL divergence between the output distributions of the original model and the model with SAE activations inserted."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_02ad427b0d20fb976741e332f69c2fd00c751164/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper introduces end-to-end sparse dictionary learning (e2e SAE), a novel method for training sparse autoencoders (SAEs) that improves their ability to identify functionally important features in neural networks. **Key Innovation:** Traditional SAEs are trained to minimize reconstruction error of network activations, but this approach may learn features that aren't maximally relevant for the network's actual computation. The authors propose training SAEs by minimizing the KL divergence between the output distributions of: 

1. The original model 

2. The model with SAE activations inserted 

{{< figure src="fig1.png" caption="**Figure 1:** Top: Diagram comparing the loss terms used to train each type of SAE. Each arrow is a loss term which compares the activations represented by circles. \ $\\text{SAE}_{\\text{local}}\ $ uses MSE reconstruction loss between the SAE input and the SAE output. \ $\\text{SAE}_{\\text{e2e}}\ $ uses KL-divergence on the logits. \ $\\text{SAE}_{\\text{e2e+ds}}\ $ (end-to-end \ $+\ $ downstream reconstruction) uses KL-divergence in addition to the sum of the MSE reconstruction losses at all future layers. All three are additionally trained with a \ $L_{1}\ $ sparsity penalty (not pictured).Bottom: Pareto curves for three different types of SAE as the sparsity coefficient is varied. E2e-SAEs require fewer features per datapoint (i.e. have a lower \ $L_{0}\ $ ) and fewer features over the entire dataset (i.e. have a low number of alive dictionary elements). GPT2-small has a CE loss of \ $3.139\ $ over our evaluation set." >}}

Figure 1 The authors introduce two variants: - **SAEe2e**: Trained only with KL divergence loss and sparsity penalty - **SAEe2e+ds**: Additionally includes downstream reconstruction loss to ensure activations follow similar pathways through later network layers **Key Findings:** 

1. Both e2e variants achieve better performance with fewer features compared to traditional SAEs: - Require ~55% fewer features per datapoint for the same level of performance - Need fewer total features across the dataset - Maintain or improve interpretability 

2. Geometric Analysis: 

*[See Figure 3 in the original paper]*

 - e2e SAEs learn more orthogonal features than traditional SAEs - SAEe2e+ds features are more robust across random seeds than SAEe2e - SAEe2e+ds features partially align with traditional SAE features, suggesting potential for initialization 

3. Downstream Effects: 

{{< figure src="fig2.png" caption="**Figure 2:** Reconstruction mean squared error (MSE) at later layers for our set of GPT2-small layer \ $6\ $ SAEs with similar CE loss increases (Table 1). \ $\\text{SAE}_{\\text{local}}\ $ is trained to minimize MSE at layer 6, \ $\\text{SAE}_{\\text{e2e}}\ $ was trained to match the output probability distribution, \ $\\text{SAE}_{\\text{e2e+ds}}\ $ was trained to match the output probability distribution and minimize MSE in all downstream layers." >}}

Figure 2 While SAEe2e has higher reconstruction error in downstream layers, SAEe2e+ds achieves similar downstream reconstruction to traditional SAEs while maintaining the benefits of end-to-end training. **Trade-offs:** The improved performance comes at a computational cost, with e2e variants taking 2-3.5x longer to train. However, the authors suggest this can be mitigated through: - Using fewer training samples - Reducing dictionary size - Using traditional SAEs for initialization **Significance:** This work represents an important advance in mechanistic interpretability by providing a method that more directly optimizes for functionally relevant features. The improved efficiency in feature usage (fewer features needed for same performance) suggests the method is better at identifying truly important computational components of neural networks. The paper includes extensive empirical validation across different layers of GPT2-small and Tinystories-1M, with comprehensive ablation studies and geometric analyses that support the main claims.