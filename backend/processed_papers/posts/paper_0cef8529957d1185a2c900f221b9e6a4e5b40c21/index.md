---
title: "Transformers Use Causal World Models in Maze-Solving Tasks"
description: "Recent studies in interpretability have explored the inner workings of transformer models trained on tasks across various domains, often discovering that these networks naturally develop highly struct..."
authors: ["Alex F Spies", "William Edwards", "Michael I. Ivanitskiy", "Adrians Skapars", "Tilman Rauker", "Katsumi Inoue", "Alessandra Russo", "Murray Shanahan"]
date: 2025-03-31
paper_url: "https://arxiv.org/pdf/2412.11867.pdf"
---

# Transformers Use Causal World Models in Maze-Solving Tasks

## Core Insight
Transformer models trained on maze-solving tasks develop causal world models (WMs) in their residual streams, where **Figure 1**

![Figure 1](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig1.png)

 demonstrates how these models construct, represent, and utilize structured internal representations of maze connectivity that causally influence their path-finding behavior.

## Key Contributions
- Identified that transformers develop causally relevant world models for maze-solving tasks, with **Figure 3**

![Figure 3](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig3.png)

 and **Figure 4**

![Figure 4](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig4.png)

 showing specialized attention heads that consolidate maze connectivity information at semicolon tokens
- Demonstrated that Sparse Autoencoders (SAEs) can effectively isolate disentangled world model features without requiring assumptions about feature form, as visualized in **Figure 6**

![Figure 6](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig6.png)

 where decision trees achieve up to 100% accuracy in identifying connection-specific features
- Discovered asymmetry in feature interventions where **Figure 9**

![Figure 9](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig9.png)

 shows activating features (up to 93% success rate) is consistently more effective than removing them for altering model behavior
- Found that models with learned positional encodings can reason about mazes with more connections in latent space than they can handle through input tokens, evidenced by successful SAE interventions in **Figure 8**

![Figure 8](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig8.png)



## Methodology
The researchers trained transformer models on maze-solving tasks using tokenized maze representations (**Figure 2**

![Figure 2](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig2.png)

), then employed two complementary approaches to identify world models: analyzing attention patterns in early layers (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig3.png)

) and training sparse autoencoders on the residual stream (**Figure 1.B**). They validated the causal nature of these representations through targeted interventions on specific features, comparing the consistency between attention-based and SAE-based analyses (**Figure 7**

![Figure 7](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig7.png)

).

## Critical Findings
- Different positional encoding schemes lead to different world model structures: Stan (learned positional embeddings) used a compositional code requiring two features per connection, while Terry (rotary positional encodings) encoded each connection as a single feature, as shown in **Figure 6**

![Figure 6](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig6.png)


- Interventions that activate features were significantly more effective than those removing features, with **Figure 9**

![Figure 9](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig9.png)

 showing success rates of 35-93% for adding connections versus 0-95% for removing them, suggesting transformers rely more on presence than absence of connectivity cues
- The Stan model could reason about mazes with more connections than encountered during training when features were activated in latent space (35% success rate), but failed completely when the same mazes were provided via input tokens, as demonstrated in **Figure 9.b**

## Limitations & Implications
- The asymmetry in intervention effectiveness (easier to activate than suppress features) suggests potential challenges for AI safety methods that rely on feature suppression rather than activation
- The findings provide a foundation for understanding how transformers might be constrained through the features they acquire during training, with implications for steering behavior in more complex AI systems