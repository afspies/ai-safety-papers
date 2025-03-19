---
title: "Using Degeneracy in the Loss Landscape for Mechanistic Interpretability"
description: "Mechanistic Interpretability aims to reverse engineer the algorithms implemented by neural networks by studying their weights and activations. An obstacle to reverse engineering neural networks is tha"
authors: ["Lucius Bushnaq", "Jake Mendel", "Stefan Heimersheim", "Dan Braun", "Nicholas Goldowsky-Dill", "Kaarel Hänni", "Cindy Wu", "Marius Hobbhahn"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2405.10927.pdf"
abstract: "Mechanistic Interpretability aims to reverse engineer the algorithms implemented by neural networks by studying their weights and activations. An obstacle to reverse engineering neural networks is that many of the parameters inside a network are not involved in the computation being implemented by the network. These degenerate parameters may obfuscate internal structure. Singular learning theory teaches us that neural network parameterizations are biased towards being more degenerate, and parameterizations with more degeneracy are likely to generalize further. We identify 3 ways that network parameters can be degenerate: linear dependence between activations in a layer; linear dependence between gradients passed back to a layer; ReLUs which fire on the same subset of datapoints. We also present a heuristic argument that modular networks are likely to be more degenerate, and we develop a metric for identifying modules in a network that is based on this argument. We propose that if we can represent a neural network in a way that is invariant to reparameterizations that exploit the degeneracies, then this representation is likely to be more interpretable, and we provide some evidence that such a representation is likely to have sparser interactions. We introduce the Interaction Basis, a tractable technique to obtain a representation that is invariant to degeneracies from linear dependence of activations or Jacobians."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_c1bc03a045ea830894fe3b1799928c9f8c14923c/thumbnail.png'
highlight: false
math: true
katex: true
weight: 1
---

# Summary

This paper explores how degeneracy in neural networks' parameter space affects mechanistic interpretability and proposes methods to address this challenge. Here are the key points: **Core Concept: Degeneracy in Neural Networks** The authors argue that a major obstacle to reverse engineering neural networks is that many parameters don't meaningfully contribute to the network's computation. These "degenerate" parameters can obscure the network's internal structure. The paper identifies three main types of degeneracy: 

1. Linear dependence between activations in a layer 

2. Linear dependence between gradients passed back to a layer 

3. ReLUs which fire on the same subset of datapoints **Theoretical Framework** The paper builds on Singular Learning Theory (SLT) and introduces several key concepts: - Local Learning Coefficient (LLC): Measures degeneracy around specific solutions - Behavioral Loss: A new loss function that helps identify functionally equivalent parameter settings - Finite Data SLT: An extension of SLT for practical applications with finite training data **Key Contributions** 

1. **Interaction Basis** The authors introduce a novel representation called the "Interaction Basis" that is invariant to certain reparameterizations. This basis aims to reveal computational structure by removing degeneracy-based obfuscation. 

2. **Modularity-Degeneracy Connection** 

{{< figure src="fig1.png" caption="**Figure 1:** Example of a loss landscape with interacting free directions, from (Carroll, 2023), lightly edited. The loss does not change when changing $w_{1} $ alone or $w_{2} $ alone, so there are two free directions in the landscape. However, the loss does change when changing both $w_{1} $ and $w_{2} $ together, so the set of zero loss is cross-shaped rather than spanning the whole plane. Thus, despite there apparently being two free directions, the effective parameter count that characterises the dimensionality of the low loss volume is $1$ rather than $0$ . Non-interacting sets of parameters have no joined terms like this in the loss function, so their free directions always span full subspaces with each other." >}}

Figure 1 The paper presents a theoretical argument linking modularity to degeneracy, illustrated well in Figure 

1. Networks with more separated modules tend to have higher degeneracy (lower LLC), suggesting that neural networks may be biased toward modular solutions. 

3. **Practical Applications** The authors develop metrics for: - Identifying modules based on interaction strength - Measuring effective parameter count - Quantifying the independence of different network components **Significance** This work provides a theoretical framework for understanding why mechanistic interpretability is challenging and offers practical tools for addressing these challenges. The connection between modularity and degeneracy suggests that networks might naturally organize into interpretable structures. **Limitations** The authors acknowledge that: - The three identified sources of degeneracy may not be exhaustive - The interaction basis may not capture all forms of degeneracy - The theoretical framework makes some simplifying assumptions about independence **Future Directions** The paper points to several promising research directions: - Developing more complete theories of network degeneracy - Creating better tools for identifying and removing degeneracy - Understanding how degeneracy relates to network generalization This paper makes significant theoretical contributions while maintaining practical relevance to mechanistic interpretability research. The authors' framework provides new tools and perspectives for understanding neural network structure and organization.