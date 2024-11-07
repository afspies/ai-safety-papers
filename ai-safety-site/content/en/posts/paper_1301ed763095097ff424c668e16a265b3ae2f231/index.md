---
title: "Dictionary Learning Improves Patch-Free Circuit Discovery in Mechanistic Interpretability: A Case Study on Othello-GPT"
description: "Sparse dictionary learning has been a rapidly growing technique in mechanistic interpretability to attack superposition and extract more human-understandable features from model activations. We ask a "
authors: ["Zhengfu He", "Xuyang Ge", "Qiong Tang", "Tianxiang Sun", "Qinyuan Cheng", "Xipeng Qiu"]
abstract: "Sparse dictionary learning has been a rapidly growing technique in mechanistic interpretability to attack superposition and extract more human-understandable features from model activations. We ask a simple question: can we improve the performance of circuit discovery by using dictionary learning?"
publication_date: "2024-02-25"
added_date: "2024-11-05"
venue: "arXiv"
paper_url: "https://arxiv.org/pdf/2402.12201.pdf"
date: 2024-11-05
bookcase_cover_src: '/posts/paper_1301ed763095097ff424c668e16a265b3ae2f231/thumbnail.png'
weight: 1
---

# Summary
This paper proposes a novel framework for discovering interpretable circuits in Transformer models using sparse dictionary learning. The key ideas are:

- Train sparse dictionaries to decompose the outputs of each module in the Transformer (word embeddings, attention outputs, and MLP outputs) into more interpretable, monosemantic features.

- Exploit the linear structure of the Transformer to trace how higher-level dictionary features are composed from lower-level ones across layers, allowing circuits to be identified in a patch-free manner.

- Demonstrate the framework on an Othello prediction model, revealing circuits that compute the board state, identify legal moves, recognize flipped pieces, and implement different attention patterns like "attending to my moves" vs "attending to opponent's moves".

- Analyze the computational complexity showing their approach is more efficient than patch-based methods and does not suffer from out-of-distribution issues.

- Discuss limitations like inability to fully interpret the relative strengths of attention scores and approximate nature of attributing MLP features.

The paper presents a promising direction for mechanistic interpretability of neural networks by combining sparse dictionary learning with circuit tracing enabled by the Transformer's linear structure. The Othello case study showcases the framework's ability to discover human-understandable circuits underlying the model's behavior.

---

[Read the original paper](https://arxiv.org/pdf/2402.12201.pdf)