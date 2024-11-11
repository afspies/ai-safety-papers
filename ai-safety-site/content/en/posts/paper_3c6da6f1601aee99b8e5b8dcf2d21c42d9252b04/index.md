---
title: "Transcoders Find Interpretable LLM Feature Circuits"
description: "A key goal in mechanistic interpretability is circuit analysis: finding sparse subgraphs of models corresponding to specific behaviors or capabilities. However, MLP sublayers make fine-grained circuit"
authors: ["Jacob Dunefsky", "Philippe Chlenski", "Neel Nanda"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2406.11944.pdf"
abstract: "A key goal in mechanistic interpretability is circuit analysis: finding sparse subgraphs of models corresponding to specific behaviors or capabilities. However, MLP sublayers make fine-grained circuit analysis on transformer-based language models difficult. In particular, interpretable features -- such as those found by sparse autoencoders (SAEs) -- are typically linear combinations of extremely many neurons, each with its own nonlinearity to account for. Circuit analysis in this setting thus either yields intractably large circuits or fails to disentangle local and global behavior. To address this we explore transcoders, which seek to faithfully approximate a densely activating MLP layer with a wider, sparsely-activating MLP layer. We introduce a novel method for using transcoders to perform weights-based circuit analysis through MLP sublayers. The resulting circuits neatly factorize into input-dependent and input-invariant terms. We then successfully train transcoders on language models with 120M, 410M, and 1.4B parameters, and find them to perform at least on par with SAEs in terms of sparsity, faithfulness, and human-interpretability. Finally, we apply transcoders to reverse-engineer unknown circuits in the model, and we obtain novel insights regarding the\"greater-than circuit\"in GPT2-small. Our results suggest that transcoders can prove effective in decomposing model computations involving MLPs into interpretable circuits. Code is available at https://github.com/jacobdunefsky/transcoder_circuits/."
tldr: "This work introduces a novel method for using transcoders to perform weights-based circuit analysis through MLP sublayers, and suggests that transcoders can prove effective in decomposing model computations involving MLPs into interpretable circuits."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_3c6da6f1601aee99b8e5b8dcf2d21c42d9252b04/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper introduces "transcoders" - a novel approach for analyzing neural network circuits in large language models (LLMs). The key innovation is that transcoders enable interpretable analysis of MLP (Multi-Layer Perceptron) layers while cleanly separating input-dependent and input-invariant behaviors. Key Points: 

1. **Problem & Motivation**: Circuit analysis in LLMs aims to find interpretable subgraphs corresponding to specific behaviors. However, analyzing MLP layers is challenging because features are typically dense combinations of many neurons. Previous approaches using sparse autoencoders (SAEs) struggle to disentangle local and global behaviors. 

2. **Transcoder Architecture**: 

*[See Figure 1 in the original paper]*

 Transcoders approximate a dense MLP layer with a wider, sparsely-activating MLP layer. The architecture includes encoder and decoder components that learn to faithfully replicate the original MLP's behavior while maintaining interpretability. 

3. **Key Advantages**: - Cleanly separates input-dependent and input-invariant terms - Enables analysis of general model behavior across all inputs - Maintains or exceeds performance compared to SAEs - Provides interpretable features 

4. **Empirical Validation**: 

*[See Figure 3 in the original paper]*

 The researchers evaluated transcoders against SAEs on models ranging from 120M to 1.4B parameters. The results show transcoders perform comparably or better than SAEs in terms of: - Sparsity - Faithfulness to original model - Human interpretability of features 

5. **Case Study - Greater Than Circuit**: 

{{< figure src="fig4.png" caption="**Figure 4:** For the three MLP10 transcoder features with the highest activation variance over the “greater-than” dataset, and for every possible YY token, we plot the DLA (the extent to which the feature boosts the output probability of YY) and the de-embedding score (an input-invariant measurement of how much YY causes the feature to fire)." >}}

Figure 4 

{{< figure src="fig5.png" caption="**Figure 5:** Left:Performance according to the probability difference metric when all but the top \ $k\ $ features or neurons in MLP10 are zero-ablated.Right:The DLA and de-embedding score for tc10[5315], which contributed negatively to the transcoder’s performance." >}}

Figure 5 The researchers demonstrated the practical utility of transcoders by analyzing how GPT-2 determines if one year is greater than another. The analysis revealed: - Clear patterns in how the model processes numerical comparisons - Sparse, interpretable features that encode year relationships - Superior interpretability compared to neuron-level analysis 

6. **Blind Case Studies**: The team conducted multiple blind case studies to validate their approach, successfully reverse-engineering various model behaviors without prior knowledge of the underlying patterns. Strengths: - Novel theoretical framework combining interpretability with practical utility - Comprehensive empirical validation - Clear separation of input-dependent and input-invariant behaviors - Scalable to larger models Limitations: - Still approximates original model computation - Doesn't fully address attention pattern computation - Limited systematic analysis of case studies Figure 1 makes the best thumbnail as it clearly illustrates the architectural difference between SAEs, transcoders, and traditional MLPs, providing an immediate visual understanding of the paper's core contribution. The work represents a significant advance in mechanistic interpretability, providing a new tool for understanding how large language models process information while maintaining the benefits of existing approaches like SAEs.