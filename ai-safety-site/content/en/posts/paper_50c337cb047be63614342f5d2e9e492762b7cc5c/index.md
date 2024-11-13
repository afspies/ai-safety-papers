---
title: "Safetywashing: Do AI Safety Benchmarks Actually Measure Safety Progress?"
description: "As artificial intelligence systems grow more powerful, there has been increasing interest in\"AI safety\"research to address emerging and future risks. However, the field of AI safety remains poorly def"
authors: ["Richard Ren", "Steven Basart", "Adam Khoja", "Alice Gatti", "Long Phan", "Xuwang Yin", "Mantas Mazeika", "Alexander Pan", "Gabriel Mukobi", "Ryan H. Kim", "Stephen Fitz", "Dan Hendrycks"]
date: 2024-11-13
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2407.21792.pdf"
abstract: "As artificial intelligence systems grow more powerful, there has been increasing interest in\"AI safety\"research to address emerging and future risks. However, the field of AI safety remains poorly defined and inconsistently measured, leading to confusion about how researchers can contribute. This lack of clarity is compounded by the unclear relationship between AI safety benchmarks and upstream general capabilities (e.g., general knowledge and reasoning). To address these issues, we conduct a comprehensive meta-analysis of AI safety benchmarks, empirically analyzing their correlation with general capabilities across dozens of models and providing a survey of existing directions in AI safety. Our findings reveal that many safety benchmarks highly correlate with upstream model capabilities, potentially enabling\"safetywashing\"-- where capability improvements are misrepresented as safety advancements. Based on these findings, we propose an empirical foundation for developing more meaningful safety metrics and define AI safety in a machine learning research context as a set of clearly delineated research goals that are empirically separable from generic capabilities advancements. In doing so, we aim to provide a more rigorous framework for AI safety research, advancing the science of safety evaluations and clarifying the path towards measurable progress."
tldr: "A comprehensive meta-analysis of AI safety benchmarks is conducted, empirically analyzing their correlation with general capabilities across dozens of models and providing a survey of existing directions in AI safety, to provide a more rigorous framework for AI safety research."
added_date: 2024-11-13
bookcase_cover_src: '/posts/paper_50c337cb047be63614342f5d2e9e492762b7cc5c/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This comprehensive paper examines the relationship between AI safety benchmarks and general model capabilities, introducing the concept of "safetywashing" - where capability improvements are misrepresented as safety advancements. The authors conduct an extensive meta-analysis across multiple safety domains and dozens of models to determine whether common safety benchmarks actually measure properties distinct from general capabilities.

Key Findings:



1. **Methodology**: The authors develop a methodology to measure correlations between safety benchmarks and general capabilities. They create a "capabilities score" using PCA on standard benchmarks like MMLU, GSM8K, and others, which explains about 75% of model performance variance.



2. **Safety Domains Analyzed**:
- **Alignment**: High correlation with capabilities (MT-Bench: 78.7%, LMSYS Arena: 62.1%)
- **Machine Ethics**: Mixed results - ETHICS shows high correlation (82.2%) while propensity measures like MACHIAVELLI show low correlation (-49.9%)
- **Bias**: Generally low correlation with capabilities (BBQ Ambiguous: -37.3%)
- **Calibration**: RMS calibration error shows low correlation (20.1%) while Brier Score shows high correlation (95.5%)
- **Adversarial Robustness**: Varies by attack type - traditional benchmarks show high correlation while jailbreak resistance shows low correlation
- **Weaponization**: Strong negative correlation with capabilities (-87.5%)



3. **Key Insights**: The paper demonstrates that many safety benchmarks (~half) inadvertently measure general capabilities rather than distinct safety properties. This enables "safetywashing" where basic capability improvements can be misrepresented as safety progress.

Important Figures:
- Figure 1 provides an excellent overview of the paper's concept, showing how safety benchmarks can be correlated with capabilities
- Figure 2 illustrates the safetywashing problem through a leaderboard example
- Figure 11 demonstrates the important distinction between RMS calibration error and Brier Score correlations
- Figure 15 shows the strong relationship between compute and capabilities scores

The authors make several recommendations:


1. Report capabilities correlations for new safety evaluations


2. Design benchmarks that are decorrelated from capabilities


3. Avoid making safety claims without demonstrating differential progress

Table 9 provides valuable context by showing the relative capabilities scores across different models, helping readers understand the landscape of current AI systems.

The paper concludes that empirical measurement, rather than intuitive arguments, should guide AI safety research. It suggests that the field needs to focus on developing safety metrics that truly measure properties independent of general capabilities.

This work provides a crucial framework for evaluating AI safety progress and helps prevent the mischaracterization of general capability improvements as safety advancements. Figure 1 would make an excellent thumbnail as it clearly illustrates the paper's core concept of safety benchmark correlation with capabilities.