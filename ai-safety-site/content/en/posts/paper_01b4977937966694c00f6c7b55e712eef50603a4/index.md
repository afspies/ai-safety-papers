---
title: "Mechanistic Understanding and Mitigation of Language Model Non-Factual Hallucinations"
description: "State-of-the-art language models (LMs) sometimes generate non-factual hallucinations that misalign with world knowledge. To explore the mechanistic causes of these hallucinations, we create diagnostic"
authors: ["Lei Yu", "Meng Cao", "Jackie C. K. Cheung", "Yue Dong"]
date: 2024-11-11
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2403.18167.pdf"
abstract: "State-of-the-art language models (LMs) sometimes generate non-factual hallucinations that misalign with world knowledge. To explore the mechanistic causes of these hallucinations, we create diagnostic datasets with subject-relation queries and adapt interpretability methods to trace hallucinations through internal model representations. We discover two general and distinct mechanistic causes of hallucinations shared across LMs (Llama-2, Pythia, GPT-J): 1) knowledge enrichment hallucinations: insufficient subject attribute knowledge in lower layer MLPs, and 2) answer extraction hallucinations: failure to select the correct object attribute in upper layer attention heads. We also found these two internal mechanistic causes of hallucinations are reflected in external manifestations. Based on insights from our mechanistic analysis, we propose a novel hallucination mitigation method through targeted restoration of the LM's internal fact recall pipeline, demonstrating superior performance compared to baselines."
tldr: "A novel hallucination mitigation method is proposed through targeted restoration of the LM's internal fact recall pipeline, demonstrating superior performance compared to baselines."
added_date: 2024-11-11
bookcase_cover_src: '/posts/paper_01b4977937966694c00f6c7b55e712eef50603a4/thumbnail.png'
highlight: false
math: true
katex: true
weight: 1
---

# Summary

This paper presents a comprehensive analysis of non-factual hallucinations in large language models (LMs), identifying two distinct mechanisms through which these errors occur and proposing a novel method for mitigating them. Key Contributions: 

1. Identification of Two Hallucination Types: 

{{< figure src="fig1.png" caption="**Figure 1:** Our main finding of two non-factual hallucination mechanisms. Left (a): The early-site hallucinations are caused by lacking general knowledge of the subject in lower layer MLPs of transformer LMs – in this case, the model fails to retrieve useful information about the entity (e.g., Orica, an Australian-based multinational corporation) to generate the correct object attribute (e.g., Australia), and therefore outputs a highly irrelevant prediction (January). Right (b): The late-site hallucinations are caused by the failure of upper layer attention heads and MLPs to identify the most relevant object to the given subject and relation – in this case, the model is able to retrieve related information about the subject (e.g., Toulouse, a French city) from lower layer MLPs, but cannot distinguish the irrelevant yet strongly associated attributes (e.g., Paris) from the correct answers (e.g., Bologna/Chongqing/Atlanta). We found that these two types of hallucinations can be distinguished by the relative causal contribution to model predictions between lower and upper layer LM components." >}}

Figure 1 - Knowledge Enrichment Hallucinations: Occur when lower-layer MLPs fail to retrieve sufficient subject attribute knowledge - Answer Extraction Hallucinations: Happen when upper-layer attention heads fail to select the correct object attribute 

2. Empirical Analysis: The researchers analyzed three major LMs (Llama-2, Pythia, GPT-J) using the ParaRel dataset of cloze-style factual queries. 

{{< figure src="fig2.png" caption="**Figure 2:** Average Indirect Effect (AIE) of hidden representations produced by individual model components to non-factual hallucinations over ParaRel queries that are incorrectly answered by Llama-2-7b-chat. The relative indirect effect metric \ $\\Delta\\overline{\\text{IE}}(y,u)\ $ of distinguishing early-site and late-site hallucinations is defined as the difference between the mean AIE of 1) the hidden representations of the last relation token by upper layer attentions/MLPs (blue dashed boxes), and 2) the hidden representations of the first subject token by lower layer attentions/MLPs (red dashed boxes)." >}}

Figure 2 shows the distribution of true answer rankings across models, revealing distinct patterns for factual vs hallucinating responses. 

3. Mechanistic Investigation: 

*[See Figure 3 in the original paper]*

 Using logit lens and causal mediation analysis, they traced how information flows through the models, showing: - Early/middle layer MLPs are crucial for knowledge retrieval - Upper layer attention heads are responsible for answer selection - Different failure modes in these components lead to different types of hallucinations 

4. External Manifestations: The two hallucination types show distinct characteristics: - Answer extraction hallucinations have stronger subject-object associations - Knowledge enrichment hallucinations show higher uncertainty and lower robustness - These patterns are consistent across all tested models 

5. Mitigation Method: The authors developed a Mechanistic Hallucination Mitigation (MHM) method that: - Targets both knowledge enrichment and answer extraction mechanisms - Achieves superior performance compared to baseline methods - Maintains model utility while reducing hallucinations Results: As shown in Table 3, the MHM method outperformed existing approaches on both Natural Questions and TruthfulQA datasets, with: - Higher effectiveness on paraphrased questions - Better preservation of model performance on correctly-answered questions - Consistent improvements across all tested models The research provides valuable insights into how and why LMs hallucinate, offering both theoretical understanding and practical solutions for improving model factuality. The methodology combines rigorous analysis of internal model mechanisms with empirical validation of external behaviors. Most Important Figures: Figure 1 is crucial as it illustrates the two distinct hallucination mechanisms, making it an ideal thumbnail. Figure 3 provides detailed empirical evidence supporting the theoretical framework, while Table 3 demonstrates the practical impact of the proposed solution.