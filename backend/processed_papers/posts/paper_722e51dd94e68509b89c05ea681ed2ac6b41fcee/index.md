---
title: "You Are What You Eat - AI Alignment Requires Understanding How Data Shapes Structure and Generalisation"
description: "In this position paper, we argue that understanding the relation between structure in the data distribution and structure in trained models is central to AI alignment. First, we discuss how two neural..."
authors: ["Simon Pepin Lehalleur", "Jesse Hoogland", "Matthew Farrugia-Roberts", "Susan Wei", "Alexander Gietelink Oldenziel", "George Wang", "Liam Carroll", "Daniel Murfet"]
date: 2025-03-28
paper_url: "https://arxiv.org/pdf/2502.05475.pdf"
---

# You Are What You Eat - AI Alignment Requires Understanding How Data Shapes Structure and Generalisation

## Core Insight
AI alignment requires understanding how data shapes internal model structure and generalization behavior, as current alignment techniques indirectly program models by shaping training data distributions without sufficient theoretical understanding of the intermediate links (**Figure 1**).

## Key Contributions
- Identifies that neural networks with equivalent training performance can develop fundamentally different internal structures and generalization behaviors, making standard evaluation insufficient for AI safety
- Demonstrates how data distribution patterns are represented by computational structures in models, with "deeper" patterns represented by correspondingly "deeper" structures (**Figure 1**)
- Explains how Bayesian inference can prefer simpler but misaligned solutions over complex but aligned solutions when sample sizes are limited (**Figure 2**)
- Argues that alignment techniques must evolve from empirical trial-and-error to a rigorous engineering discipline grounded in understanding how structure propagates from data to models

## Methodology
The paper analyzes the pipeline from data to model behavior through the lens of singular learning theory, showing how statistical structure in training data shapes geometric structure in the loss landscape, which influences developmental structure in the learning process, ultimately determining algorithmic structure in the learned model (**Figure 1**). This framework explains why models may develop simplistic but misaligned internal algorithms even when the training data uniquely specifies aligned behavior at optimality (**Figure 2**).

## Critical Findings
- Current alignment techniques (RLHF, DPO, CAI) operate by shaping the training data distribution, which only indirectly determines model structure through effects on the optimization process (**Figure 1**)
- Bayesian inference can prefer simpler, less accurate models over accurate but more complex models, potentially causing AI systems to learn simplified and dangerous alternative solutions to alignment specifications (**Figure 2**)
- Distribution shifts between training and deployment environments may disproportionately affect alignment-related structures compared to capability-related structures, leading to the concerning possibility that "capabilities generalize further than alignment"

## Limitations & Implications
- Understanding the relationship between data, structure, and generalization may be fundamentally intractable, requiring complementary approaches like deployment guardrails and policy interventions
- Progress in alignment of superintelligent systems requires transitioning from viewing AI development as alchemy to a true engineering discipline with mathematical foundations for mechanistic interpretability and "pattern engineering"

## Figures

![1](https://assets.afspies.com/figures/722e51dd94e68509b89c05ea681ed2ac6b41fcee/fig1.png)

![2](https://assets.afspies.com/figures/722e51dd94e68509b89c05ea681ed2ac6b41fcee/fig2.png)

