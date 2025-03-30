---
title: "Adaptive Circuit Behavior and Generalization in Mechanistic Interpretability"
description: "Mechanistic interpretability aims to understand the inner workings of large neural networks by identifying circuits, or minimal subgraphs within the model that implement algorithms responsible for per..."
authors: ["Jatin Nainani", "Sankaran Vaidyanathan", "AJ Yeung", "Kartik Gupta", "David Jensen"]
date: 2025-03-29
paper_url: "https://arxiv.org/pdf/2411.16105.pdf"
---

# Adaptive Circuit Behavior and Generalization in Mechanistic Interpretability

## Core Insight
The paper investigates how the Indirect Object Identification (IOI) circuit in GPT-2 small generalizes across prompt variants that should theoretically break its algorithm, revealing surprising adaptability through a mechanism called "S2 Hacking" and demonstrating strong circuit reuse (**Figure 1**

![Figure 1](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig1.png)

, **Figure 7**

![Figure 7](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig7.png)

).

## Key Contributions
- Discovered that the IOI circuit generalizes surprisingly well to prompt variants where the original algorithm should fail, maintaining high performance with logit differences of 2.722 and 3.174 for DoubleIO and TripleIO variants respectively (<FIGURE_ID>Table 1</FIGURE_ID>).
- Identified "S2 Hacking," a mechanism where circuit evaluation procedures inadvertently enable the circuit to solve tasks by consistently suppressing subject tokens, visible in attention patterns of key heads (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig3.png)

, **Figure 4**

![Figure 4](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig4.png)

).
- Demonstrated strong circuit reuse with 100% node overlap and 92%/85% edge overlap for DoubleIO/TripleIO variants, only adding edges from additional input tokens (<FIGURE_ID>Table 2</FIGURE_ID>, **Figure 7**

![Figure 7](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig7.png)

).
- Found that most attention heads maintain similar functionality across prompt variants with minimal deviation in attention patterns (**Figure 2**

![Figure 2](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig2.png)

), despite significant changes in task format.

## Methodology
The researchers evaluated the base IOI circuit on two prompt variants (DoubleIO and TripleIO) where both subject and indirect object tokens are duplicated, challenging the assumptions of the original IOI algorithm (**Figure 1**

![Figure 1](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig1.png)

). They analyzed attention patterns (**Figure 2**

![Figure 2](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig2.png)

), identified the S2 Hacking mechanism (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig3.png)

), and discovered new circuits for the variants using path patching to measure causal effects of different components (**Figure 5**

![Figure 5](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig5.png)

, **Figure 6**

![Figure 6](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig6.png)

).

## Critical Findings
- The base IOI circuit significantly outperforms the full model on prompt variants with faithfulness scores of 1.285 and 2.586 for DoubleIO and TripleIO respectively, despite these variants theoretically breaking the original algorithm (<FIGURE_ID>Table 1</FIGURE_ID>).
- S2 Hacking occurs primarily through S-Inhibition head 8.6 and Induction heads 5.5 and 5.9, where the circuit shows higher confidence ratios (>1) compared to the model's ratios (~1), enabling consistent suppression of subject tokens (**Figure 4**

![Figure 4](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig4.png)

).
- The order of name appearance in prompts significantly affects performance, with both the model and circuit performing better when the indirect object appears first, due to a "first come, first serve" mechanism in head 2.2 (**Figure 8**

![Figure 8](https://assets.afspies.com/figures/ac2fa12190cb6de71fef60f04c1a499167bec938/fig8.png)

).

## Limitations & Implications
- The S2 Hacking mechanism is an artifact of circuit evaluation procedures rather than the model's actual problem-solving approach, highlighting limitations in current circuit analysis methods.
- The strong generalization of circuits through component reuse suggests that mechanistic interpretability can provide more general explanations of model behavior than previously thought, potentially enabling more robust understanding of LLM capabilities.