---
title: "Enhancing Automated Interpretability with Output-Centric Feature Descriptions"
description: "Automated interpretability pipelines generate natural language descriptions for the concepts represented by features in large language models (LLMs), such as plants or the first word in a sentence. Th..."
authors: ["Yoav Gur-Arieh", "Roy Mayan", "Chen Agassy", "Atticus Geiger", "Mor Geva"]
date: 2025-03-31
paper_url: "https://arxiv.org/pdf/2501.08319.pdf"
---

# Enhancing Automated Interpretability with Output-Centric Feature Descriptions

## Core Insight
Current automated interpretability pipelines fail to capture how features causally affect model outputs; this paper introduces output-centric feature description methods that, when combined with input-centric approaches, provide more comprehensive feature understanding and can even revive "dead" features (**Figure 1**

![Figure 1](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig1.png)

).

## Key Contributions
- Proposed two efficient output-centric methods (VocabProj and TokenChange) for generating feature descriptions that better capture features' causal effects on model outputs, requiring only 1-2 inference passes compared to costly input-based methods (**Figure 1**

![Figure 1](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig1.png)

).
- Developed a two-faceted evaluation framework that assesses feature descriptions through both input-based and output-based metrics, revealing that different methods excel at different aspects of feature description (**Figure 2**

![Figure 2](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig2.png)

).
- Demonstrated that ensembles combining input- and output-centric methods consistently outperform single methods, with improvements of 6-10% on both metrics for Gemma-2 features (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig3.png)

).
- Showed that output-centric descriptions can efficiently discover inputs that activate 62% of residual "dead" features in Gemma-2 that had no previously identified activating inputs.

## Methodology
The authors introduce two output-centric methods: VocabProj, which projects feature vectors to vocabulary space to identify promoted/suppressed tokens, and TokenChange, which measures token probability changes when amplifying features (**Figure 1**

![Figure 1](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig1.png)

). These methods are evaluated against the standard MaxAct approach using both input-based metrics (whether descriptions identify activating inputs) and output-based metrics (whether descriptions capture the feature's effect on model outputs) across multiple LLMs and feature types (**Figure 2**

![Figure 2](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig2.png)

).

## Critical Findings
- MaxAct outperforms output-centric methods on input-based evaluations (by up to 30%), while output-centric methods consistently perform better on output-based evaluations, confirming that these approaches capture complementary aspects of features (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig3.png)

).
- Ensembles combining all three methods (MaxAct, VocabProj, TokenChange) achieved the best overall performance, with Ensemble Raw performing better on input-based evaluations and Ensemble Concat excelling on output-based evaluations (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig3.png)

).
- Output-based performance is substantially lower for MLP features (45-50 points) compared to residual features (~66 points), suggesting MLP layers introduce more gradual changes that are harder to steer (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/0c9b7ee426606034b8a2253e0efc598ce3c5423e/fig3.png)

).

## Limitations & Implications
- The output-based evaluation is noisy, requiring large feature samples and multiple prompts; output-centric methods are also sensitive to prompt choice and tied to the model's vocabulary, limiting their ability to describe features not easily expressed with words.
- The approach enables more efficient automated interpretability at scale, particularly for model steering applications, and provides a framework for understanding features through both their activating inputs and their effects on model outputs.