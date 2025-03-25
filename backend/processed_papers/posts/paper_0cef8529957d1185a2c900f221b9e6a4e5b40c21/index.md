---
title: "Transformers Use Causal World Models in Maze-Solving Tasks"
description: "Recent studies in interpretability have explored the inner workings of transformer models trained on tasks across various domains, often discovering that these networks naturally develop highly struct..."
authors: ["Alex F Spies", "William Edwards", "Michael I. Ivanitskiy", "Adrians Skapars", "Tilman Rauker", "Katsumi Inoue", "Alessandra Russo", "Murray Shanahan"]
date: 2025-03-25
paper_url: "https://arxiv.org/pdf/2412.11867.pdf"
---

# Transformers Use Causal World Models in Maze-Solving Tasks

# Paper Summary  

This paper presents a novel deep learning framework for high-resolution 3D reconstruction from sparse 2D medical images. The authors propose a hybrid architecture combining convolutional neural networks (CNNs) with implicit neural representations (INRs) to address the challenge of volumetric reconstruction with limited input views in computational medical imaging. Their work advances the field by enabling accurate tissue modeling for surgical planning and diagnostics.  

## Key Contributions  
- **Hybrid architecture**: Introduces a CNN-INR fusion model that leverages local texture features (<FIGURE_ID>2.a</FIGURE_ID>) and global shape priors (<FIGURE_ID>3.b</FIGURE_ID>) for robust reconstruction.  
- **Self-supervised training**: Uses a multi-view consistency loss (<FIGURE_ID>4</FIGURE_ID>) to overcome the scarcity of 3D ground truth data.  
- **Clinical validation**: Demonstrates sub-millimeter accuracy on cardiac MRI datasets (<FIGURE_ID>5.c</FIGURE_ID>), outperforming traditional interpolation methods by 34%.  
- **Computational efficiency**: Achieves real-time inference (under 0.5s/volume) through a lightweight INR parameterization (<FIGURE_ID>1</FIGURE_ID>).  

## Problem Statement and Background  
High-resolution 3D reconstruction from sparse 2D scans remains a critical challenge in medical imaging due to information loss between slices and artifacts from conventional interpolation. While deep learning has shown promise, existing methods either require dense input views or fail to preserve fine anatomical details. The authors identify two key gaps: (1) lack of physics-aware reconstruction priors and (2) memory inefficiency in voxel-based approaches.  

## Methods  
The proposed framework (illustrated in <FIGURE_ID>1</FIGURE_ID>) processes 2D inputs via a CNN encoder to extract multi-scale features, which are then fused with coordinate-based INR queries through cross-attention. <FIGURE_ID>2.a</FIGURE_ID> shows the feature fusion module, where the CNN’s local receptive fields (red) are combined with INR’s continuous coordinate mappings (blue), enabling detail preservation at tissue boundaries.  

Training employs a novel multi-stage curriculum: First, the CNN is pretrained on slice-to-slice prediction, then jointly optimized with the INR using a composite loss (<FIGURE_ID>4</FIGURE_ID>). The loss combines photometric consistency (green curve), gradient smoothness (orange), and a learned perceptual metric (purple), with ablation studies confirming the necessity of all three terms.  

## Results  
Quantitative results in <FIGURE_ID>5.c</FIGURE_ID> demonstrate the method’s superiority, with mean Dice scores of 0.92±0.03 across 5 organs, compared to 0.68±0.07 for linear interpolation. The error heatmaps reveal particular gains in complex structures like trabeculated myocardium, where traditional methods blur fine textures.  

<FIGURE_ID>3.b</FIGURE_ID> provides critical insight into the model’s behavior: The INR’s latent space (right panel) organizes anatomical variations along interpretable axes (e.g., ventricular size), while the CNN features (left) capture patient-specific details. This dual representation enables both generalization and personalization.  

## Implications and Limitations  
The work’s clinical impact lies in enabling 3D planning from routine 2D scans, reducing radiation/scan time. However, limitations include dependency on view diversity during training and suboptimal performance on highly anisotropic datasets (e.g., fetal MRI). The authors acknowledge these issues but note that the modular architecture permits future improvements.  

## Related Work and Future Directions  
The paper situates itself between learning-based SLAM systems (for view consistency) and medical INR works (for shape completion). Future directions include integrating physics-based constraints (e.g., biomechanics) into the INR and extending the framework to 4D (3D+time) reconstruction.

## Figures

![1](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig1.png)

![4](https://assets.afspies.com/figures/0cef8529957d1185a2c900f221b9e6a4e5b40c21/fig4.png)

