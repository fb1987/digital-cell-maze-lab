# Handoff: discussion of cellular computing, artificial life and mazes

**Origin:** ChatGPT thread, October 17, 2026. This document is a **curated handoff**, not an export of ChatGPT's complete verbatim assistant transcript. The user messages below are reproduced from the conversation; assistant conclusions are summarized accurately rather than copied in full.

## What the user is imagining (most important)

1. An architecture closer to **a biological organism than an organization**: encode the "DNA" of capabilities and their expression logic. Local stimulus changes concentrations/availability, causing useful computation and emergent behaviour. Learn from transcription, translation, regulatory networks, suppression, DNA accessibility, metabolism and feedback.
2. Drop the expensive cloud / LLM-agent swarm as the immediate research direction. **Instead, seek radically more compute-efficient algorithms** through reactive local rules that resemble physics, chemistry or cellular self-organization. No expensive intelligence APIs.
3. Use **maze solving** as the first benchmark. An entire maze is presented as a stimulus, and the organism responds with a pattern of lit/unlit pixels representing the solution. Prioritize **latency and accuracy versus optimized conventional algorithms**, not novelty of imagery or inflated parallel scale.
4. **One organism, one entire maze, one output.** Internally the organism may contain a 2D or eventually 3D array of update sites. The individual array element is not the organism. A *population* of tens/hundreds/thousands of organisms, each with a genome/rule set, is evolved by preferential reproduction of effective genomes with mutation and/or crossover.
5. Consider evolving the rule system rather than hand-coding a particular solution. Train over randomized mazes and generations, with fitness rewarding generalization and efficiency. Explore the possibility that a cheap reactionary substrate can develop a fast reflexive route to a valid output.
6. Expand later to very large mazes and 3D mazes. Compete with prior-art Pathfinding Neural Cellular Automata (2023) as well as strong non-AI algorithms.

## Exact user messages from the discussion

### 1. Initial biological architecture and self-evolving software thought experiment

> I want to talk about the future of ai generated interfaces and experiences. With agentic coding becoming so powerful, I imagine that rapidly adapting experiences will soon be possible. Imagine a future where you can continuously evolve without human intervention. Imagine an architecture that is more organism than organization. We write the DNA - encode it's core context and instructions. We give it it's tools, API keys, gateways, databases, integrations.
>
> Perhaps we model it's codebase after DNA as well. The concept of physical availability regulating relative compute/expression levels of mRNA and subsequently proteins is most interesting and I'm not sure if it exists in general programming concepts. But it could be accomplished through a layered compression concept or something. And perhaps we think of this pattern of simultaneous genetic availability along with suppression being akin to genetic attention. It is the molecular, cellular attention model. Modulated by methylation and other things I'm sure, with that scaffold of proteins helping keep it all together.
>
> With llms being so fast now I imagine we could recreate an agentic coded organism that is self sustaining now. We can steal as much from biology as possible. It feels like dnas 4 letter encoding read in triplets encoding the 20-something amino acids is very similar to language, that 20-something letters can encode the breadth of our experience, especially when the output can be accessorized.
>
> What if we design our codebase to be read in this massively parallel manner like a cell does. It's as if we have horizontally scaled tasks with an sqs queue for each function that is being expressed. So we could be expressing like 1000 or 10000 functions in parallel and filling their respective queues.
>
> These queues could be actioned by shared functions that convert the transcripts into the encoded agent (oh yes this is it -- the agent is the protein. It is what does everything. We need to encode agents like we do proteins.) And then we need to give them a vpc and a compute budget.
>
> There is a lot to think through here in this mapping. But the result feels like it could be novel. Though it may require some serious technical planning to accommodate the level of parallelization required to scale to 100K threads. Perhaps it's GPU powered. The DNA packing is also constantly being edited on the other side by feedback mechanisms. This allows for the instant orchestration of thousands of agents -- a powerful signal could rapidly shift the expression patterns and respond in kind. This rapid feedback loop from input to output is the basis of life, I think.
>
> I think this cell concept is really very interesting and we are able to test it. I am seeing thoughts like how it could dramatically reduce the compute needed for certain calculations -- physical interactions let nuclear forces due the work for free instead of running calculators to place things in the correct spots.
>
> Okay still thinking this through. As I'm imagining what to encode with the DNA, maybe it's the same concept as model weights for llms? I guess it would be more of a digital bacterium or some single cell entity to start. And I'm assuming gpus or whatever are optimized to run those parallel calculations already, which is necessary for the "transcription" equicalent step.
>
> Okay I'm pausing for breath there, let's discuss this concept including the work that has been done and demonstrated to date. I'm sure this isn't the first concept, though the extent to which anyone has modelled it in AWS or used it for full autonomous rsi or something I don't know. I think there is something here but want to be very realistic

