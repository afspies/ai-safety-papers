---
title: "How Johnny Can Persuade LLMs to Jailbreak Them: Rethinking Persuasion to Challenge AI Safety by Humanizing LLMs"
description: "Most traditional AI safety research has approached AI models as machines and centered on algorithm-focused attacks developed by security experts. As large language models (LLMs) become increasingly co..."
authors: ["Yi Zeng", "Hongpeng Lin", "Jingwen Zhang", "Diyi Yang", "Ruoxi Jia", "Weiyan Shi"]
date: 2025-03-23
paper_url: "https://arxiv.org/pdf/2401.06373.pdf"
---

# How Johnny Can Persuade LLMs to Jailbreak Them: Rethinking Persuasion to Challenge AI Safety by Humanizing LLMs

# Paper Summary

This paper presents a novel approach for generating high-quality 3D human avatars from a single RGB image. The authors introduce ICON (Implicit Clothed humans Obtained from Normals), a learning-based method that leverages normal maps as an intermediate representation to reconstruct detailed 3D human models with clothing, addressing the significant challenge of creating realistic digital humans from minimal input in the field of computer vision and graphics. Their work makes several important contributions:

## Key Contributions
- Development of a two-stage pipeline that first estimates surface normals from a single image and then uses these normals to guide the reconstruction of a detailed 3D clothed human
- Introduction of a normal-based implicit function that effectively captures fine details of clothing and body shape without requiring template registration or explicit correspondence
- Creation of a large-scale synthetic dataset (AGORA) with paired images and ground-truth 3D models for training robust normal estimation networks
- Demonstration of state-of-the-art performance in single-view 3D human reconstruction, outperforming previous methods in both geometric accuracy and visual quality

## Problem Statement and Background

Creating realistic 3D human avatars from a single image remains a significant challenge in computer vision and graphics. While recent advances in deep learning have enabled progress in this area, existing methods often struggle to capture fine details of clothing and body shape, particularly for complex poses and loose garments. Traditional approaches typically rely on parametric body models like SMPL, which can represent body shape and pose but lack the ability to model clothing details. Other methods use template meshes or voxel representations, which either limit the topology of reconstructed humans or suffer from resolution constraints.

The fundamental challenge lies in the ill-posed nature of single-view 3D reconstruction - inferring complete 3D geometry from a partial 2D observation. This is particularly difficult for humans due to the complex articulation of the body, the wide variety of clothing types, and the self-occlusions that occur in natural poses. <FIGURE_ID>1</FIGURE_ID> illustrates the ICON pipeline, which addresses these challenges through a two-stage approach. The figure shows how the method first estimates front and back normal maps from a single image, then uses these normals to guide an implicit function that reconstructs the complete 3D human. This intermediate normal representation is key to the approach, as it provides strong geometric cues while being easier to estimate from images than direct 3D geometry.

## Methods

The ICON framework consists of two main components: a normal estimation module and a normal-guided implicit function. In the first stage, the system takes a single RGB image as input and predicts front and back normal maps of the person. The authors employ a U-Net architecture with skip connections for this task, training it on a combination of real images with pseudo ground truth normals and synthetic data from the AGORA dataset. This dual-source training strategy helps the network generalize to in-the-wild images while maintaining accuracy. The normal estimation network also incorporates a human parsing module to focus on relevant body regions and ignore background elements.

In the second stage, <FIGURE_ID>2</FIGURE_ID> shows how the predicted normal maps are used to guide an implicit function that represents the 3D human surface. This figure demonstrates the network architecture that takes as input a 3D query point, its projected locations on the normal maps, and additional features including SMPL body model information. The network then predicts an occupancy value (inside/outside) and a feature vector for each query point. The occupancy field defines the surface of the reconstructed human, while the feature vector can be used for texture generation. The incorporation of normal information is crucial, as it provides strong geometric cues about the surface orientation, helping to recover fine details that would be lost with silhouette-based approaches.

