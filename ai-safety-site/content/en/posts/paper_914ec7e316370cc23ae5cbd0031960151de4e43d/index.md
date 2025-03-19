---
title: "Extracting Finite State Machines from Transformers"
description: "Fueled by the popularity of the transformer architecture in deep learning, several works have investigated what formal languages a transformer can learn. Nonetheless, existing results remain hard to c"
authors: ["Rik Adriaensen", "Jaron Maene"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2410.06045.pdf"
abstract: "Fueled by the popularity of the transformer architecture in deep learning, several works have investigated what formal languages a transformer can learn. Nonetheless, existing results remain hard to compare and a fine-grained understanding of the trainability of transformers on regular languages is still lacking. We investigate transformers trained on regular languages from a mechanistic interpretability perspective. Using an extension of the $L^*$ algorithm, we extract Moore machines from transformers. We empirically find tighter lower bounds on the trainability of transformers, when a finite number of symbols determine the state. Additionally, our mechanistic insight allows us to characterise the regular languages a one-layer transformer can learn with good length generalisation. However, we also identify failure cases where the determining symbols get misrecognised due to saturation of the attention mechanism."
tldr: ""
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_914ec7e316370cc23ae5cbd0031960151de4e43d/thumbnail.png'
highlight: false
math: true
katex: true
weight: 1
---

# Summary

This paper investigates how transformers learn regular languages from a mechanistic interpretability perspective. The authors develop a method to extract finite state machines (Moore machines) from trained transformers and analyze how these models internally represent different states. Key contributions: - Extension of the L* algorithm to extract Moore machines from transformers - Analysis of how transformers represent states in their activation space - Characterization of which regular languages one-layer transformers can learn with good generalization - Identification of failure modes due to attention saturation The authors begin by examining different training tasks for regular languages: 

1. Next character prediction 

2. State prediction 

3. Membership prediction 

{{< figure src="fig1.png" caption="**Figure 1:** Target Moore Machine (left) and extracted Moore machine (right) from a transformer trained on $\mathcal{D}_{1} $ . The labels show whether the 0, 1 and end-of-sequence symbols are considered valid in that state." >}}

Figure 1 A key finding is that transformers learn to represent states as directions in their output layer. When a transformer successfully learns a language, sequences ending in the same state produce activation vectors aligned with a consistent direction. The authors demonstrate this through detailed analysis of the cosine similarities between activations. The paper identifies three cases where transformers can learn regular languages effectively: 

1. Languages with reset sequences 

2. Languages where occurrence of specific symbols determines the state 

3. Languages where symbols at fixed positions determine the state 

{{< figure src="fig14.png" caption="**Figure 14:** The cosine similarities between the activations on the returning suffixes and their average as well as the m-directions for the language $\mathcal{G}_{2} $ ." >}}

Figure 14 However, the authors also identify important failure modes. Due to the limitations of soft attention (Hahn's lemma), transformers eventually fail when determining symbols become too diluted by other symbols in long sequences. This is demonstrated through analysis of attention patterns: 

{{< figure src="fig23.png" caption="**Figure 23:** Cosine similarities of activations on returning suffixes for $\mathcal{C}_{2} $ ." >}}

Figure 23 

{{< figure src="fig24.png" caption="**Figure 24:** Cosine similarities of activations on returning suffixes for $\mathcal{C}_{3} $ ." >}}

Figure 24 

{{< figure src="fig25.png" caption="**Figure 25:** Cosine similarities of activations on returning suffixes for Parity." >}}

Figure 25 

*[See Figure 26 in the original paper]*

 The paper provides strong empirical evidence that one-layer transformers can reliably learn regular languages where states are determined by a finite number of symbols. This sets a tighter lower bound on transformer capabilities than previous work. The authors validate their findings through extensive experiments on multiple regular languages including: - Ones (sequences of only 1s) - First (sequences starting with 1) - Depth-bounded Dyck languages - Modulo length languages - Parity 

*[See Figure 19 in the original paper]*

 The mechanistic interpretability approach provides clear insights into both successful learning and failure modes. The paper demonstrates that extraction and analysis of finite state machines is a powerful tool for understanding transformer behavior on formal languages. The most significant figures are Figure 1 (showing the extracted vs target Moore machines), Figure 14 (demonstrating state representation in activation space), and the attention pattern figures (23-26) which reveal how transformers detect important symbols. Figure 1 would make an excellent thumbnail as it clearly illustrates the paper's core concept of extracting interpretable state machines from transformers.