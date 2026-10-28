# Anthropic — How We Built Our Multi-Agent Research System
**The case for multi-agent: orchestrator-worker, parallel subagents for breadth-first research — and the honest cost accounting (multi-agent burns roughly 15× the tokens of a single chat)**

* In this reading, Anthropic talks about how they have used multi-agent systems to enhance research capabilities for users. 
* A lead agent is in charge of delegating tasks to subagents that operate in parallel to support efficient research methods where the landscape of a topic is widely explored and then relevant areas get a deep dive to retrieve specific information asked by the user
* Tries to mimic the methodology of expert human researchers 

# Cognition — Don't Build Multi-Agents (Walden Yan)
**The case against: context fragmentation, subagents making conflicting implicit decisions, and why a single-threaded agent with full context usually wins.**

* In this reading, the authors argue against using multi-agentic systems, as they may lead to undesired outputs, even if every agent has the entire history and context 
* They propose using single threaded agents, where the idea of subagents is essentially executed sequentially instead of happening in parallel like in multiagent systems 

# Where do I stand?

* I think that single-threaded systems are definitely more reliable, as they cannot branch out exponentially and result in endless tokens and confused outputs
* While there exists a certain level of uncertainty in both systems, the flow of single-threaded agents allows us to maintain some control over the process 
* I think that until we find a more restricted method of building multiagent systems, we can stick to single-threaded agents for most tasks. 
* Finally, if a task is more experimental in nature, and branching out from the prompt would be beneficial in that scenario, then I would switch to multiagentic systems


