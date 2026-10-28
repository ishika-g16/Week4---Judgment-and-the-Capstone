import os, sys 
import json 
import re # RegEx

def truncate(text, max_length=150):
   if len(text) > max_length:
      return text[:max_length] + "... (truncated)"
   return text

def clean_num(text):
   return text.replace(',', '').replace('.', '')

def audit(answer, tool_store):
   print(f"\n----------------------------")
   print(f">> AUDIT")
   new = re.compile(r'\d[\d,\.]*')
   raw_nums = new.findall(answer)
   
   for num in raw_nums:
      cleaned_num = clean_num(num)
      found = False
      for tool_name, iter_num, result in tool_store:
         if cleaned_num in clean_num(result):
            print(f"\n**GROUNDED**\nNumber {num} found in tool result of '{tool_name}' at iteration {iter_num}.")
            found = True
            break
      if not found:
         print(f"\n**UNGROUNDED**\nNumber {num} NOT found in any tool results.")
   return

def view(run_id, traces_dir=None):
   if traces_dir is None:
      traces_dir = os.path.join(os.path.dirname(__file__), "traces")
   file = os.path.join(traces_dir, f"{run_id}.jsonl")
   if not os.path.isfile(file):
      print(f"[VIEWER] No trace found: {file}")
      return

   # PART 1: RECONSTRUCTING THE TIMELINE 
   current_iter = 0
   tool_store = []

   try:
      with open(file, "r") as f:
         for line in f:
            record = json.loads(line)
            event_type = record["event_type"]
            iter_num = record.get("iter", current_iter)

            if event_type == "run_start":
               print(f"\n============================")
               print(f">> RUN START")
               print(f"RUN_ID: {run_id}")
               print(f"QUESTION: {record['question']}")
               print(f"============================\n")
               continue 
            
            if iter_num != current_iter:
               print(f"\n--------ITERATION {iter_num}--------\n")
               current_iter = iter_num

            if event_type == "model_call":
               input_tokens = record["in_tokens"]
               output_tokens = record["out_tokens"]
               stop = record["stop_reason"]
               print(f">> MODEL CALL:\nInput Tokens = {input_tokens}, Output Tokens = {output_tokens}, Stop Reason = {stop}\n")
            
            if event_type == "tool_call":
               tool_name = record["tool_name"]
               tool_inputs = record["inputs"]
               id = record["tool_block_id"]
               print(f">> TOOL CALL:\nTool Name = {tool_name}\nTool Inputs = {tool_inputs}\n")

            if event_type == "tool_result":
               id = record["tool_block_id"]
               tool_name = record["tool_name"]
               tool_inputs = record["inputs"]
               result = truncate(record["result"])
               print(f">> TOOL RESULT:\nTool Name = {tool_name}\nResult = {result}\n")
               tool_store.append((tool_name, iter_num, record["result"]))

            if event_type == "final_answer":
               answer = record["answer"]
               print(f">> FINAL ANSWER: \n{answer}")

            if event_type == "end_run":
               print(f"\n============================")
               print(f">> RUN END: run_id = {run_id}")
               print(f">> TOTALS: Iterations = {record['iter']} | Total Tokens = {record['total_tokens']}")
               print(f"============================\n")
               break

      # PART 2: AUDIT
      audit(answer, tool_store)  

   except Exception as e:
      print(f"[VIEWER WARNING] Failed to view trace for id {run_id}: {e}")
   return

if __name__ == "__main__":
   if len(sys.argv) < 2:
      print("Usage: uv run trace_view.py <run_id> [traces_dir]")
      print("Example: uv run trace_view.py 74526bdb ../Ex3_2/traces")
      raise SystemExit(1)
   run_id = sys.argv[1]
   traces_dir = sys.argv[2] if len(sys.argv) > 2 else None
   view(run_id, traces_dir)
