import multion
def use_multion(prompt):
    multion.login()
    prompt = f"'{prompt}'Book a table with the details from above statement. Choose San Francisco Location"
    multion.new_session({"input":prompt,"url":"https://www.opentable.com/all-metros"})