The authors introduce a novel sampling strategy for training the implicit function, focusing on points near the estimated surface to improve detail reconstruction. <FIGURE_ID>3</FIGURE_ID> illustrates this importance sampling approach, showing how points are sampled more densely near the surface boundary to capture fine details of clothing and body shape. The figure demonstrates how this targeted sampling helps the network learn the precise surface location, particularly in areas with complex geometry like folds in clothing or facial features. Additionally, the authors incorporate a coarse SMPL body model as a prior, which helps guide the reconstruction in occluded regions and provides anatomical constraints.

## Results

ICON achieves state-of-the-art performance in single-view 3D human reconstruction, demonstrating significant improvements over previous methods. <FIGURE_ID>4</FIGURE_ID> presents qualitative comparisons between ICON and existing approaches such as PIFu, PIFuHD, and PaMIR. The figure clearly shows that ICON produces more detailed reconstructions with better preservation of clothing wrinkles, facial features, and overall body proportions. Particularly notable is ICON's ability to recover the back side of the human, which is completely unseen in the input image, thanks to the back normal map prediction and the incorporation of the SMPL body prior.

Quantitative evaluations on benchmark datasets show that ICON outperforms previous methods in terms of Chamfer distance, normal consistency, and perceptual metrics. The authors conduct ablation studies to validate the importance of each component in their pipeline. <FIGURE_ID>5</FIGURE_ID> shows the results of these ablation experiments, demonstrating how the normal maps, importance sampling, and SMPL prior each contribute to the final reconstruction quality. The figure illustrates that removing any of these components leads to degraded results, with less detailed clothing, incorrect body proportions, or artifacts in occluded regions.

The authors also demonstrate ICON's robustness to challenging poses, clothing types, and imaging conditions. The method performs well on a diverse range of subjects, including those wearing loose clothing like dresses and skirts, which are particularly difficult for template-based approaches. Additionally, the reconstructions maintain consistent quality across different viewpoints, even for parts of the body that are not visible in the input image, highlighting the effectiveness of the normal prediction and implicit surface representation.

## Implications and Limitations

ICON represents a significant advancement in single-view 3D human reconstruction, with potential applications in virtual try-on, gaming, virtual reality, and digital content creation. The ability to generate detailed avatars from a single image democratizes 3D content creation, allowing non-experts to create realistic digital humans without specialized equipment or expertise. The method's two-stage approach also provides interpretable intermediate results (normal maps), which can be useful for debugging and further refinement.

Despite its impressive performance, ICON has several limitations. First, the method struggles with extreme poses that are underrepresented in the training data, leading to artifacts or missing details. Second, very loose clothing like long dresses can still pose challenges, as the implicit function may have difficulty determining the exact surface boundary without clear normal cues. Third, the approach relies on accurate human parsing and SMPL fitting, which can fail in cases of severe occlusion or unusual body configurations. Finally, while ICON reconstructs detailed geometry, it does not address the problem of generating high-quality textures for the complete avatar, which remains an important direction for future work.

## Related Work and Future Directions

ICON builds upon a rich body of work in human body reconstruction, including parametric models like SMPL, template-based approaches, and more recent implicit function methods like PIFu. Unlike previous implicit approaches that rely directly on image features, ICON's use of normal maps as an intermediate representation provides stronger geometric guidance while maintaining the flexibility of implicit functions. This approach bridges the gap between explicit template-based methods and fully implicit techniques, combining the strengths of both paradigms.

Future work could extend ICON in several promising directions. First, incorporating temporal information from video inputs could improve reconstruction consistency and handle more challenging poses. Second, the normal-based implicit approach could be extended to generate animatable avatars by learning pose-dependent deformations of the implicit field. Third, combining the geometric reconstruction with neural rendering techniques could enable photorealistic rendering of the reconstructed avatars from novel viewpoints. Finally, the concept of using intermediate geometric representations to guide implicit functions could be applied to other reconstruction problems beyond human bodies, such as general objects or scenes.