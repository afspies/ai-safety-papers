---
title: "How do language models learn facts? Dynamics, curricula and hallucinations"
description: "Large language models accumulate vast knowledge during pre-training, yet the dynamics governing this acquisition remain poorly understood. This work investigates the learning dynamics of language mode..."
authors: ["Nicolas Zucchet", "Jörg Bornschein", "Stephanie Chan", "Andrew K. Lampinen", "Razvan Pascanu", "Soham De"]
date: 2025-04-01
paper_url: "https://arxiv.org/pdf/2503.21676.pdf"
---

# How do language models learn facts? Dynamics, curricula and hallucinations

## Core Insight
Language models learn factual knowledge through a three-phase process **Figure 2**, with performance plateauing before knowledge acquisition, while imbalanced data distributions accelerate learning **Figure 4** and hallucinations emerge simultaneously with knowledge **Figure 5**.

## Key Contributions
- Identified a three-phase learning process for factual knowledge: initial distribution learning, plateau phase, and knowledge emergence, with plateau duration scaling proportionally to population size (**Figure 2**)
- Demonstrated that attention-based recall circuits develop during the plateau phase, explaining the delay in knowledge acquisition (**Figure 3**)
- Discovered that imbalanced data distributions significantly shorten the plateau phase, with optimal α values between 0.6-0.8 improving final knowledge (**Figure 4**)
- Showed that hallucinations emerge concurrently with knowledge acquisition, and fine-tuning on new data rapidly corrupts existing parametric memories (**Figure 5**)

## Methodology
The researchers used synthetic biographies with controlled attributes to isolate factual recall from other abilities, training Transformer models (44M parameters) on populations of individuals with unique attributes. Knowledge acquisition was measured through attribute loss and accuracy metrics, with attention patching experiments revealing circuit formation dynamics (**Figure 1**, **Figure 3**).

## Critical Findings
- The plateau duration scales nearly linearly with the number of individuals (R² = 0.998), indicating a statistical rather than optimization bottleneck (**Figure 2**)
- Imbalanced distributions (Zipf law, α = 0.6-0.8) reduce plateau length by up to 75% compared to uniform distributions, while dynamic "warm-up" strategies yield even greater benefits (**Figure 4**)
- Fine-tuning on new individuals causes rapid performance collapse on pre-training data (within hundreds of steps), with replay only partially mitigating this catastrophic forgetting (**Figure 5**)

## Limitations & Implications
- Findings are based on synthetic data with simplified biographies, which may not fully capture the complexity of real-world knowledge acquisition
- Results suggest practical strategies for accelerating LLM training through data scheduling and curricula, while explaining why fine-tuning is ineffective for incorporating new factual knowledge