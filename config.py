API_KEY = "sk-live-4f9a8b2c1d3e5f7890abcdef1234567890"
   
   def get_user(user_input):
       db_query = "SELECT * FROM users WHERE id = " + user_input
       return db_query
