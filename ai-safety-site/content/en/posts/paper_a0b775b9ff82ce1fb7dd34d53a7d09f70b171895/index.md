---
title: "How to use and interpret activation patching"
description: "Activation patching is a popular mechanistic interpretability technique, but has many subtleties regarding how it is applied and how one may interpret the results. We provide a summary of advice and b"
authors: ["Stefan Heimersheim", "Neel Nanda"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2404.15255.pdf"
abstract: "Activation patching is a popular mechanistic interpretability technique, but has many subtleties regarding how it is applied and how one may interpret the results. We provide a summary of advice and best practices, based on our experience using this technique in practice. We include an overview of the different ways to apply activation patching and a discussion on how to interpret the results. We focus on what evidence patching experiments provide about circuits, and on the choice of metric and associated pitfalls."
tldr: "What evidence patching experiments provide about circuits, and on the choice of metric and associated pitfalls, are focused on."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_a0b775b9ff82ce1fb7dd34d53a7d09f70b171895/thumbnail.png'
highlight: false
math: true
katex: true
weight: 1
---

# Summary

This paper provides a comprehensive guide to activation patching, an important mechanistic interpretability technique for understanding neural networks. The authors, Stefan Heimersheim and Neel Nanda, draw from extensive practical experience to outline best practices and common pitfalls. Key aspects covered include: **

1. Core Concepts** - Activation patching involves replacing internal activations of a neural network during execution to understand how different components contribute to model behavior - The technique is more targeted than simple ablation, allowing researchers to isolate specific behaviors and circuits - The authors illustrate the concept with an example of analyzing how a model completes "The Colosseum is in" → "Rome", demonstrating how different patching approaches can isolate language processing vs factual recall **

2. Types of Patching** - *Denoising* (clean → corrupt): Tests if patched activations are sufficient to restore model behavior - *Noising* (corrupt → clean): Tests if patched activations are necessary to maintain behavior - The paper emphasizes these approaches are not symmetric and provide different insights **

3. Circuit Analysis Example** 

{{< figure src="fig1.png" caption="**Figure 1:** Toy 'Nobel Peace Price' circuit" >}}

Figure 1 The authors present a detailed walkthrough of analyzing a "Nobel Peace Prize" circuit, showing how different patching approaches reveal different aspects of the model's behavior. This example effectively demonstrates how components like attention heads and neurons work together to produce model outputs. **

4. Metrics and Measurement** 

{{< figure src="fig2.png" caption="**Figure 2:** Illustration of different metrics for an example patching experiment with GPT-2 medium." >}}

Figure 2 The paper provides a thorough analysis of different metrics for evaluating patching results: - Logit difference (recommended as most reliable) - Logarithmic probability - Raw probability - Accuracy/rank metrics The authors emphasize that metric choice significantly impacts interpretation and recommend using multiple metrics while being particularly careful with discrete or overly sharp metrics. **

5. Best Practices** - Start with low-granularity patching before increasing granularity - Consider multiple corrupted prompts to test different aspects of model behavior - Use continuous metrics rather than discrete ones for exploratory work - Be aware of backup behaviors and negative components that can complicate analysis **

6. Common Pitfalls** - Over-relying on binary metrics that mask partial effects - Not considering the full range of model behaviors - Misinterpreting results due to backup circuits or negative components - Using metrics that saturate or fail to capture important behavioral changes The paper is particularly valuable for practitioners as it combines theoretical understanding with practical advice gained from extensive experience with the technique. The authors' emphasis on careful metric selection and interpretation makes this a crucial resource for anyone working in mechanistic interpretability. The included figures effectively illustrate the concepts, with Figure 2 being particularly insightful as it demonstrates how different metrics can lead to varying interpretations of the same underlying behavior.