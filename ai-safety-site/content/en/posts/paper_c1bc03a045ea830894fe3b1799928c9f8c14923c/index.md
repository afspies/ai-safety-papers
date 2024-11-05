---
title: "Using Degeneracy in the Loss Landscape for Mechanistic Interpretability"
description: "Mechanistic Interpretability aims to reverse engineer the algorithms implemented by neural networks by studying their weights and activations. An obstacle to reverse engineering neural networks is tha"
authors: ["Lucius Bushnaq", "Jake Mendel", "Stefan Heimersheim", "Dan Braun", "Nicholas Goldowsky-Dill", "Kaarel Hänni", "Cindy Wu", "Marius Hobbhahn"]
date: 2024-11-05
bookcase_cover_src: '/posts/paper_c1bc03a045ea830894fe3b1799928c9f8c14923c/thumbnail.png'
weight: 1
---

The paper discusses the concept of degeneracy in neural network parameterizations and its impact on mechanistic interpretability. The key points are:

1. Neural networks tend to have many degenerate parameters that do not affect the computation, obfuscating the network's internal structure and hindering interpretability.

2. Singular learning theory suggests that networks are biased towards more degenerate solutions that generalize better, with a lower local learning coefficient (LLC).

3. The paper identifies three sources of degeneracy in neural networks:
   a. Linear dependence between activations in a layer
   b. Linear dependence between gradients passed back to a layer
   c. Neurons firing on the same subset of data points (synchronized nonlinearities)

4. Degeneracy reduces the effective parameter count of the network. Removing degeneracies by finding a parameterization-invariant representation can lead to sparser interactions and improved interpretability.

5. The paper argues that modularity in networks may contribute to degeneracy, as non-interacting modules have independent degeneracies that sum up, lowering the overall LLC.

6. The Interaction Basis technique is proposed to obtain a parameterization-invariant representation by removing degeneracies from linear dependence in activations or Jacobians.

The paper aims to provide a theoretical foundation for mechanistic interpretability by understanding and exploiting the degeneracy in neural network parameterizations.

---

[Read the original paper](https://arxiv.org/pdf/2405.10927.pdf)