---
title: "Mechanistically Interpreting a Transformer-based 2-SAT Solver: An Axiomatic Approach"
description: "Mechanistic interpretability aims to reverse engineer the computation performed by a neural network in terms of its internal components. Although there is a growing body of research on mechanistic int"
authors: ["Nils Palumbo", "Ravi Mangal", "Zifan Wang", "Saranya Vijayakumar", "Corina S. Păsăreanu", "Somesh Jha"]
date: 2024-11-13
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2407.13594.pdf"
abstract: "Mechanistic interpretability aims to reverse engineer the computation performed by a neural network in terms of its internal components. Although there is a growing body of research on mechanistic interpretation of neural networks, the notion of a mechanistic interpretation itself is often ad-hoc. Inspired by the notion of abstract interpretation from the program analysis literature that aims to develop approximate semantics for programs, we give a set of axioms that formally characterize a mechanistic interpretation as a description that approximately captures the semantics of the neural network under analysis in a compositional manner. We use these axioms to guide the mechanistic interpretability analysis of a Transformer-based model trained to solve the well-known 2-SAT problem. We are able to reverse engineer the algorithm learned by the model -- the model first parses the input formulas and then evaluates their satisfiability via enumeration of different possible valuations of the Boolean input variables. We also present evidence to support that the mechanistic interpretation of the analyzed model indeed satisfies the stated axioms."
tldr: "A set of axioms are given that formally characterize a mechanistic interpretation as a description that approximately captures the semantics of the neural network under analysis in a compositional manner and are able to reverse engineer the algorithm learned by the model."
added_date: 2024-11-13
bookcase_cover_src: '/posts/paper_432a829987174ae1da3350c32f9b9c1d502bd0de/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper presents an important theoretical framework for mechanistic interpretability of neural networks, introducing formal axioms to characterize what constitutes a valid mechanistic interpretation. The authors demonstrate their approach through a detailed case study of a Transformer model trained to solve 2-SAT problems.

Key Contributions:


1. A formal axiomatic framework for evaluating mechanistic interpretations, including:
- Prefix Equivalence (Axiom 1)
- Component Equivalence (Axiom 2) 
- Prefix Replaceability (Axiom 3)
- Component Replaceability (Axiom 4)
Plus two additional informal axioms related to compilability.



2. A comprehensive case study applying these axioms to interpret a Transformer solving 2-SAT, revealing:
- The first layer acts as a parser, converting input formulas into clause-level representations
- The second layer implements an exhaustive evaluation strategy to determine satisfiability

The analysis is particularly noteworthy for its rigorous methodology. The authors use multiple complementary techniques:

For the first layer:
- Attention pattern analysis (
{{< figure src="fig1.png" caption="**Figure 1:** Attention scores for all heads on the first sample of the test set. x-axis represents the source (key) positions and y-axis represents the destination (query) positions for the attention mechanism." >}}
Figure 1 and 
{{< figure src="fig2.png" caption="**Figure 2:** Average attention scores, grouped by source token position, for all heads, calculated over the test set. In the first layer, we further average across destination token positions restricted to positions \$4i+2\$ , where \$0\\leq i<10\$ is the clause index. For the second layer, we only consider the readout token as the destination." >}}
Figure 2 show clear periodic patterns)
- Distributional attention analysis (
{{< figure src="fig3.png" caption="**Figure 3:** Expected attention scores by position for the second token of each clause." >}}
Figure 3 demonstrates expected attention scores)

For the second layer:
- Analysis of neuron sparsity (Figure 4 shows only 34 relevant neurons)
- Detailed study of neuron activation patterns (
{{< figure src="fig5.png" caption="**Figure 5:** Output coefficients of hidden neurons computed using the composition of the weight matrix for the output layer of the MLP and the unembedding matrix projected to the SAT logit." >}}
Figure 5 reveals assignment-specific behaviors)
- Decision tree analysis (Figure 12, Figure 13, Figure 14, Figure 15 show increasingly complex interpretations)

The interpretations are validated using the proposed axioms, with detailed results showing strong performance (low ε values) for most components. The complete neuron interpretations are provided in Table 1 (decision tree based) and Table 2 (disjunction-only), showing how different neurons recognize specific satisfying assignments.

{{< figure src="fig3.png" caption="**Figure 3:** Expected attention scores by position for the second token of each clause." >}}
Figure 3 would make an excellent thumbnail as it clearly shows the structured attention patterns that form the basis for understanding the model's parsing behavior, while being visually striking and representative of the paper's technical depth.

The paper's methodology is particularly valuable as it provides a template for future mechanistic interpretability work, combining theoretical rigor (through the axioms) with practical analysis techniques. The authors acknowledge limitations, particularly regarding the generalizability of their approach to other tasks and the current reliance on human effort for analysis.

This work represents a significant step forward in making mechanistic interpretability more rigorous and systematic, while demonstrating these principles on a concrete, non-trivial example.