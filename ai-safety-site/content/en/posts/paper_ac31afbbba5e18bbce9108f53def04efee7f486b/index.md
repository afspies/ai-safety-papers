---
title: "Training Compute-Optimal Large Language Models"
description: "We investigate the optimal model size and number of tokens for training a transformer language model under a given compute budget. We find that current large language models are significantly undertra..."
authors: ["Jordan Hoffmann", "Sebastian Borgeaud", "Arthur Mensch", "Elena Buchatskaya", "Trevor Cai", "Eliza Rutherford", "Diego de Las Casas", "Lisa Anne Hendricks", "Johannes Welbl", "Aidan Clark", "Tom Hennigan", "Eric Noland", "Katie Millican", "George van den Driessche", "Bogdan Damoc", "Aurelia Guy", "Simon Osindero", "Karen Simonyan", "Erich Elsen", "Jack W. Rae", "Oriol Vinyals", "Laurent Sifre"]
date: 2025-03-14
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/abs/2203.15556"
abstract: "We investigate the optimal model size and number of tokens for training a transformer language model under a given compute budget. We find that current large language models are significantly undertrained, a consequence of the recent focus on scaling language models whilst keeping the amount of training data constant. By training over 400 language models ranging from 70 million to over 16 billion parameters on 5 to 500 billion tokens, we find that for compute-optimal training, the model size and the number of training tokens should be scaled equally: for every doubling of model size the number of training tokens should also be doubled. We test this hypothesis by training a predicted compute-optimal model, Chinchilla, that uses the same compute budget as Gopher but with 70B parameters and 4$\\times$ more more data. Chinchilla uniformly and significantly outperforms Gopher (280B), GPT-3 (175B), Jurassic-1 (178B), and Megatron-Turing NLG (530B) on a large range of downstream evaluation tasks. This also means that Chinchilla uses substantially less compute for fine-tuning and inference, greatly facilitating downstream usage. As a highlight, Chinchilla reaches a state-of-the-art average accuracy of 67.5% on the MMLU benchmark, greater than a 7% improvement over Gopher."
tldr: ""
added_date: 2025-03-14
bookcase_cover_src: '/posts/paper_ac31afbbba5e18bbce9108f53def04efee7f486b/thumbnail.png'
highlight: false
math: true
katex: true
weight: 1
---

<div class="paper-meta">
  <div class="paper-meta-item">
    <span class="paper-meta-label">Authors:</span>
    <div class="paper-authors">
      Jordan Hoffmann, Sebastian Borgeaud, Arthur Mensch, Elena Buchatskaya, Trevor Cai, Eliza Rutherford, Diego de Las Casas, Lisa Anne Hendricks, Johannes Welbl, Aidan Clark, Tom Hennigan, Eric Noland, Katie Millican, George van den Driessche, Bogdan Damoc, Aurelia Guy, Simon Osindero, Karen Simonyan, Erich Elsen, Jack W. Rae, Oriol Vinyals, Laurent Sifre
    </div>
  </div>
  <div class="paper-meta-item">
    <span class="paper-meta-label">Published:</span>
    <span>Unknown</span>
  </div>
  <div class="paper-meta-item">
    <span class="paper-meta-label">Original Paper:</span>
    <a href="https://arxiv.org/abs/2203.15556" target="_blank" rel="noopener">View Paper</a>
  </div>
</div>

# Summary

This paper discusses Training Compute-Optimal Large Language Models.

The authors propose a novel approach to address important challenges in the field.

{{< figure src="fig1.png" caption="**Figure 1:** Overlaid predictions.We overlay the predictions from our three different approaches, along with projections from Kaplan et al. (2020). We find that all three methods predict that current large models should be substantially smaller and therefore trained much longer than is currently done. In Figure A3, we show the results with the predicted optimal tokens plotted against the optimal number of parameters for fixed FLOP budgets.Chinchilla outperforms Gopher and the other large models (see Section 4.2)." >}}
Figure 1 shows the main architecture of their proposed method.

Their experiments demonstrate significant improvements over previous approaches as shown in 
{{< figure src="fig2.png" caption="**Figure 2:** Training curve envelope.On theleftwe show all of our different runs. We launched a range of model sizes going from 70M to 10B, each for four different cosine cycle lengths. From these curves, we extracted the envelope of minimal loss per FLOP, and we used these points to estimate the optimal model size (center) for a given compute budget and the optimal number of training tokens (right). In green, we show projections of optimal model size and training token count based on the number of FLOPs used to train Gopher ( \$5.76\\times 10^{23}\$ )." >}}
Figure 2.
