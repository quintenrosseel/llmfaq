# Requirements V1; by 23 November

- Chatbot should clearly indicate when the user's question is not in the database. 
    - So then clearly show "the answer cannot be found". 
    - Thereafter, this "bad" chat is written back to Neo4j to give a notification that there was a question that could not be answered by the people in the practice/hospital
- A button by which the patient can reply directly with "I don't understand the answer" or clearly indicate that the answer is clear.
    - Again, feedback loop to database
- Interface for hospital to visualize not clear / I don't know / good answers
    - Done in Neodash! 
- interface for hospital to supplement non-obvious/I don't know answers (and also succeed I db)