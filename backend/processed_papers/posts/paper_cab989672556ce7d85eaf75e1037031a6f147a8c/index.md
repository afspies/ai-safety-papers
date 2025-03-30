---
title: "Scalable Mechanistic Neural Networks"
description: "We propose Scalable Mechanistic Neural Network (S-MNN), an enhanced neural network framework designed for scientific machine learning applications involving long temporal sequences. By reformulating t..."
authors: ["Jiale Chen", "Dingling Yao", "Adeel Pervez", "Dan Alistarh", "Francesco Locatello"]
date: 2025-03-29
paper_url: "https://arxiv.org/pdf/2410.06074.pdf"
---

# Scalable Mechanistic Neural Networks

## Core Insight
Scalable Mechanistic Neural Network (S-MNN) reduces computational complexity from cubic to linear with respect to sequence length while maintaining accuracy, enabling efficient modeling of long-term dynamics as demonstrated in **Figure 1**

![Figure 1](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig1.png)

 with 4-year sea surface temperature forecasting.

## Key Contributions
- Reformulated the original MNN by eliminating slack variables and central difference constraints, reducing time complexity from O(T³) to O(T) and space complexity from O(T²) to O(T) as evidenced in **Figure 5**

![Figure 5](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig5.png)


- Developed an efficient solver leveraging banded matrix structures for GPU execution, achieving 4.9× speedup and 50% memory reduction compared to MNN dense solver as shown in **Figure 5**

![Figure 5](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig5.png)


- Demonstrated accurate modeling of complex dynamical systems including Lorenz equations (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig3.png)

) and KdV PDEs while maintaining precision comparable to the original MNN
- Successfully applied to real-world long-term climate data forecasting (**Figure 4**

![Figure 4](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig4.png)

) that the original MNN failed to handle due to resource limitations

## Methodology
S-MNN reformulates the original MNN's underlying linear system by reducing the quadratic programming problem to least squares regression and exploiting the banded structure of matrices. The solver employs efficient Cholesky decomposition and forward/backward substitution algorithms (**Figure 2**

![Figure 2](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig2.png)

) that maintain numerical stability while achieving linear time and space complexity.

## Critical Findings
- S-MNN matches the convergence rate and accuracy of the original MNN dense solver for Lorenz system discovery while reducing computation time from 36.4ms to 7.4ms per optimization step (**Figure 3**

![Figure 3](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig3.png)

)
- For KdV equation modeling, S-MNN achieves NMSE of 0.00005 (outperforming the original MNN's 0.00006) while reducing training time from 38.0 to 10.1 hours and memory usage from 3.40 to 2.19 GiB
- S-MNN can process sequence lengths up to 1,727 weeks for SST prediction with linear scaling in both runtime and memory usage, while MNN dense solver fails beyond 104 weeks (**Figure 5**

![Figure 5](https://assets.afspies.com/figures/cab989672556ce7d85eaf75e1037031a6f147a8c/fig5.png)

)

## Limitations & Implications
- Sequential for-loops in Cholesky decomposition and substitution steps limit parallelism along the time dimension, causing potential bottlenecks when batch and block sizes are small compared to time steps
- S-MNN can serve as a drop-in replacement for MNN in scientific machine learning applications, providing a practical and efficient tool for integrating mechanistic bottlenecks into neural network models of complex dynamical systems