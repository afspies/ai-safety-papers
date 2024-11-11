---
title: "Mechanistic Unlearning: Robust Knowledge Unlearning and Editing via Mechanistic Localization"
description: "Methods for knowledge editing and unlearning in large language models seek to edit or remove undesirable knowledge or capabilities without compromising general language modeling performance. This work"
authors: ["P. Guo", "Aaquib Syed", "Abhay Sheshadri", "Aidan Ewart", "G. Dziugaite"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2410.12949.pdf"
abstract: "Methods for knowledge editing and unlearning in large language models seek to edit or remove undesirable knowledge or capabilities without compromising general language modeling performance. This work investigates how mechanistic interpretability -- which, in part, aims to identify model components (circuits) associated to specific interpretable mechanisms that make up a model capability -- can improve the precision and effectiveness of editing and unlearning. We find a stark difference in unlearning and edit robustness when training components localized by different methods. We highlight an important distinction between methods that localize components based primarily on preserving outputs, and those finding high level mechanisms with predictable intermediate states. In particular, localizing edits/unlearning to components associated with the lookup-table mechanism for factual recall 1) leads to more robust edits/unlearning across different input/output formats, and 2) resists attempts to relearn the unwanted information, while also reducing unintended side effects compared to baselines, on both a sports facts dataset and the CounterFact dataset across multiple models. We also find that certain localized edits disrupt the latent knowledge in the model more than any other baselines, making unlearning more robust to various attacks."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_23a921483746b8b3c828bd601f54d485bec32014/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper presents "mechanistic unlearning," a novel approach for robustly removing or editing knowledge in large language models (LLMs) by targeting specific model components identified through mechanistic interpretability. Key Contributions: - Introduces a more precise and effective method for knowledge editing/unlearning that focuses on modifying the "fact lookup" (FLU) mechanism rather than just output-focused components - Demonstrates superior robustness against prompt variations and relearning attempts compared to existing methods - Provides evidence that targeting FLU mechanisms leads to better disruption of latent knowledge while maintaining general model capabilities 

{{< figure src="fig1.png" caption="**Figure 1:** High level depiction of mechanistic unlearning. We localize components responsible for fact extraction/enrichment and modify their weights to change the associations, in order to target internal latent representations rather than targeting the output. Graph inspired by Nanda et al. (2023)." >}}

Figure 1 The core insight is the distinction between two types of model components: 

1. Fact lookup (FLU) mechanisms: MLPs that enrich the latent stream with subject attributes 

2. Fact extraction mechanisms: Components that transform latent knowledge into output formats The authors show that previous output-tracing (OT) methods like causal tracing primarily target extraction mechanisms, which makes edits less robust since the underlying knowledge remains accessible through alternative prompting or extraction methods. In contrast, their mechanistic approach targets the FLU components where the knowledge is first incorporated into the model's representations. The methodology was evaluated on two datasets: 

1. Sports Facts dataset: Testing unlearning of athlete-sport associations 

2. CounterFact dataset: Testing fact editing across multiple models 

{{< figure src="fig2.png" caption="**Figure 2:** (Left) Retraining basketball-unlearned models with two athletes in the forget set, for ten iterations. (Right) Retraining models that have had 16 athlete-sport associations replaced with Golf as the athletes’ associated sport, with two athletes in the forget set, for ten iterations. The y-axis represents the normal accuracy on the forget set. Low-resource relearning of athletes demonstrates that using manual interpretability makes edits significantly more robust to relearning." >}}

Figure 2 The results demonstrate several key advantages of mechanistic unlearning: - Better generalization across different input/output formats - Improved resistance to relearning attempts - Reduced unintended side effects on general language modeling capabilities 

{{< figure src="fig4.png" caption="**Figure 4:** Probe accuracy (combined over all three sports) on the athlete golf-injected models across layers. The ‘Localized AP’, ‘Localized CT’, and ‘Random’ lines are overlapping." >}}

Figure 4 The authors provide extensive empirical validation through: - Standard evaluation metrics (Tables 1-3) - Adversarial relearning experiments - Latent knowledge analysis using probing - Weight masking studies to quantify edit sizes 

{{< figure src="fig3.png" caption="**Figure 3:** Retraining counterfact-edited models with all forgotten facts, for twenty iterations. (Left) The y-axis represents the normal accuracy on the forget set. (Right) The y-axis represents the Multiple Choice Formatted question accuracy on the forget set." >}}

Figure 3 The research makes a strong case that successful knowledge editing requires targeting the mechanisms where knowledge is initially encoded, rather than just modifying how that knowledge is expressed in outputs. This insight could have important implications for developing more reliable methods of controlling and updating LLM knowledge. The paper's findings challenge previous conclusions about the ineffectiveness of localization for model editing, showing that the success depends critically on which components are targeted and how they're identified. This suggests mechanistic interpretability can play a valuable role in developing more precise and robust model modification techniques. The work has significant implications for AI safety and control, offering a more principled approach to removing or modifying undesirable model knowledge while preserving desired capabilities.