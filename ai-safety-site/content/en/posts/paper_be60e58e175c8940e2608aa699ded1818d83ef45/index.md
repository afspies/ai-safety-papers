---
title: "Towards evaluations-based safety cases for AI scheming"
description: "We sketch how developers of frontier AI systems could construct a structured rationale -- a 'safety case' -- that an AI system is unlikely to cause catastrophic outcomes through scheming. Scheming is "
authors: ["Mikita Balesni", "Marius Hobbhahn", "David Lindner", "Alexander Meinke", "Tomasz Korbak", "Joshua Clymer", "Buck Shlegeris", "J'er'emy Scheurer", "Rusheb Shah", "Nicholas Goldowsky-Dill", "Dan Braun", "Bilal Chughtai", "Owain Evans", "Daniel Kokotajlo", "Lucius Bushnaq"]
date: 2024-11-17
publication_date: Unknown
venue: ""
paper_url: "https://arxiv.org/pdf/2411.03336.pdf"
abstract: "We sketch how developers of frontier AI systems could construct a structured rationale -- a 'safety case' -- that an AI system is unlikely to cause catastrophic outcomes through scheming. Scheming is a potential threat model where AI systems could pursue misaligned goals covertly, hiding their true capabilities and objectives. In this report, we propose three arguments that safety cases could use in relation to scheming. For each argument we sketch how evidence could be gathered from empirical evaluations, and what assumptions would need to be met to provide strong assurance. First, developers of frontier AI systems could argue that AI systems are not capable of scheming (Scheming Inability). Second, one could argue that AI systems are not capable of posing harm through scheming (Harm Inability). Third, one could argue that control measures around the AI systems would prevent unacceptable outcomes even if the AI systems intentionally attempted to subvert them (Harm Control). Additionally, we discuss how safety cases might be supported by evidence that an AI system is reasonably aligned with its developers (Alignment). Finally, we point out that many of the assumptions required to make these safety arguments have not been confidently satisfied to date and require making progress on multiple open research problems."
tldr: "This report proposes three arguments that safety cases could use in relation to scheming, and sketches how evidence could be gathered from empirical evaluations, and what assumptions would need to be met to provide strong assurance."
added_date: 2024-11-17
bookcase_cover_src: '/posts/paper_be60e58e175c8940e2608aa699ded1818d83ef45/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

This paper presents a framework for developing safety cases to address the risk of AI systems engaging in "scheming" - the covert pursuit of misaligned goals. The authors, primarily from Apollo Research and other institutions, propose structured arguments and evaluation methods to demonstrate that AI systems are unlikely to cause catastrophic outcomes through scheming behavior.

The paper introduces three main safety arguments:



1. **Scheming Inability**: Arguing that the AI system lacks the capability to scheme


2. **Harm Inability**: Arguing that even if the AI attempts to scheme, it cannot cause unacceptable harm


3. **Harm Control**: Arguing that control measures would prevent harm even if the AI actively tries to subvert them

Additionally, the authors discuss supporting "Alignment" arguments, though they emphasize these should not be primary safety arguments given current limitations in alignment science.

The paper provides a comprehensive framework for evaluating these arguments through capability testing and control protocols. Figure 2 presents a clear overview of how capability evaluations are structured, breaking down the process into defining capability graphs, creating task suites, running evaluations, and aggregating results.

A particularly valuable contribution is the detailed example safety case presented in Section 8, illustrated through Figure 3, Figure 4, and Figure 

5. These figures show the evolution of a control protocol through multiple rounds of red team testing and improvements. The final protocol in Figure 5 combines untrusted monitoring with whitebox probes to achieve more robust detection of harmful actions.

The paper's structured approach is well-summarized in Table 1, which outlines the main evidence and assumptions required for each safety argument. Figure 6 provides a formal representation of the safety case using Claims-Arguments-Evidence (CAE) notation, demonstrating how different lines of evidence combine to support the overall safety claim.

Key contributions include:
- A formal framework for constructing safety cases against AI scheming
- Detailed evaluation methodologies for testing scheming capabilities
- Practical examples of control protocols and their evolution
- Analysis of assumptions underlying different safety arguments
- Extensive discussion of capability evaluation design

The authors acknowledge that many assumptions underlying these safety arguments remain unproven, highlighting the need for further research in areas like capability elicitation, probe design, and control measure validation.

Figure 5 would make an excellent thumbnail as it illustrates the sophisticated final control protocol combining multiple defensive layers - a key contribution of the paper that exemplifies the depth of thinking required for AI safety measures.

The paper's thorough treatment of both theoretical frameworks and practical implementation details makes it a valuable contribution to the field of AI safety, particularly in addressing the challenge of covert misalignment in advanced AI systems.