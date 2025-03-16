---
title: "Locating and Editing Factual Associations in GPT"
description: "We analyze the storage and recall of factual associations in autoregressive transformer language models, finding evidence that these associations correspond to localized, directly-editable computation..."
authors: ["Kevin Meng", "David Bau", "Alex Andonian", "Yonatan Belinkov"]
date: 2025-03-14
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/abs/2202.05262"
abstract: "We analyze the storage and recall of factual associations in autoregressive transformer language models, finding evidence that these associations correspond to localized, directly-editable computations. We first develop a causal intervention for identifying neuron activations that are decisive in a model's factual predictions. This reveals a distinct set of steps in middle-layer feed-forward modules that mediate factual predictions while processing subject tokens. To test our hypothesis that these computations correspond to factual association recall, we modify feed-forward weights to update specific factual associations using Rank-One Model Editing (ROME). We find that ROME is effective on a standard zero-shot relation extraction (zsRE) model-editing task, comparable to existing methods. To perform a more sensitive evaluation, we also evaluate ROME on a new dataset of counterfactual assertions, on which it simultaneously maintains both specificity and generalization, whereas other methods sacrifice one or another. Our results confirm an important role for mid-layer feed-forward modules in storing factual associations and suggest that direct manipulation of computational mechanisms may be a feasible approach for model editing. The code, dataset, visualizations, and an interactive demo notebook are available at https://rome.baulab.info/"
tldr: ""
added_date: 2025-03-14
bookcase_cover_src: '/posts/paper_ce641b1fe35a2a64268a305380dd404e231eec02/thumbnail.png'
math: true
katex: true
weight: 1
---

<div class="paper-meta">
  <div class="paper-meta-item">
    <span class="paper-meta-label">Authors:</span>
    <div class="paper-authors">
      Kevin Meng, David Bau, Alex Andonian, Yonatan Belinkov
    </div>
  </div>
  <div class="paper-meta-item">
    <span class="paper-meta-label">Published:</span>
    <span>Unknown</span>
  </div>
  <div class="paper-meta-item">
    <span class="paper-meta-label">Original Paper:</span>
    <a href="https://arxiv.org/abs/2202.05262" target="_blank" rel="noopener">View Paper</a>
  </div>
</div>

# Paper Summary

This paper presents a novel method for understanding and editing factual knowledge in GPT language models through targeted interventions in middle-layer MLPs. The authors combine causal tracing analysis with a rank-one editing technique (ROME) to identify and modify specific network components responsible for storing factual associations, addressing the challenge of precisely editing model knowledge while maintaining model integrity.

## Key Contributions
- Development of a causal tracing methodology that identifies specific neural activations decisive for factual predictions
- Discovery that factual associations are primarily stored in middle-layer MLP modules at the final token of subject entities
- Introduction of ROME (Rank-One Model Editing), a precise editing technique that can modify individual facts while maintaining model performance
- Creation of COUNTERFACT, a new benchmark dataset for evaluating model editing techniques across multiple dimensions

## Problem Statement and Background
Large language models like GPT have demonstrated the ability to store and recall factual knowledge, but understanding how this information is represented and how to modify it remains a significant challenge. Previous approaches to model editing have struggled to achieve both specificity (changing only the intended fact) and generalization (maintaining the change across different contexts).

{{< figure src="fig1.png" caption="**Figure 1:** Causal Tracescompute the causal effect of neuron activations by running the network twice: (a) once normally, and (b) once where we corrupt the subject token and then (c) restore selected internal activations to their clean value. (d) Some sets of activations cause the output to return to the original prediction; the light blue path shows an example of information flow. The causal impact on output probability is mapped for the effect of (e) each hidden state on the prediction, (f) only MLP activations, and (g) only attention activations." >}}

 illustrates the paper's core methodology through causal tracing, showing how the authors identify critical neural activations by running the network under normal and corrupted conditions. The figure demonstrates their three-step process: clean run, corrupted run, and corrupted-with-restoration run, revealing how specific hidden states influence factual predictions.

## Methods
The authors develop a two-part approach to understanding and editing factual knowledge. First, they use causal tracing to identify decisive neural activations by corrupting subject tokens and systematically restoring individual activations to measure their causal effect on predictions. 

{{< figure src="fig2.png" caption="**Figure 2:** Average Indirect Effectof individual model components over a sample of 1000 factual statements reveals two important sites. (a) Strong causality at a ‘late site’ in the last layers at the last token is unsurprising, but strongly causal states at an ‘early site’ in middle layers at the last subject token is a new discovery. (b) MLP contributions dominate the early site. (c) Attention is important at the late site. Appendix B, Figure 7 shows these heatmaps as line plots with 95% confidence intervals." >}}

 presents the average indirect effects of different model components, revealing two key sites: an early site in middle layers at the last subject token and a late site in final layers. This analysis shows that MLP modules play a crucial role in storing factual associations, while attention mechanisms are more important for final word prediction.

The ROME editing technique builds on these insights by treating MLP layers as key-value memories. The method involves selecting a key vector representing the subject, optimizing a value vector for the new fact, and computing a rank-one update to the weight matrix that minimizes interference with other stored knowledge.

## Results

{{< figure src="fig4.png" caption="**Figure 4:** Editing one MLP layer with ROME. To associate Space Needle with Paris, the ROME method inserts a new \$(k_{*},v_{*})\$ association into layer \$l^{*}\$ , where (a) key \$k_{*}\$ is determined by the subject and (b) value \$v_{*}\$ is optimized to select the object. (c) Hidden state at layer \$l^{*}\$ and token \$i\$ is expanded to produce (d) the key vector \$k_{*}\$ for the subject. (e) To write new value vector \$v_{*}\$ into the layer, (f) we calculate a rank-one update \$\\Lambda(C^{-1}k_{*})^{T}\$ to cause \$\\smash{\\hat{W}^{(l)}_{proj}k_{*}=v_{*}}\$ while minimizing interference with other memories stored in the layer." >}}

 provides comprehensive quantitative results comparing ROME against baseline methods. The results show that ROME achieves superior performance across multiple metrics, particularly in maintaining both specificity (75.4% neighborhood success) and generalization (96.4% paraphrase success) compared to other methods that typically sacrifice one for the other.

Figure 19 showcases qualitative examples of generated text after applying different editing methods. These examples demonstrate ROME's ability to maintain coherent and factually consistent text generation while preserving model fluency, though some cases show limitations in handling ambiguous concepts.

## Implications and Limitations
The success of ROME has significant implications for understanding how language models store and process factual knowledge, suggesting that such knowledge is more localized than previously thought. However, the method is currently limited to editing single facts at a time and requires separate edits for different phrasings of the same fact. The authors also note that while edited models can maintain consistency with new facts, they may still generate plausible but false information.

## Related Work and Future Directions
This work builds on previous research in model interpretability and editing, particularly studies of BERT and other masked language models. The authors suggest that future work could focus on scaling the approach to handle multiple simultaneous edits and exploring applications to other types of knowledge beyond factual associations. The success of ROME also opens new directions for investigating the structure of learned representations in large language models.