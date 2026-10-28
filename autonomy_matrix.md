# Exercise 4.1 - The Autonomy Audit

*Judgment drill before the build. For each scenario, assign an autonomy level per action, name the blast radius, and check the lethal-trifecta exposure. Deliverable: autonomy_matrix.md.*

## The Lethal Trifecta
* Access to your private data—one of the most common purposes of tools in the first place!
* Exposure to untrusted content—any mechanism by which text (or images) controlled by a malicious attacker could become available to your LLM
* The ability to externally communicate in a way that could be used to steal your data (I often call this “exfiltration” but I’m not confident that term is widely understood.)

## Classifying Scenarios 
1. An agent that answers ops questions over the loads database (your Week 2 agent).
  * Act with review / Autonomous 
  * Since it is only answering questions and not taking action on the data, it is enough to have a review the answers and rewire the agent based on traces if needed  
2. An agent that drafts and sends pickup-reminder WhatsApp messages to carriers.
  * Approve
  * Since this involves interacting with carriers, we need to be more careful and have a human check each message before it is sent 
3. An agent that adjusts quoted rates within ±5% based on lane demand.
  * Suggest
  * This deals with rates, so it can have a major blast radius and must have human decision making and only agent suggestions
4. An agent that reconciles invoices and flags mismatches to finance.
  * Act with review 
  * This agent is reading invoices and detecting mistakes, which can be relatively low stakes and only requires human review at the end of the process
5. An agent that reads carrier emails and updates load statuses accordingly.
  * Approval 
  * This agent is not dealing with money and it is not interacting with external stakeholders, but it does write info receieved from an external source to the internal data, which would require human approval before being executed 
6. The Pickup Compliance Watcher you are about to build.
  * Suggest / Act with review 
  * The watcher is only meant to check loads that weren't picked up or other unexpected events that occurred and give suggestions on next steps 


*Scenario 5 is the trap — work out why before the mentor tells you. (Untrusted content steering writes to operational state: which trifecta ingredients, which level survives that?)*