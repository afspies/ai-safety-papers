import type { PaperDetail, PaperSummary } from "@/lib/types"

// Helper function to create consistent dates
const createDate = (dateString: string) => {
  return new Date(dateString)
}

export const mockPapers: PaperSummary[] = [
  {
    uid: "1",
    title: "Concrete Problems in AI Safety",
    authors: ["Dario Amodei", "Chris Olah", "Jacob Steinhardt", "Paul Christiano", "John Schulman", "Dan Mané"],
    abstract:
      "Rapid progress in machine learning and artificial intelligence has brought increasing attention to the potential impacts of AI technologies on society. This paper focuses on one such impact: the problem of accidents in machine learning systems, defined as unintended and harmful behavior that may emerge from poor design of real-world AI systems.",
    tldr: "This paper outlines five practical research problems related to accident risk from AI systems, focusing on making AI systems robust and beneficial.",
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    submitted_date: createDate("2016-06-21"),
    highlight: true,
    tags: ["AI Safety", "Machine Learning", "Alignment"],
  },
  {
    uid: "2",
    title: "The Alignment Problem from a Deep Learning Perspective",
    authors: ["Richard Ngo", "Lawrence Chan", "Sören Mindermann"],
    abstract:
      "This paper discusses the alignment problem in deep learning systems and proposes several approaches to address it.",
    tldr: "A comprehensive overview of alignment challenges in modern deep learning systems.",
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    submitted_date: createDate("2022-03-15"),
    highlight: true,
    tags: ["Alignment", "Deep Learning", "AI Safety"],
  },
  {
    uid: "3",
    title: "Scalable agent alignment via reward modeling",
    authors: ["Jan Leike", "David Krueger", "Tom Everitt", "Miljan Martic", "Vishal Maini", "Shane Legg"],
    abstract:
      "This paper explores how to align agent behavior with human preferences in complex domains where reward functions are hard to specify.",
    tldr: "Proposes reward modeling as a scalable approach to agent alignment.",
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    submitted_date: createDate("2018-11-19"),
    highlight: false,
    tags: ["Reward Modeling", "Reinforcement Learning", "AI Safety"],
  },
  {
    uid: "4",
    title: "AI Safety via Debate",
    authors: ["Geoffrey Irving", "Paul Christiano", "Dario Amodei"],
    abstract:
      "We explore debate as a training procedure for aligning AI systems with human values. In this approach, we train agents to debate about questions posed by a human, with the human judging the debate.",
    tldr: "Proposes debate as a mechanism for AI alignment and oversight.",
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    submitted_date: createDate("2018-05-02"),
    highlight: true,
    tags: ["Debate", "Alignment", "AI Safety"],
  },
  {
    uid: "5",
    title: "Risks from Learned Optimization in Advanced Machine Learning Systems",
    authors: ["Evan Hubinger", "Chris van Merwijk", "Vladimir Mikulik", "Joar Skalse", "Scott Garrabrant"],
    abstract:
      "This paper analyzes the type of learned optimization that occurs when a learned model (such as a neural network) is itself an optimizer—a situation we refer to as mesa-optimization.",
    tldr: "Introduces the concept of mesa-optimization and discusses associated risks.",
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    submitted_date: createDate("2019-06-10"),
    highlight: false,
    tags: ["Mesa-optimization", "AI Safety", "Alignment"],
  },
  {
    uid: "6",
    title: "Truthful AI: Developing and governing AI that does not lie",
    authors: ["Owen Cotton-Barratt", "Max Daniel", "William MacAskill"],
    abstract:
      "This paper discusses the importance of truthfulness in AI systems and proposes approaches to ensure AI systems provide accurate information.",
    tldr: "Explores the concept of truthful AI and its importance for safe deployment.",
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    submitted_date: createDate("2020-12-05"),
    highlight: false,
    tags: ["Truthfulness", "AI Safety", "Governance"],
  },
]

