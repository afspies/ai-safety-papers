---
title: "Planning in a recurrent neural network that plays Sokoban"
description: "How a neural network (NN) generalizes to novel situations depends on whether it has learned to select actions heuristically or via a planning process."An investigation of model-free planning"(Guez et ..."
authors: ["Mohammad Taufeeque", "Phil Quirke", "Maximilian Li", "Chris Cundy", "Aaron David Tucker", "A. Gleave", "Adrià Garriga-Alonso"]
date: 2025-03-30
paper_url: "https://arxiv.org/pdf/2407.15421.pdf"
---

# Planning in a recurrent neural network that plays Sokoban

## Core Insight
This paper investigates a recurrent neural network (RNN) that plays Sokoban, demonstrating that it causally represents plans and performs search-like behavior, with performance improving when given extra computation time **Figure 1**

![Figure 1](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig1.png)

.

## Key Contributions
- Discovered that the RNN learns to "pace" in cycles to give itself extra computation time in complex situations, with 75% of early cycles eliminated when forced thinking steps are introduced **Figure 4**

![Figure 4](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig4.png)


- Developed linear probes that predict and causally control the agent's future actions, with box-direction probes achieving 77.8% causal effect in best-case scenarios **Figure 1**

![Figure 1](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig1.png)


- Performed model surgery enabling the convolutional network to generalize beyond its 10×10 architectural limit to solve challenging, off-distribution levels **Figure 2**

![Figure 2](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig2.png)


- Demonstrated that thinking time disproportionately helps with difficult levels, with the agent avoiding greedy strategies in favor of long-term returns **Figure 3**

![Figure 3](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig3.png)



## Methodology
The researchers trained a Deep Repeating ConvLSTM (DRC) architecture using the IMPALA reinforcement learning algorithm on 10×10 Sokoban puzzles, then analyzed its behavior through forced no-op "thinking" steps and linear probes that predict future actions. They measured plan quality by examining box-direction probe predictions **Figure 5**

![Figure 5](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig5.png)

 and performed causal interventions to test whether these representations control the agent's behavior.

## Critical Findings
- The RNN's planning capability emerges during the first 70M training steps and continues to increase for hard levels, with 8 thinking steps improving performance by ~5% on difficult puzzles **Figure 1**

![Figure 1](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig1.png)


- Box-direction probes are strongly causal (43.7% average effect) compared to agent-direction probes (7.1%), indicating the network primarily builds plans around box movements rather than agent movements **Figure 6**

![Figure 6](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig6.png)


- The quality of the agent's plan improves with thinking time, with both the length of predicted direction chains and the F1 score of plan probes increasing over time **Figure 5**

![Figure 5](https://assets.afspies.com/figures/66193a41a667b69b353e671d17510e1ee038df18/fig5.png)



## Limitations & Implications
- While evidence strongly suggests the RNN implements an online search algorithm that scales with computation, the researchers cannot completely rule out multi-step heuristics
- The small size of the network (1.29M parameters) makes it an excellent model organism for understanding planning in neural networks, with potential applications to AI alignment research on mesa-optimizers