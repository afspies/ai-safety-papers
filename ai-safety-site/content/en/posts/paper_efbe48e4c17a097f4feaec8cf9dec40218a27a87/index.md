---
title: "Interpreting Attention Layer Outputs with Sparse Autoencoders"
description: "Decomposing model activations into interpretable components is a key open problem in mechanistic interpretability. Sparse autoencoders (SAEs) are a popular method for decomposing the internal activati"
authors: ["Connor Kissane", "Robert Krzyzanowski", "J. Bloom", "Arthur Conmy", "Neel Nanda"]
date: 2024-11-13
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2406.17759.pdf"
abstract: "Decomposing model activations into interpretable components is a key open problem in mechanistic interpretability. Sparse autoencoders (SAEs) are a popular method for decomposing the internal activations of trained transformers into sparse, interpretable features, and have been applied to MLP layers and the residual stream. In this work we train SAEs on attention layer outputs and show that also here SAEs find a sparse, interpretable decomposition. We demonstrate this on transformers from several model families and up to 2B parameters. We perform a qualitative study of the features computed by attention layers, and find multiple families: long-range context, short-range context and induction features. We qualitatively study the role of every head in GPT-2 Small, and estimate that at least 90% of the heads are polysemantic, i.e. have multiple unrelated roles. Further, we show that Sparse Autoencoders are a useful tool that enable researchers to explain model behavior in greater detail than prior work. For example, we explore the mystery of why models have so many seemingly redundant induction heads, use SAEs to motivate the hypothesis that some are long-prefix whereas others are short-prefix, and confirm this with more rigorous analysis. We use our SAEs to analyze the computation performed by the Indirect Object Identification circuit (Wang et al.), validating that the SAEs find causally meaningful intermediate variables, and deepening our understanding of the semantics of the circuit. We open-source the trained SAEs and a tool for exploring arbitrary prompts through the lens of Attention Output SAEs."
tldr: "The mystery of why models have so many seemingly redundant induction heads is explored, SAEs are used to motivate the hypothesis that some are long-prefix whereas others are short-prefix, and SAEs find a sparse, interpretable decomposition are shown."
added_date: 2024-11-13
bookcase_cover_src: '/posts/paper_efbe48e4c17a097f4feaec8cf9dec40218a27a87/thumbnail.png'
highlight: false
math: true
katex: true
weight: 1
---

# Summary

This paper presents a novel approach to interpreting attention mechanisms in transformer models using Sparse Autoencoders (SAEs). The authors demonstrate that SAEs can effectively decompose attention layer outputs into interpretable features, providing new insights into how attention layers process information.

{{< figure src="fig1.png" caption="Overview. We train Sparse Autoencoders (SAEs) on \$\\textbf{z}_{\\text{cat}}\$ , the attention layer outputs pre-linear, concatenated across all heads. The SAEs extract linear directions that correspond to concepts in the model, giving us insight into what attention layers learn in practice. Further, we uncover what information was used to compute these features with direct feature attribution (DFA, Section 2)." >}}
Figure 1

The key contributions include:



1. **Novel Application of SAEs**: The authors show that SAEs can successfully decompose attention layer outputs into sparse, interpretable features across multiple model families up to 2B parameters. They train SAEs on the concatenated outputs of attention heads before the final linear projection.



2. **Feature Families**: Through qualitative analysis, they identify three main families of attention features:
- Long-range context features
- Short-range context features 
- Induction features



3. **Polysemanticity Analysis**: The research reveals that approximately 90% of attention heads in GPT-2 Small are polysemantic (performing multiple unrelated tasks), challenging previous approaches to interpreting individual attention heads.

{{< subfigures caption="Specificity plot [4] (a) which compares the distribution of the board induction feature activations to the activation of our proxy. The expected value plot (b) shows distribution of feature activations weighted by activation level [4], compared to the activation of the proxy. Note red is stacked on top of blue, where blue represents examples that our proxy identified as board induction. We notice high specificity above the weakest feature activations." >}}
{{< subfigure src="fig2_a.png" caption="(a)" >}}{{< subfigure src="fig2_b.png" caption="(b)" >}}
{{< /subfigures >}}
Figure 2



4. **Long-Prefix Induction**: The authors make progress on understanding why models have multiple seemingly redundant induction heads, showing that some specialize in "long-prefix" vs "short-prefix" induction patterns.

{{< subfigures caption="Two lines of evidence that 5.1 specializes in long prefix induction, while 5.5 primarily does short prefix induction. In (a) we see that 5.1’s induction score [54] sharply increases from less than 0.3 to over 0.7 as we transition to long prefix lengths, while 5.5 already starts at 0.7 for short prefixes. In (b) we see that intervening on examples of long prefix induction from the training distribution causes 5.1 to essentially stop attending to that token, while 5.5 continues to show an induction attention pattern." >}}
{{< subfigure src="fig4_a.png" caption="(a)" >}}{{< subfigure src="fig4_b.png" caption="(b)" >}}
{{< /subfigures >}}
Figure 4

A particularly significant contribution is their analysis of the Indirect Object Identification (IOI) circuit, where they discover that the "positional signal" is determined by whether duplicate names appear before or after "and" tokens. This provides concrete evidence of how the model processes relative positioning information.

Figure 14

The methodology includes several novel techniques:
- Weight-based head attribution
- Direct feature attribution (DFA)
- Recursive Direct Feature Attribution (RDFA)

Figure 16

The authors validate their findings through multiple independent lines of evidence and provide extensive evaluations across different model scales. They also release their trained SAEs and visualization tools to support further research.

The paper's limitations are thoughtfully addressed, including the focus on attention outputs rather than the full transformer architecture and the reliance on qualitative investigations and human judgment in some analyses.

This work represents a significant advance in mechanistic interpretability, providing both theoretical insights and practical tools for understanding how attention mechanisms process information in transformer models.

The most important figures are:
- Figure 1: Overview of the SAE approach
- Figure 2: Specificity analysis of induction features
- Figure 4: Evidence for long-prefix specialization
- Figures 14 & 16: IOI circuit analysis results

Figure 1 would make the best thumbnail as it clearly illustrates the paper's core concept of using SAEs to interpret attention layer outputs.