### 2. Shift from agent swarm to efficient maze-solving substrate

> Very helpful and inspiring research and analysis thank you. I agree there are some interesting paths here. I appreciate the fairly clear aws analogies that is interesting and the idea of building an agentic command centre of sorts is interesting from a swarm orchestration perspective certainly.
>
> But since I want to experiment without a huge budget we will need to focus on massive efficiency gains. I suspect that API calls to powerful external intelligence is not ideal. Instead of need to leverage the elegance of biology for solving useful things faster than current algorithms can. A lofty goal! But I imagine it truly is what a cell is doing - it is the real time calculation of input output without a huge computer system. The whole 3d chemical and electromagnetic physical system is the output that is responding.
>
> I think we should attempt to tackle this instead of the scale of llm agents. I want to specifically consider pathfinding algorithms. For example solving a maze. I assume there is some very deeply researched subject area on this kind of tree traversing or whatever problem. If our cellular computer system can improve on that then we have something, otherwise we have nothing. And this goal is clear and the timing to measure I assume is quite fast and fairly reliable.
>
> I realize this is a bit of a departure but I'm interested in it now. I think the test must be some large randomized (ideally unless test sets or libraries exist to use) maze. The goal is to display the solution path line faster than the conventional algorithm.
>
> I imagine this cell expresses its interface like a 2d array representing the pixels of the maze. And they are either on or off. And the pattern of on at that moment is the solution to the puzzle. It is like a coordinated dot matrix panel. And instead of calculating it pixel by pixel it runs entirely parallel. I guess it becomes like some kind of diffusion model? Where we could start with a random genome that expresses these on or off states.
>
> Ultimately I want the program to respond reactively to the input maze such that it replies with the solution seemingly without effort. The cellular systems must provide sufficient complexity to scaffold such a potential interface reflex.
>
> Maybe it needs to be grown like a model is? We could for example have a digital pool of our default cell. Perhaps we randomly distribute some mutations throughout too. Then we use a multiplication factor to amplify signals that are more positive. Then we run a round of mutations, then another maze, highest matches gain reproduction bonuses, system is run for many generations and we see what we end up with at the end? Is that a method?
>
> The devil is certainly in the details, and the ability to react to an input maze nearly instantly with a solution would be astronomical of course. And perhaps it's also impossible, it certainly feels like it would be traditionally. Maybe it's a quantum thing already.
>
> Feels like it's testable though. I am hoping we could attempt this type of thing locally since our computer required is fairly traditional rounds of optimizations and outcomes or whatever.
>
> What do you think? Worth a try? It's very bold I recognize and very not likely to land but I feel that biology has so much wisdom and expressive programming or algorithms are such interesting topics regardless.

### 3. Most recent clarification about the organism and evolution

