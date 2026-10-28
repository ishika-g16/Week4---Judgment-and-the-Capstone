

# ------------ token-use and cost add ons ------------

def estimate_tokens(text:str) -> int:
   # estimating that 1 token is approx 4 characters 
   return max(1, len(text) // 4)

class TokenLedger:
   def __init__(self):
      self.rows = [] # 1 row = 1 iteration
      self.headers = ["Iteration", "Input", "Output", "In: System", "Schemas", "History", "New"]
      self.msg_store = [] # storing all messages to get the rent 
   
   # this is called every iteration to keep a track of the token count with each call
   def record(self, iteration, usage, old_messages, new_messages, system, tools, messages):
      input = usage.input_tokens # ground truth 
      output = usage.output_tokens # ground truth 
      in_system = estimate_tokens(str(system)) # system prompt 
      schemas = sum(estimate_tokens(str(t)) for t in tools) # tool schema 
      history = sum(estimate_tokens(str(msg)) for msg in old_messages) # all earlier messages 
      new = sum(estimate_tokens(str(msg)) for msg in new_messages) # newer messages being sent to the LLM for the first time

      self.rows.append([iteration+1, input, output, in_system, schemas, history, new])
         
      # only appending the newer messages that were added to the list 
      startidx = len(self.msg_store) 
      add_msgs = messages[startidx:]
      for msg in add_msgs:
         self.msg_store.append({"msg":str(msg), "iter": iteration+1}) # messages stored in text, iteration pairs 
      # print("\nMSG STORE: ", self.msg_store)

   # calculates the rent of a single message
   def rent_of(self, message_index:int, max_iter) -> int:
      msg = self.msg_store[message_index]["msg"] 
      iteration_added = self.msg_store[message_index]["iter"]
      tokens = estimate_tokens(msg)
      rent = tokens * (max_iter-iteration_added)
      return rent

   def print_ledger(self, max_iter, question):
      print(f"\n------- TOKEN LEDGER -------")
      # printing per-iteration table
      for col in self.headers:
         print(col.ljust(15), end="")
      print()
      for row in self.rows:
         for col in row:
            print(str(col).ljust(15), end="")
         print()

      # calculating cumulative totals 
      total_input = sum(row[1] for row in self.rows)
      total_output = sum(row[2] for row in self.rows)
      print(f"Total Input Tokens: {total_input}")
      print(f"Total Output Tokens: {total_output}\n")


      '''
      print("------- TOP 3 RENT PAYERS -------\n")
      #calculating the top 3 rent payers 
      total_rent = []
      for i, msg in enumerate(self.msg_store):
         total_rent.append({"msg": msg, "rent":self.rent_of(i, max_iter)})
      top3 = sorted(total_rent, key= lambda x: x["rent"], reverse=True)[:3]
      
      for item in top3:
         msg = item["msg"]
         rent = item["rent"]
         print(f"Message: {msg} with rent = {rent}\n")
       '''

      return total_input + total_output