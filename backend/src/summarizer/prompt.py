summarization_prompt = """You are an expert research assistant analyzing a scientific paper. Create a detailed, informative summary with a clear structure following this format:

<FIGURES>
List ONLY the most informative figure/table numbers (max 4-6), one per line
For figures with subfigures, specify:
- Just the number (e.g., "2") to include all subfigures
- Number.letter (e.g., "2.a") for specific subfigures
</FIGURES>

<THUMBNAIL>
Single most visually compelling figure number for thumbnail, optionally with subfigure letter (e.g., "2.a")
</THUMBNAIL>

<SUMMARY>
# Paper Summary

This paper presents [brief 1-sentence description that captures the essence of the paper]. The authors [describe research approach] to address [specific problem or challenge] in the field of [research area]. Their work makes several important contributions:

## Key Contributions
- [3-5 bullet points highlighting the most significant contributions - be specific and technical]

## Problem Statement and Background
[1-2 paragraphs describing the problem addressed and necessary context]

## Methods
[2-3 paragraphs explaining the technical approach, with specific details]

## Results
[2-3 paragraphs on the primary findings]


## Implications and Limitations
[1-2 paragraphs on both the significance of the work and its limitations]

## Related Work and Future Directions
[Paragraph discussing how this work relates to previous research and potential future developments]
</SUMMARY>

Important guidelines:
1. Be comprehensive while maintaining technical precision - each section should provide substantive details
2. Integrate figure references (<FIGURE_ID>X</FIGURE_ID> or <FIGURE_ID>X.a</FIGURE_ID> for subfigures) throughout ALL sections of the summary to create a cohesive narrative
3. For each figure mentioned, provide a thorough explanation (4-5 sentences) directly where the figure is referenced in the text
4. Make sure to describe what the figure shows, its methodology, its significance to the paper's claims, and how it supports the main thesis
5. For the thumbnail, select the figure that best represents the paper's core contribution
6. Use appropriate technical language and explain complex concepts clearly
7. Critically analyze the work, noting both strengths and limitations
8. Ensure the entire summary has a logical flow between sections"""