> I am imagining something similar sounding to that 2023 paper yes. But perhaps the methods of developing those local rules and expressing them would make larger gains. It is a benchmark at least now to also compete against. Also we could aim for very large mazes and 3d mazes as well as an extension.
>
> Note I have been thinking about this as a single cell that computes an individual response to the stimulus. And there could be dozens or hundreds or thousands of these cells in a pool, and we are growing them by evolving and amplifying the most effective of the generation while using our low cost reactionary compute method and the DNA codebase etc .
>
> Just points to consider as we continue!

### 4. Codex handoff request

> Are you able to transfer this thread and continue it in codex on my remote machine. Or perhaps zip it up and I can open it with my codex and start from there if you aren't connected

## What ChatGPT researched/discussed earlier

### Existing work

- Earle et al. (2023), *Pathfinding Neural Cellular Automata*: learned shared local update rules for mazes; arXiv https://arxiv.org/abs/2301.06820 ; repo https://github.com/smearle/pathfinding-nca . The prior conversation described approximately 97% test accuracy on small mazes in one setting; **verify task definitions and metrics from source before claiming a direct comparison**.
- 1996 cellular automaton shortest-path literature: excitation propagating and leaving a path.
- Nakagaki et al. (2000), *Physarum* slime-mould maze solving through reinforced tubes and self-organizing flow. Physical medium ≠ free CPU simulator performance.
- Growing Neural Cellular Automata (2020), local shared updates producing coherent macrostructure.
- Related projects discussed at a higher abstraction: Avida digital organisms; Google AlphaEvolve; Darwin Gödel Machine; physical reservoir computing. These do not demonstrate end-to-end improvement in our maze benchmark.

### Biological-to-algorithm mapping

The original digital-agent conception mapped DNA to versioned capability blueprints, regulation to activation, mRNA to temporary recipes, ribosomes to instantiation machinery, proteins to workers, metabolism to resource budgets, homeostasis to feedback and mutation to program selection. For the maze experiment, **those are inspirations rather than literal AWS components**. In particular, do not use message queues, isolated cloud agents or LLM tool calls simply to simulate 2D local reactions.

### Existing empirical toy results and caveats

ChatGPT built `cellular_maze_lab.py` with BFS, bit-parallel excitation and leaf pruning. Demonstrated:

- Exact wavefront paths on reachable general unweighted mazes.
- Exact leaf-pruning survivor mask on *perfect mazes* (tree graphs), but incorrect/non-unique patterns on cyclic mazes.
- On a prior illustrative CPU measurement, compiled BFS beat the naive Python big-int bit-parallel wave and pruning on ordinary 65/129 mazes by a large margin. A trivial long unbranched maze allowed extremely fast pruning but did not establish a useful general-purpose speedup.
- A Numba warm-up bug could allow first-sample compilation to contaminate timing. **This ZIP fixes the warm-up to use readonly byte-array signature**, and adds smoke tests. Treat any inherited millisecond numbers as illustrative only.
- Differences in return types (BFS path list vs pruning bitmask) and input representation are possible confounders. A fair new harness should normalize and report full end-to-end times.

### Agreed next research direction

- Begin with a modest CPU-only grid and bounded genome vocabulary, not AWS or GPUs.
- Evolve **rules** over many mazes, not per-maze solutions; measure holdout generalization.
- Compare seeded functional genomes, fully random genomes and no-selection/no-evolution controls.
- Reward legality of complete solution, then path optimality, then time/memory; avoid rewarding all-off pixel masks.
- Test cyclic and perfect mazes independently, with larger sizes and 3D later.
- A local-only scheme cannot transmit information faster than one grid step per synchronous update. Multiscale channels may be worth investigating but must be measured fairly.
- Seek a genuinely useful and computationally inexpensive emergent algorithm, but be prepared to falsify the hypothesis.

## User expectations for Codex work style

The user is comfortable with Python, AWS, coding agents and technical architecture. They favour direct, carefully reasoned explanations, quantitative baselines, cheap local prototypes, and scientifically credible claims. The immediate ask is **project continuity**, not marketing copy or cloud deployment.
