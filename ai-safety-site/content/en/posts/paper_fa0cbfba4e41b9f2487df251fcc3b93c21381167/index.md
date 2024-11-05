---
title: "Detecting and Understanding Vulnerabilities in Language Models via Mechanistic Interpretability"
description: "Large Language Models (LLMs), characterized by being trained on broad amounts of data in a self-supervised manner, have shown impressive performance across a wide range of tasks. Indeed, their generat"
authors: ["Jorge García-Carrasco", "A. Maté", "Juan Trujillo"]
date: 2024-11-05
bookcase_cover_src: '/posts/paper_fa0cbfba4e41b9f2487df251fcc3b93c21381167/thumbnail.png'
weight: 1
---

This paper proposes a method to detect and understand vulnerabilities in large language models from a mechanistic interpretability perspective. The key steps are:

1. Define the task of interest and curate a dataset to elicit the desired behavior from the model. Define a metric to quantify the model's performance on the task.

2. Use activation patching experiments to identify the subset of components (the "circuit") in the model that is responsible for the task.

3. Generate adversarial samples for the task using a gradient-based optimization method that operates in the continuous embedding space. This provides insight into potential vulnerabilities and a dataset of adversarial samples.

4. Use logit attribution experiments on the adversarial samples to locate the specific components within the circuit that are affected by vulnerabilities. Apply interpretability techniques to understand the source of the vulnerabilities.

The authors showcase their method by detecting vulnerabilities in GPT-2 Small for the task of predicting 3-letter acronyms. They identify attention heads 10.10, 9.9, and 8.11 as the key components for this task. Generating adversarial samples reveals the model is prone to misclassifying samples with the letters A and S. Further analysis locates head 10.10 as the main source contributing to these misclassifications by tending to overpredict the letter Q.

The authors argue that this mechanistic interpretability approach provides a way to systematically detect, locate, and understand vulnerabilities in language models by zooming into their internal components and circuits. This could eventually help mitigate such vulnerabilities without requiring adversarial training that may cause unintended effects.

---

[Read the original paper](https://arxiv.org/pdf/2407.19842.pdf)