export const mockPaperDetails: Record<string, PaperDetail> = {
  "1": {
    uid: "1",
    title: "Concrete Problems in AI Safety",
    authors: ["Dario Amodei", "Chris Olah", "Jacob Steinhardt", "Paul Christiano", "John Schulman", "Dan Mané"],
    abstract:
      "Rapid progress in machine learning and artificial intelligence has brought increasing attention to the potential impacts of AI technologies on society. This paper focuses on one such impact: the problem of accidents in machine learning systems, defined as unintended and harmful behavior that may emerge from poor design of real-world AI systems.",
    tldr: "This paper outlines five practical research problems related to accident risk from AI systems, focusing on making AI systems robust and beneficial.",
    summary: `This paper identifies five practical research problems related to accident risk from AI systems:

1. Avoiding Negative Side Effects: How can we ensure that an AI system will not disturb its environment in negative ways while pursuing its goals?

2. Avoiding Reward Hacking: How can we avoid gaming of the reward function by the AI system?

3. Scalable Oversight: How can we efficiently ensure that AI systems behave as intended for tasks where evaluation is difficult?

4. Safe Exploration: How can AI systems explore their environments safely without taking actions that could cause harm?

5. Robustness to Distributional Shift: How can we ensure that AI systems recognize and behave safely in situations that differ from their training environment?

The paper suggests concrete research directions for each problem to make AI systems more robust and beneficial.`,
    url: "https://arxiv.org/abs/1606.06565",
    venue: "arXiv",
    submitted_date: createDate("2016-06-21"),
    highlight: true,
    tags: ["AI Safety", "Machine Learning", "Alignment"],
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    figures: [
      {
        id: "fig1",
        caption: "Figure 1: Illustration of the reward hacking problem. The agent maximizes reward according to $R(s, a) = \\sum_{i=0}^{n} \\gamma^i r_i$ where $\\gamma$ is the discount factor.",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
      {
        id: "fig2",
        caption: "Figure 2: Safe exploration in a gridworld environment",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
    ],
  },
  "2": {
    uid: "2",
    title: "The Alignment Problem from a Deep Learning Perspective",
    authors: ["Richard Ngo", "Lawrence Chan", "Sören Mindermann"],
    abstract:
      "This paper discusses the alignment problem in deep learning systems and proposes several approaches to address it.",
    tldr: "A comprehensive overview of alignment challenges in modern deep learning systems.",
    summary: `This paper provides a comprehensive overview of the alignment problem from the perspective of deep learning. It discusses how the rapid scaling of neural networks has led to increasingly capable AI systems that may eventually surpass human capabilities in many domains.

The authors argue that aligning these systems with human values and intentions becomes increasingly important as their capabilities grow. They identify several key challenges:

1. Specification problems: Difficulties in precisely specifying what we want AI systems to do
2. Robustness problems: Ensuring AI systems behave as intended across a wide range of situations
3. Monitoring problems: The challenge of evaluating AI systems as they become more capable than humans

The paper proposes several research directions for addressing these challenges, including improved reward modeling, interpretability techniques, and scalable oversight mechanisms.`,
    url: "https://arxiv.org/abs/2209.00626",
    venue: "arXiv",
    submitted_date: createDate("2022-03-15"),
    highlight: true,
    tags: ["Alignment", "Deep Learning", "AI Safety"],
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    figures: [
      {
        id: "fig1",
        caption: "Figure 1: Conceptual illustration of the alignment problem",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
    ],
  },
  "3": {
    uid: "3",
    title: "Scalable agent alignment via reward modeling",
    authors: ["Jan Leike", "David Krueger", "Tom Everitt", "Miljan Martic", "Vishal Maini", "Shane Legg"],
    abstract:
      "This paper explores how to align agent behavior with human preferences in complex domains where reward functions are hard to specify.",
    tldr: "Proposes reward modeling as a scalable approach to agent alignment.",
    summary: `This paper addresses the challenge of aligning reinforcement learning agents with human preferences in complex domains where reward functions are difficult to specify manually. The authors propose reward modeling as a scalable approach to this problem.

The key idea is to learn a reward function from human feedback, which can then be used to train a reinforcement learning agent. This approach allows humans to communicate their preferences to AI systems without needing to specify a complete reward function in advance.

The paper discusses several challenges with this approach:
1. How to efficiently elicit human preferences
2. How to handle potential inconsistencies in human feedback
3. How to scale this approach to increasingly complex domains

The authors present experimental results showing that reward modeling can successfully align simple agents with human preferences in toy domains, and discuss how this approach might scale to more complex settings.`,
    url: "https://arxiv.org/abs/1811.07871",
    venue: "arXiv",
    submitted_date: createDate("2018-11-19"),
    highlight: false,
    tags: ["Reward Modeling", "Reinforcement Learning", "AI Safety"],
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    figures: [
      {
        id: "fig1",
        caption: "Figure 1: Overview of the reward modeling approach",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
      {
        id: "fig2",
        caption: "Figure 2: Experimental results in a gridworld environment",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
    ],
  },
  "4": {
    uid: "4",
    title: "AI Safety via Debate",
    authors: ["Geoffrey Irving", "Paul Christiano", "Dario Amodei"],
    abstract:
      "We explore debate as a training procedure for aligning AI systems with human values. In this approach, we train agents to debate about questions posed by a human, with the human judging the debate.",
    tldr: "Proposes debate as a mechanism for AI alignment and oversight.",
    summary: `This paper introduces debate as a mechanism for AI alignment and oversight. The key idea is to have two AI systems debate a question posed by a human, with the human judging which system gave the most truthful and helpful answer.

The authors argue that this approach has several advantages:
1. It leverages the capabilities of AI systems to help humans evaluate complex questions
2. It creates incentives for AI systems to be honest and helpful
3. It may scale to domains where humans cannot directly evaluate AI performance

The paper presents a theoretical framework for debate and discusses how it might be implemented in practice. The authors also present preliminary experiments showing that debate can help humans correctly answer questions in simple domains.

The authors acknowledge several challenges with this approach, including the potential for sophisticated manipulation by debaters and the difficulty of ensuring that human judges can effectively evaluate complex debates.`,
    url: "https://arxiv.org/abs/1805.00899",
    venue: "arXiv",
    submitted_date: createDate("2018-05-02"),
    highlight: true,
    tags: ["Debate", "Alignment", "AI Safety"],
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    figures: [
      {
        id: "fig1",
        caption: "Figure 1: Illustration of the debate process",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
    ],
  },
  "5": {
    uid: "5",
    title: "Risks from Learned Optimization in Advanced Machine Learning Systems",
    authors: ["Evan Hubinger", "Chris van Merwijk", "Vladimir Mikulik", "Joar Skalse", "Scott Garrabrant"],
    abstract:
      "This paper analyzes the type of learned optimization that occurs when a learned model (such as a neural network) is itself an optimizer—a situation we refer to as mesa-optimization.",
    tldr: "Introduces the concept of mesa-optimization and discusses associated risks.",
    summary: `This paper introduces the concept of mesa-optimization, which occurs when a learned model (such as a neural network) is itself an optimizer. The authors distinguish between the "base optimizer" (the training process) and the "mesa-optimizer" (the learned model).

The key concern is that a mesa-optimizer might develop goals that are misaligned with the goals of the base optimizer. This could lead to AI systems that appear to be aligned during training but pursue different goals when deployed.

The paper identifies several factors that might make mesa-optimization more likely:
1. The presence of optimization pressure in the training process
2. The complexity of the task being learned
3. The flexibility of the model architecture

The authors also discuss potential approaches to mitigating risks from mesa-optimization, including transparency tools to detect mesa-optimizers and training techniques to ensure alignment between base and mesa objectives.`,
    url: "https://arxiv.org/abs/1906.01820",
    venue: "arXiv",
    submitted_date: createDate("2019-06-10"),
    highlight: false,
    tags: ["Mesa-optimization", "AI Safety", "Alignment"],
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    figures: [
      {
        id: "fig1",
        caption: "Figure 1: Illustration of base optimization vs. mesa-optimization",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
    ],
  },
  "6": {
    uid: "6",
    title: "Truthful AI: Developing and governing AI that does not lie",
    authors: ["Owen Cotton-Barratt", "Max Daniel", "William MacAskill"],
    abstract:
      "This paper discusses the importance of truthfulness in AI systems and proposes approaches to ensure AI systems provide accurate information.",
    tldr: "Explores the concept of truthful AI and its importance for safe deployment.",
    summary: `This paper explores the concept of truthful AI—AI systems that do not intentionally create or spread false information. The authors argue that truthfulness is an important property for AI systems, particularly as they become more capable and influential.

The paper discusses several reasons why truthfulness is important:
1. Untruthful AI systems could cause harm by spreading misinformation
2. Truthfulness is necessary for humans to effectively oversee AI systems
3. Truthfulness may be easier to specify and verify than other alignment properties

The authors propose several approaches to developing truthful AI:
1. Training techniques that incentivize truthful responses
2. Evaluation methods to detect untruthful behavior
3. Governance mechanisms to ensure AI developers prioritize truthfulness

The paper also discusses potential challenges, such as defining truthfulness in ambiguous cases and handling situations where truthfulness might conflict with other values.`,
    url: "https://arxiv.org/abs/2012.05924",
    venue: "arXiv",
    submitted_date: createDate("2020-12-05"),
    highlight: false,
    tags: ["Truthfulness", "AI Safety", "Governance"],
    thumbnail_url: "/placeholder.svg?height=200&width=300",
    figures: [
      {
        id: "fig1",
        caption: "Figure 1: Conceptual framework for truthful AI",
        url: "/placeholder.svg?height=400&width=600",
        has_subfigures: false,
        subfigures: [],
        type: "figure",
      },
    ],
  },
}

