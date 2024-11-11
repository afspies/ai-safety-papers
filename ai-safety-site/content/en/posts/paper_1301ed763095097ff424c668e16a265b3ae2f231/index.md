---
title: "Dictionary Learning Improves Patch-Free Circuit Discovery in Mechanistic Interpretability: A Case Study on Othello-GPT"
description: "Sparse dictionary learning has been a rapidly growing technique in mechanistic interpretability to attack superposition and extract more human-understandable features from model activations. We ask a "
authors: ["Zhengfu He", "Xuyang Ge", "Qiong Tang", "Tianxiang Sun", "Qinyuan Cheng", "Xipeng Qiu"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2402.12201.pdf"
abstract: "Sparse dictionary learning has been a rapidly growing technique in mechanistic interpretability to attack superposition and extract more human-understandable features from model activations. We ask a further question based on the extracted more monosemantic features: How do we recognize circuits connecting the enormous amount of dictionary features? We propose a circuit discovery framework alternative to activation patching. Our framework suffers less from out-of-distribution and proves to be more efficient in terms of asymptotic complexity. The basic unit in our framework is dictionary features decomposed from all modules writing to the residual stream, including embedding, attention output and MLP output. Starting from any logit, dictionary feature or attention score, we manage to trace down to lower-level dictionary features of all tokens and compute their contribution to these more interpretable and local model behaviors. We dig in a small transformer trained on a synthetic task named Othello and find a number of human-understandable fine-grained circuits inside of it."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_1301ed763095097ff424c668e16a265b3ae2f231/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper presents a novel approach to discovering interpretable circuits in transformer models using dictionary learning, focusing on a case study of Othello-GPT. The work advances mechanistic interpretability by providing a patch-free alternative to traditional circuit discovery methods. Key Contributions: 

1. A new framework for circuit discovery that avoids activation patching and offers better computational efficiency 

2. A comprehensive analysis of where to apply dictionary learning in transformer architectures 

3. Detailed case studies showing how the method reveals interpretable circuits in Othello-GPT The authors propose decomposing three key components: - Word embeddings - Attention layer outputs - MLP layer outputs 

{{< figure src="fig2.png" caption="**Figure 2:** Five choices of positions to decompose via dictionary learning. Prior work has studied decomposing $X_{P1} $ , $X_{p2} $ and $X_{p5} $ , namely word embedding, MLP hidden layer and the residual stream. We claim it preferable to decompose $X_{P1} $ , $X_{P3} $ and $X_{P4} $ i.e. word representations, the output of each attention layer, and the output of each MLP layer." >}}

Figure 2 The paper demonstrates how this approach can trace information flow through the model's components. The framework allows for both end-to-end and local circuit analysis, starting from any logit or dictionary feature. A significant case study examines Othello-GPT, a transformer trained to predict legal moves in the game Othello. The authors discover several types of interpretable features: - Current move position features - Board state representations - Empty cell detectors - Legal move indicators 

{{< figure src="fig6.png" caption="**Figure 6:** (a)Board state at move 8. White player has just played on b-4 and flipped c-3, so throughout this residual stream Othello-GPT treats white tiles as mine and black as the opponents. We mainly focus on the azure-framed local state in Figure 6(b)." >}}

Figure 6 The paper provides detailed examples of circuit discovery, including: 

1. A local OV circuit computing board state 

2. QK circuits implementing attention patterns 

3. Early MLP circuits identifying flipped pieces 

*[See Figure 8 in the original paper]*

 Compared to traditional patch-based methods, this approach offers several advantages: - Linear computational complexity vs quadratic for patching - No out-of-distribution issues - Direct interpretation of feature interactions The authors acknowledge some limitations in their dictionary training: 

*[See Figure 10 in the original paper]*

 An interesting observation about Othello-GPT vs language models shows different density patterns in feature activation: 

{{< figure src="fig13.png" caption="**Figure 13:** Average L0 norm of 10,000 tokens of each dictionary. Late MLPs in Othello-GPT exhibits higher L0-norm, close to d_model = 128." >}}

Figure 13 The paper makes a compelling case for dictionary learning as a powerful tool for mechanistic interpretability, while honestly addressing current limitations and areas for future work. The approach shows promise for scaling to larger language models, though the authors note that Othello-GPT's simpler domain makes it an ideal test case for developing these methods. The methodology presented could significantly impact how we understand neural networks, offering a more systematic and computationally efficient approach to circuit discovery. The authors' careful attention to both theoretical foundations and practical implementation details makes this work particularly valuable for future research in mechanistic interpretability.